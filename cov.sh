#!/bin/sh

coverage run "--omit=/usr/share/python-support/python-configobj/configobj.py,*run_tests*,*cchrc/tests*,*config*" ./run_tests.py
coverage report -m
