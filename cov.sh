#!/bin/sh

python-coverage run "--omit=/usr/share/*,/usr/local/*,*run_tests*,*cchrc/tests*,*config*" ./run_tests.py --quiet --both
python-coverage report -m
