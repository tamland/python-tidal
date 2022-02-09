#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
import sys

required = ['requests']
if sys.version_info < (3,4):
    required.append('enum34')

if sys.version_info < (3,0):
    required.append('futures')

long_description = ""
with open('README.rst') as f:
    long_description += f.read()

with open('HISTORY.rst') as f:
    long_description += '\n\n'
    long_description += f.read() .replace('.. :changelog:', '')

setup(
    name='tidalapi',
    version='0.6.10',
    description='Unofficial API for TIDAL music streaming service.',
    long_description=long_description,
    author='Thomas Amland',
    author_email='thomas.amland@googlemail.com',
    maintainer='morguldir',
    maintainer_email='morguldir@protonmail.com',
    url='https://github.com/tamland/python-tidal',
    license='LGPL',
    packages=['tidalapi'],
    install_requires=required,
    keywords='',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
