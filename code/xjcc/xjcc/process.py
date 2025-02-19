# -*- coding: utf-8 -*-
import multiprocessing
import pickle
import logging
import resource
import signal
import subprocess
import os
import zlib


def work(target, ctx, send_conn, max_cpu_secs, max_vmem_size):
    logger = ctx.log_to_stderr()
    logger.setLevel(logging.DEBUG)

    if max_cpu_secs:
        resource.setrlimit(resource.RLIMIT_CPU, (max_cpu_secs,)*2)
        logger.info('RLIMIT_CPU = %d seconds', max_cpu_secs)

    if max_vmem_size:
        resource.setrlimit(resource.RLIMIT_AS, (max_vmem_size,)*2)
        logger.info('RLIMIT_RSS set to %d bytes', max_vmem_size)

    rusage = resource.getrusage(resource.RUSAGE_SELF)
    logger.info('Memory info: %r', rusage)
    logger.info('Page size: %d', resource.getpagesize())
    logger.info('Maximum Resident Set Size: %d * %d = %d',
                rusage.ru_maxrss, resource.getpagesize(),
                rusage.ru_maxrss*resource.getpagesize())

    try:
        result = target()
    except subprocess.CalledProcessError as e:
        result = None
        logger.info('Child process cmd: %r', e.cmd)
        if hasattr(e, 'stderr'):
            logger.info('Child process stderr: %r', e.stderr)
        logger.info('Child process stdout: %r', e.output)
        if e.returncode < 0:
            logger.info('Child process died, committing suicide using ' +
                        'signal %s (%d).',
                        signal.Signals(-e.returncode).name, -e.returncode)
            os.kill(os.getpid(), -e.returncode)
            signal.pause()
        else:
            logger.info('Child process failed with status %s', e.returncode)
            os._exit(e.returncode)
    except (OSError, MemoryError):
            sgn = signal.SIGSEGV
            logger.info('Child process ran out of memory, committing suicide' +
                        ' using signal %s (%d).',
                        sgn.name, sgn)
            os.kill(os.getpid(), sgn)
            signal.pause()

    zresult = zlib.compress(pickle.dumps(result))
    send_conn.send_bytes(zresult)
    logger.info('Maximum Resident Set Size: %r',
                rusage.ru_maxrss*resource.getpagesize())


def execute(target, ctx=None, timeout=30):
    logger = logging.getLogger(__name__)

    max_cpu_secs = 10
    max_vmem_size = 750*1024**2  # 300 MiB should suffice

    if not ctx:
        logger.debug('No multiprocessing context given, using default one...')
        ctx = multiprocessing.get_context()

    recv_conn, send_conn = ctx.Pipe(duplex=False)
    process = ctx.Process(target=work, args=(target, ctx, send_conn, max_cpu_secs, max_vmem_size))
    process.daemon = True
    process.start()

    logger.info('PID of spawned process: %d', process.pid)
    process.join(timeout)
    if process.is_alive():
        if timeout:
            logger.info('Process is taking longer than %d seconds, ' +
                        'sending SIGTERM...', timeout)
        process.terminate()
        process.join()
    logger.info('Process terminated.')

    try:
        send_conn.close()
    except Exception:
        pass
    logger.info('Send conn closed.')
    try:
        if not recv_conn.poll():
            raise ValueError('No result found')
        zretval = recv_conn.recv_bytes()
    except Exception:
        logger.info('No output data received.', exc_info=True)
        retval = None
    else:
        try:
            pretval = zlib.decompress(zretval)
            logger.debug('Received value: %d bytes (%d bytes compressed)',
                         len(pretval), len(zretval))
            retval = pickle.loads(pretval)
        except zlib.error:
            logger.info('Decompression error', exc_info=True)
            retval = None
        except Exception:
            logger.info('Unpickling error', exc_info=True)
            retval = None

    exitcode = process.exitcode
    logger.info('Exitcode was %r', exitcode)
    return (exitcode, retval)
