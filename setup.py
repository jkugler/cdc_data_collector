#!/usr/bin/env python

from setuptools import setup, find_packages
setup(
    name = "CDCDataCollector",
    version = "0.1",
    packages = find_packages(),
    exclude_package_data = {'':['README.rst', 'doc/*']},
    scripts = ['cdc.py'],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = ['configobj', 'daemon', 'futures'],
    tests_require = ['unittest'],

    # metadata for upload to PyPI
    author = "Joshua Kugler",
    author_email = "joshua at azariah dot com",
    description = "This is the CDC Data Collector",
    license = "BSD",
    keywords = "data collection",
    url = "http://azariah.com/",   # project home page, if any

    # could also include long_description, download_url, classifiers, etc.
)
