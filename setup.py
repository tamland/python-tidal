#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

long_description = ""
with open('README.rst') as f:
    long_description += f.read()

with open('HISTORY.rst') as f:
    long_description += '\n\n'
    long_description += f.read() .replace('.. :changelog:', '')

setup(
    name='tidalapi',
    version='0.5.0',
    description='Unofficial API for TIDAL music streaming service.',
    long_description=long_description,
    author='Thomas Amland',
    author_email='thomas.amland@googlemail.com',
    url='https://github.com/tamland/tidalapi',
    license='LGPL',
    packages=['tidalapi'],
    install_requires=['requests'],
    keywords='',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
)