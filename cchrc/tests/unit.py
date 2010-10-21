import csv
import os
import shutil
import tempfile
import time
import unittest2 as unittest

import cchrc
from cchrc.common.exceptions import *

from common import get_file, MyTestSensor

class TestSensorBase(unittest.TestCase):
    """Tests the base sensor and its functions"""

    def test_list_sensor_types(self):
        """Ensure sensors.list_all() is returning what it should"""
        self.assertEqual(cchrc.sensors.list_all(), ['onewire'])

    def test_base_attributes(self):
        """Ensure SensorBase has all needed attributes"""
        self.assertTrue(hasattr(cchrc.sensors.SensorBase, '__init__') and
                        hasattr(cchrc.sensors.SensorBase, 'get_reading'))

    def test_friendly_name_when_not_set(self):
        """Ensure getting friendly name when not set returns name"""
        s = MyTestSensor('NAME', 'id')
        self.assertEqual(s.display_name, 'NAME')

    def test_friendly_name_when_set(self):
        """Ensure getting friendly name when set returns friendly name"""
        s = MyTestSensor('NAME', 'id')
        s.display_name = 'FRIENDLY'
        self.assertEqual(s.display_name, 'FRIENDLY')

    def test_normal_name(self):
        """Ensure name can be set and returned"""
        s = MyTestSensor('NAME', 'id')
        s.name = 'NAME2'
        self.assertEqual(s.name, 'NAME2')

    def test_invoking_sensorbase_directly(self):
        """Ensure SensorBase raises error if invoked directly"""
        self.assertRaises(NotImplementedError, cchrc.sensors.SensorBase, 'NAME')

    def test_valid_keywords(self):
        """Ensure sensor accepts valid keywords"""
        s = MyTestSensor('NAME', 'id', increment_value=5)
        self.assertEqual(5, s.incr)

    def test_invalid_keywords(self):
        """Ensure sensor rejects invalid keywords"""
        self.assertRaises(cchrc.sensors.InvalidSensorArg,
                          MyTestSensor, 'NAME', 'id', invalid_keyword_arg='some_value')

class TestAveragingSensor(unittest.TestCase):
    """Tests the averaging sensor"""

    def test_empty_readings(self):
        """Ensure empty averaging sensor returns none"""
        avs = cchrc.sensors.AveragingSensor(MyTestSensor('', ''))
        self.assertEqual(avs.get_reading(), None)

    def test_averaging(self):
        """Ensure returned average is correct"""
        avs = cchrc.sensors.AveragingSensor(MyTestSensor('', '',
                                                         increment_value=5), 5)
        avs.collect_reading()
        avs.collect_reading()
        avs.collect_reading()
        value = avs.get_reading()
        self.assertEqual(int(value), 10)

class TestNullSensor(unittest.TestCase):
    """Tests the NullSensor"""

    def test_default_reading(self):
        """Ensure NullSensor returns None"""
        ns = cchrc.sensors.NullSensor('foo', 'bar')
        self.assertTrue(ns.get_reading() is None)

    def test_non_default_reading(self):
        """Ensure NullSensor returns the value given at initialization"""
        ns = cchrc.sensors.NullSensor('foo', 'bar', value='TESTVALUE')
        self.assertEqual(ns.get_reading(), 'TESTVALUE')

class TestOwfsSensor(unittest.TestCase):
    """Test the various OWFS sensor functions and utilities"""

    def test_id_conversion(self):
        """Ensure endianess conversion succeeds"""
        from cchrc.sensors import onewire as ow
        self.assertEqual('28.F76AA8020000',
                         ow._get_owfs_id('BF000002A86AF728'))

    def test_id_conversion_fail(self):
        """Ensure _get_owfs_id blows up when given an already-converted id"""
        from cchrc.sensors import onewire as ow
        self.assertRaises(ow.OwfsIdAlreadyConverted,
                          ow._get_owfs_id, '28.F76AA8020000')

class TestUtils(unittest.TestCase):
    """Test various utilities"""

    def test_parse_sensor_info(self):
        """Ensure the sensor info string is parsed correctly"""
        psi = cchrc.common.parse_sensor_info
        major_param, minor_params = psi('major/a=b;c=d;e=f')
        self.assertTrue(major_param =='major' and
                        minor_params == {'a': 'b', 'c': 'd', 'e': 'f'})

    def test_sensor_get(self):
        """Ensure the correct class is retrieved"""
        self.assertEqual(cchrc.sensors.get('onewire').Sensor,
                         cchrc.sensors.onewire.Sensor)

    def test_mod_list(self):
        """Ensure cchrc.common.mod.mod_list is working: module dir"""
        opd = os.path.dirname
        self.assertEqual(cchrc.common.mod.mod_list(os.path.join(opd(opd(__file__)),
                                                                'common')),
                         ['config', 'datafile', 'exceptions', 'mod'])

    def test_mod_nolist(self):
        """Ensure cchrc.common.mod.mod_list is working: no module dir"""
        temp_dir = tempfile.mkdtemp()
        self.assertEqual(cchrc.common.mod.mod_list(temp_dir), [])
        shutil.rmtree(temp_dir)

    def test_my_sum_all_good(self):
        """Ensure my_sum arrives at the correct sum with all good values"""
        self.assertEqual(cchrc.sensors._my_sum([1,2,3,4,5]), 15)

    def test_my_sum_some_bad(self):
        """Ensure my_sum ignores None and NaN values"""
        self.assertEqual(cchrc.sensors._my_sum([1,2,3,4,5, None, float('nan')]), 15)

    def test_my_sum_all_bad(self):
        """Ensure my_sum returns a sane value for no values"""
        self.assertEqual(cchrc.sensors._my_sum([None, float('nan')]), 0)

class TestSensorCollection(unittest.TestCase):
    """Test operation of the SensorCollection class"""

    def test_adding_sensors(self):
        """Ensure all added sensors are listed"""
        sc = cchrc.common.SensorContainer()
        sc.put(MyTestSensor('X1', 'Y1'), 'Z1')
        sc.put(MyTestSensor('X2', 'Y2'), 'Z1')
        self.assertEqual(str(sc), "<SensorContainer: ('Z1', 'X1', None), ('Z1', 'X2', None)>")

    def test_adding_invalid_object(self):
        """Ensure adding an invalid object raises an error"""
        class TO(object):
            pass
        obj = TO()
        obj.name = 'Some Value'
        sc = cchrc.common.SensorContainer()
        self.assertRaises(InvalidObject, sc.put, obj, 'X1')

    def test_adding_duplicate_sensor(self):
        """Ensure adding another sensor with a duplicate group/name raises and error"""
        sc = cchrc.common.SensorContainer()
        sc.put(MyTestSensor('X1', 'Y1'), 'Z1')
        self.assertRaises(SensorAlreadyDefined, sc.put, MyTestSensor('X1', 'Y1'), 'Z1')

    def test_getting_back_sensor(self):
        """Ensure sensor put in SC is retrieved"""
        sc = cchrc.common.SensorContainer()
        s = MyTestSensor('X1', 'Y1')
        sc.put(s, 'Z1')
        self.assertTrue(s is sc.get('Z1', 'X1'))

    def test_retrieving_invalid_sensor(self):
        """Ensure retrieving an invalid sensor raises an error"""
        sc = cchrc.common.SensorContainer()
        self.assertRaises(SensorNotDefined, sc.get, 'ZZ', 'YY')

    def test_storing_sampling_sensor_as_averaging(self):
        """Ensure trying to store a Sampling sensor as an averaging sensor raises an error"""
        sc = cchrc.common.SensorContainer()
        sc.put(MyTestSensor('X1', 'Y1'), 'Z1')
        self.assertRaises(NotAnAveragingSensor, sc.put, MyTestSensor('X1', 'Y1'), 'Z1', 900)

    def test_storing_averaging_sensor(self):
        """Ensure an averaging sensor is stored properly"""
        sc = cchrc.common.SensorContainer()
        smp_sensor = MyTestSensor('X1', 'Y1')
        avg_sensor = cchrc.sensors.AveragingSensor(smp_sensor)
        sc.put(avg_sensor, 'Z1', interval=900)
        self.assertTrue(75 in sc._SensorContainer__sbsi and
                        sc._SensorContainer__sbsi[75][0] is avg_sensor)

    def test_starting_stopping_sensor_collection(self):
        """Ensure SensorCollection thread starts and stops correctly"""
        sc = cchrc.common.SensorContainer()
        sc.start_averaging_sensors()
        is_alive = sc.isAlive()
        sc.stop_averaging_sensors()
        self.assertTrue(is_alive)

class TestFileAuxOperations(unittest.TestCase):
    """Test operation of auxillary DataFile operations"""
    import cchrc.common.datafile

    def test_split_sensor_info_invalid_mode(self):
        """Ensure error is raised on invalid mode"""
        ssi = cchrc.common.datafile._split_sensor_info
        self.assertRaises(InvalidSensorMode, ssi, 'NAME', 'GROUP', 'BARF')

    def test_split_sensor_info_name_only(self):
        """Ensure correctness with a name and default group and mode"""
        ssi = cchrc.common.datafile._split_sensor_info
        self.assertEqual(('GROUP', 'NAME', 'SAMPLE'),
                         ssi('NAME', 'GROUP', 'SAMPLE'))

    def test_split_sensor_info_name_group(self):
        """Ensure correctness with name and group, and default mode"""
        ssi = cchrc.common.datafile._split_sensor_info
        self.assertEqual(('MYGROUP', 'NAME', 'SAMPLE'),
                         ssi('MYGROUP.NAME', 'GROUP', 'SAMPLE'))

    def test_split_sensor_info_name_group_mode(self):
        """Ensure correctness with name, group, and mode"""
        ssi = cchrc.common.datafile._split_sensor_info
        self.assertEqual(('MYGROUP', 'NAME', 'AVERAGE'),
                         ssi('MYGROUP.NAME/AVERAGE', 'GROUP', 'SAMPLE'))

    def test_split_sensor_info_name_mode(self):
        """Ensure correctness with name and mode, and default group"""
        ssi = cchrc.common.datafile._split_sensor_info
        self.assertEqual(('GROUP', 'NAME', 'AVERAGE'),
                         ssi('NAME/AVERAGE', 'GROUP', 'SAMPLE'))

    def test_rotate_files(self):
        """Ensure proper operation of the file rotater"""
        rotate_files = cchrc.common.datafile._rotate_files
        ope = os.path.exists
        temp_dir = tempfile.mkdtemp()
        path = os.path.join(temp_dir, 'test_file')
        for x in xrange(0, 3):
            if x > 0:
                tpath = path + '.' + str(x)
            else:
                tpath = path
            open(tpath, 'w')

        rotate_files(os.path.join(temp_dir, 'test_file'))

        self.assertTrue(all([ope(path + '.' + str(x)) for x in [1,2,3]]))
        shutil.rmtree(temp_dir)

class TestDataFileRunner(unittest.TestCase):
    def __init__(self, *a, **kw):
        self.DF = cchrc.common.datafile.DataFile
        unittest.TestCase.__init__(self, *a, **kw)

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sc = cchrc.common.SensorContainer()
        self.dfr = cchrc.common.datafile.DataFileRunner()
        self.sc.put(MyTestSensor('T1'), 'TestGroup')
        self.sc.put(MyTestSensor('T2', increment_value=5), 'TestGroup')
        self.sc.put(MyTestSensor('T3', increment_value=10), 'TestGroup')
        self.sc.put(MyTestSensor('T4', increment_value=15), 'TestGroup')
        s = MyTestSensor('T5', increment_value=20)
        s.display_name = 'T5 Display'
        self.sc.put(s, 'TestGroup')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_adding_datafile(self):
        """Ensure adding data file to DFR"""
        d = self.DF('TestID', 'TestFile', self.temp_dir, 'TestGroup',
                    5, 'SAMPLE', ["T1","T2","T5"], self.sc)
        self.dfr.put(d)
        self.assertTrue(len(self.dfr._DataFileRunner__data_files[5]) == 1)

    def test_adding_invalid_datafile_object(self):
        """Ensure adding an invalid object to the DFR fails"""
        d = object()
        self.assertRaises(InvalidObject, self.dfr.put, d)

    def test_adding_duplicate_datafile_object(self):
        """Ensure adding a duplicate file to the DFR fails"""
        d = self.DF('TestID', 'TestFile', self.temp_dir, 'TestGroup',
                    5, 'SAMPLE', ["T1","T2","T5"], self.sc)
        self.dfr.put(d)
        self.assertRaises(DuplicateObject, self.dfr.put, d)

    def test_starting_stopping_datafile_runner(self):
        """Ensure starting and stopping the DFR works"""
        self.dfr.start_data_files()
        is_alive = self.dfr.isAlive()
        self.dfr.stop_data_files()
        self.assertTrue(is_alive)

class TestDataFileOperations(unittest.TestCase):
    def __init__(self, *a, **kw):
        self.DF = cchrc.common.datafile.DataFile
        unittest.TestCase.__init__(self, *a, **kw)

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sc = cchrc.common.SensorContainer()
        self.sc.put(MyTestSensor('T1'), 'TestGroup')
        self.sc.put(MyTestSensor('T2', increment_value=5), 'TestGroup')
        self.sc.put(MyTestSensor('T3', increment_value=10), 'TestGroup')
        self.sc.put(MyTestSensor('T4', increment_value=15), 'TestGroup')
        s = MyTestSensor('T5', increment_value=20)
        s.display_name = 'T5 Display'
        self.sc.put(s, 'TestGroup')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_file_creation(self):
        """Ensure file is created and has correct headers"""
        d = self.DF('TestID', 'TestFile', self.temp_dir, 'TestGroup',
                    5, 'SAMPLE', ["T1","T2","T5"], self.sc)
        self.assertEqual('Timestamp,T1,T2,T5 Display\r\n',
                         get_file(self.temp_dir, 'TestFile'))

    def test_header_supression(self):
        """Ensure file is not given a second set of headers if it already exists"""
        d = self.DF('TestID', 'TestFile', self.temp_dir, 'TestGroup',
                    5, 'SAMPLE', ["T1","T2","T5"], self.sc)
        d = None
        d = self.DF('TestID', 'TestFile', self.temp_dir, 'TestGroup',
                    5, 'SAMPLE', ["T1","T2","T5"], self.sc)
        self.assertEqual('Timestamp,T1,T2,T5 Display\r\n',
                         get_file(self.temp_dir, 'TestFile'))

    def test_file_rotation(self):
        """Ensure files are rotated if the headers do not match"""
        d = self.DF('TestID', 'TestFile', self.temp_dir, 'TestGroup',
                    5, 'SAMPLE', ["T1","T2","T5"], self.sc)
        d = None
        d = self.DF('TestID', 'TestFile', self.temp_dir, 'TestGroup',
                    5, 'SAMPLE', ["T3","T4","T5"], self.sc)
        d = None
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'TestFile'))
                        and os.path.exists(os.path.join(self.temp_dir, 'TestFile.1')))

    def test_collect_data(self):
        """Ensure data is collected and recorded"""
        d = self.DF('TestID', 'TestFile', self.temp_dir, 'TestGroup',
                    5, 'SAMPLE', ["T1","T2","T5"], self.sc)
        d.collect_data()
        d.collect_data()

        csv_file = csv.reader(open(os.path.join(self.temp_dir, 'TestFile')))
        data = csv_file.next()
        data = csv_file.next()
        data = csv_file.next()

        self.assertEqual(data[1:], ['2', '10', '40'])

    def test_invalid_sensor(self):
        """Ensure asking for an invalid sensor raises and error"""
        self.assertRaises(MalformedConfigFile, self.DF, 'TestID', 'TestFile',
                          self.temp_dir, 'TestGroup', 5, 'SAMPLE',
                          ["T1","T2","T6"], self.sc)

    def test_use_new_averaging_sensor(self):
        """Ensure correctness of adding an averaging sensor that is *not* in the SC"""
        d = self.DF('TestID', 'TestFile', self.temp_dir, 'TestGroup',
                    5, 'SAMPLE', ["T1","T2","T5/AVERAGE"], self.sc)
        self.assertTrue(type(d.sensors[2]) is cchrc.sensors.AveragingSensor)

    def test_use_existing_averaging_sensor(self):
        """Ensure correctness of adding an averaging sensor that is in the SC"""
        d1 = self.DF('TestID', 'TestFile', self.temp_dir, 'TestGroup',
                    5, 'SAMPLE', ["T5/AVERAGE"], self.sc)
        d2 = self.DF('TestID', 'TestFile2', self.temp_dir, 'TestGroup',
                    5, 'SAMPLE', ["T5/AVERAGE"], self.sc)
        self.assertTrue(type(d1.sensors[0]) is cchrc.sensors.AveragingSensor
                        and d1.sensors[0] is d2.sensors[0])

    def test_use_invalid_dir(self):
        """Ensure using an invalid directory raises an error"""
        self.assertRaises(BaseDirDoesNotExist, self.DF, 'TestID', 'TestFile',
                          '/tmp/INVALIDDIRXXXXX', 'TestGroup', 5, 'SAMPLE',
                          ["T1"], self.sc)
