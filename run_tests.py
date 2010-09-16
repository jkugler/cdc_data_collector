#!/usr/bin/env python

import os
import sys
import unittest2 as unittest

# Set up the test environment
opd = os.path.dirname
sys.path.insert(0, opd(os.path.abspath(__file__)))

from cchrc.tests import (unit, integration)

test_mods = [unit]

if __name__ == '__main__':
    if '--both' in sys.argv:
        test_mods.append(integration)
    elif '--integration' in sys.argv:
        test_mods = [integration]

    if '--quiet' in sys.argv:
        verbosity = 0
    else:
        verbosity = 2

    for tests in test_mods:
        suite = unittest.TestLoader().loadTestsFromModule(tests)
        unittest.TextTestRunner(verbosity=verbosity).run(suite)
