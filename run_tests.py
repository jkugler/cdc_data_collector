#!/usr/bin/env python

import os
import sys
import unittest

# Set up the test environment
opd = os.path.dirname
sys.path.insert(0, opd(os.path.abspath(__file__)))

from cchrc import unit_tests
from cchrc import integration_tests

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--integration':
        to_run = integration_tests
    else:
        to_run = unit_tests

    suite = unittest.TestLoader().loadTestsFromModule(to_run)
    unittest.TextTestRunner(verbosity=2).run(suite)
