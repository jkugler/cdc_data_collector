#!/usr/bin/env python

import os
import sys
import unittest

# Set up the test environment
opd = os.path.dirname
sys.path.insert(0, opd(os.path.abspath(__file__)))

from cchrc import tests as cchrc_tests

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromModule(cchrc_tests)
    unittest.TextTestRunner(verbosity=2).run(suite)
