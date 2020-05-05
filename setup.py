#!/usr/bin/env python
import io
import re
from os.path import dirname
from os.path import join

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    with io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ) as fh:
        return fh.read()


setup(
    name='pw.tcamp.magic-home',
    version='0.1',
    description='An python connector to MagicHome controllers.',
    long_description='',
    author='Thiago Campmany',
    url='https://github.com/TCampmany/pw.tcamp.magic-home',
    packages=find_packages(f'src'),
    package_dir={'': 'src'},
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Topic :: Utilities',
    ],
    python_requires='>=3.0',
    # install_requires=['termcolor==1.1.0'],
)
