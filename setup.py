#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
from wimpy import __version__


readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

requirements = [
    'requests >=2.2.1'
]

setup(
    name='wimpy',
    version=__version__,
    description='Unofficial WiMP Python API',
    long_description=readme + '\n\n' + history,
    author='Thomas Amland',
    author_email='thomas.amland@googlemail.com',
    url='https://github.com/tamland/wimpy',
    license='LGPL',
    zip_safe=False,
    include_package_data=True,
    packages=['wimpy'],
    package_dir={'wimpy': 'wimpy'},
    install_requires=requirements,
    keywords='',
    classifiers=[
        'Development Status :: 3 - Alpha',
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