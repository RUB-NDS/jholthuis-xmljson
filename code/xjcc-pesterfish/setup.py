#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import setuptools

setuptools.setup(
    name='xjcc_pesterfish',
    version='0.1.0',
    description='Pesterfish converter for xjcc',
    author='Jan Holthuis',
    author_email='jan.holthuis@ruhr-uni-bochum.de',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='xml json jxon conversion translation algorithm lossless security',
    packages=setuptools.find_packages(exclude=['contrib', 'docs', 'tests']),
    entry_points={
        'xjcc.converters': [
            'pesterfish = xjcc_pesterfish:PesterfishPlugin',
            'pesterfishdefused = xjcc_pesterfish:PesterfishDefusedPlugin',
        ],
    },
    install_requires=[
        'simplejson>=3.10.0',
    ]
)
