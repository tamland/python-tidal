#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand
from wimpy import __version__

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['--cov=wimpy', 'tests']
        self.test_suite = True
    def run_tests(self):
        import pytest
        sys.exit(pytest.main(self.test_args))


readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

requirements = [
    'requests >=2.2.1'
]

test_requirements = [
    'pytest', 'pytest-cov',
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
    test_suite='tests',
    tests_require=test_requirements,
    install_requires=requirements,
    cmdclass={'test': PyTest},
    keywords='',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License (LGPL)',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
)