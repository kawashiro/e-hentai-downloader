#!/usr/bin/env python3
# -*- coding: UTF-8

""" ehd setup script """

import sys
import os
from distutils.core import setup, Extension

# Some dirty hack to define version in one place
sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)) + '/src')
from EHentaiDownloader import __version__

setup(
    # Metadata
    name='EHentaiDownloader',
    version=__version__,
    description='Hentai downloader',
    long_description='Download your favourite comic from e-hentai.org',
    url='http://under-construction.example.com',
    maintainer='Kawashiro Nitori',
    maintainer_email='spam@example.com',
    license='WTFPL-2',
    platforms=['POSIX'],
    # Python packages
    package_dir={'': 'src/'},
    packages=['EHentaiDownloader'],
    # Executable files
    scripts=['src/ehd'],
)
