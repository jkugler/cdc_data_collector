import csv
import os
import shutil
import tempfile
import time
import unittest2 as unittest

import cchrc
from cchrc.common.exceptions import *

from common import get_file, MyTestSensor

file_dir = os.path.join(os.path.dirname(__file__), 'files')

class TestIntegration(unittest.TestCase):
    def __init__(self, *a, **kw):
        self.DF = cchrc.common.datafile.DataFile
        unittest.TestCase.__init__(self, *a, **kw)

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sc = cchrc.common.SensorContainer()
        self.dfr = cchrc.common.datafile.DataFileRunner()
        self.sc.put(MyTestSensor('T1'), 'TestGroup')
        self.sc.put(MyTestSensor('T2', increment_value=2), 'TestGroup')
        self.sc.put(MyTestSensor('T3', increment_value=3), 'TestGroup')
        self.sc.put(MyTestSensor('T4', increment_value=4), 'TestGroup')
        self.sc.put(MyTestSensor('T5', increment_value=5), 'TestGroup')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        pass

    def test_recording_sampling_sensors(self):
        """Test Recording Using Sampling Only"""
        df = self.DF('TestID', 'TestFile', self.temp_dir, 'TestGroup',
                    5, 'SAMPLE', ["T1","T2","T5"], self.sc)
        self.dfr.put(df)
        self.sc.start_averaging_sensors()
        self.dfr.start_data_files()
        time.sleep(15)
        self.sc.stop_averaging_sensors()
        self.dfr.stop_data_files()
        self.assertRegexpMatches(get_file(self.temp_dir, 'TestFile'),
                                 ('Timestamp,T1,T2,T5\r\n'
                                  '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},1,2,5\r\n'
                                  '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},2,4,10\r\n'
                                  '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},3,6,15\r\n')
                                 )

    def test_recording_averaging_sensors(self):
        """Test Recording Using Averaging Sensors As Well"""
        # We cannot just start self.dfr up here, because the sampling results
        # will depend on how close to time.time()%12 == 0 the DFR was started.
        df = self.DF('TestID', 'TestFile', self.temp_dir, 'TestGroup',
                     12, 'AVERAGE', ["T1","T2","T5"], self.sc)
        self.sc.start_averaging_sensors()
        for _ in [1,2,3]:
            time.sleep(12)
            df.collect_data()
        self.sc.stop_averaging_sensors()
        self.assertRegexpMatches(get_file(self.temp_dir, 'TestFile'),
                                 ('Timestamp,T1_avg,T2_avg,T5_avg\r\n'
                                  '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},6.5,13.0,32.5\r\n'
                                  '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},18.5,37.0,92.5\r\n'
                                  '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},30.5,61.0,152.5\r\n')
                                 )
