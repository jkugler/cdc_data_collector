import csv
import os
import shutil
import tempfile
import time
import unittest

import cchrc

def get_file(*a):
    """Convenience function to return the contents of a file"""
    return open(os.path.join(*a)).read()

class MyTestSensor(cchrc.sensors.SensorBase):
    def __init__(self, name, sensor_id = None, **kwargs):
        cchrc.sensors.SensorBase.__init__(self, name)
        self.sensor_id = sensor_id
        self.value = 0

        if 'increment_value' in kwargs:
            self.incr = kwargs['increment_value']
        else:
            self.incr = 1

    def get_reading(self):
        self.value += self.incr
        return self.value

class TestSensorBase(unittest.TestCase):
    """Tests the base sensor and its functions"""

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

class TestAveragingSensor(unittest.TestCase):
    """Tests the averaging sensor"""

    def test_empty_readings(self):
        """Ensure empty averaging sensor returns none"""
        avs = cchrc.sensors.AveragingSensor(MyTestSensor('', ''))
        self.assertEqual(avs.get_reading(), None)

    def test_simple_averaging(self):
        """Ensure interval collection"""
        avs = cchrc.sensors.AveragingSensor(MyTestSensor('', ''),
                                            1, 5)
        avs.go()
        time.sleep(1)
        value = avs.get_reading()
        avs.stop()
        self.assertEqual(value, 4)

    def test_odd_interval_averaging(self):
        """Ensure interval collection works even when time_period % num_samples != 0"""
        avs = cchrc.sensors.AveragingSensor(MyTestSensor('', ''),
                                            1, 3)
        avs.go()
        time.sleep(1)
        value = avs.get_reading()
        avs.stop()
        self.assertEqual(value, 3)

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
        self.assertRaises(RuntimeError, ow._get_owfs_id, '28.F76AA8020000')

class TestUtils(unittest.TestCase):
    """Test various utilities"""

    def test_parse_sensor_type(self):
        """Ensure the sensor type string is parsed correctly"""
        pst = cchrc.common.parse_sensor_type
        stype, params = pst('onewire/a=b;c=d;e=f')
        self.assertTrue(stype =='onewire' and
                        params == {'a': 'b', 'c': 'd', 'e': 'f'})

    def test_sensor_get(self):
        """Ensure the correct class is retrieved"""
        self.assertEqual(cchrc.sensors.get('onewire').Sensor,
                         cchrc.sensors.onewire.Sensor)

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
        self.assertRaises(RuntimeError, sc.put, obj, 'X1')

    def test_adding_duplicate_sensor(self):
        """Ensure adding another sensor with a duplicate group/name raises and error"""
        sc = cchrc.common.SensorContainer()
        sc.put(MyTestSensor('X1', 'Y1'), 'Z1')
        self.assertRaises(RuntimeError, sc.put, MyTestSensor('X1', 'Y1'), 'Z1')

    def test_getting_back_sensor(self):
        """Ensure sensor put in SC is retrieved"""
        sc = cchrc.common.SensorContainer()
        s = MyTestSensor('X1', 'Y1')
        sc.put(s, 'Z1')
        self.assertTrue(s is sc.get('Z1', 'X1'))

    def test_retrieving_invalid_sensor(self):
        """Ensure retrieving an invalid sensor raises an error"""
        sc = cchrc.common.SensorContainer()
        self.assertRaises(KeyError, sc.get, 'ZZ', 'YY')

    def test_adding_averaging_sensor_without_corresponding_sample_sensor(self):
        """Ensure an averaging sensor already has a sampling sensor stored"""
        sc = cchrc.common.SensorContainer()
        self.assertRaises(RuntimeError, sc.put, MyTestSensor('X1', 'Y1'), 'Z1', 900)

    def test_storing_sampling_sensor_as_averaging(self):
        """Ensure trying to store a Sampling sensor as an averaging sensor raises an error"""
        sc = cchrc.common.SensorContainer()
        sc.put(MyTestSensor('X1', 'Y1'), 'Z1')
        self.assertRaises(RuntimeError, sc.put, MyTestSensor('X1', 'Y1'), 'Z1', 900)

class TestFileAuxOperations(unittest.TestCase):
    """Test operation of auxillary DataFile operations"""
    import cchrc.common.datafile

    def test_split_sensor_info_invalid_mode(self):
        """Ensure error is raised on invalid mode"""
        ssi = cchrc.common.datafile._split_sensor_info
        self.assertRaises(RuntimeError, ssi, 'NAME', 'GROUP', 'BARF')

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

class TestDataFileOperations(unittest.TestCase):
    def __init__(self, *a, **kw):
        self.df = cchrc.common.datafile.DataFile
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
        d = self.df('TestID', 'TestFile', self.temp_dir, 'TestGroup',
                    5, 'SAMPLE', ["T1","T2","T5"], self.sc)
        self.assertEqual('Timestamp,T1,T2,T5 Display\r\n',
                         get_file(self.temp_dir, 'TestFile'))

    def test_file_rotation(self):
        """Ensure files are rotated if the headers do not match"""
        d = self.df('TestID', 'TestFile', self.temp_dir, 'TestGroup',
                    5, 'SAMPLE', ["T1","T2","T5"], self.sc)
        d = None
        d = self.df('TestID', 'TestFile', self.temp_dir, 'TestGroup',
                    5, 'SAMPLE', ["T3","T4","T5"], self.sc)
        d = None
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'TestFile'))
                        and os.path.exists(os.path.join(self.temp_dir, 'TestFile.1')))

    def test_collect_data(self):
        """Ensure data is collected and recorded"""
        d = self.df('TestID', 'TestFile', self.temp_dir, 'TestGroup',
                    5, 'SAMPLE', ["T1","T2","T5"], self.sc)
        d.collect_data()
        d.collect_data()

        csv_file = csv.reader(open(os.path.join(self.temp_dir, 'TestFile')))
        data = csv_file.next()
        data = csv_file.next()
        data = csv_file.next()

        self.assertEqual(data[1:], ['2', '10', '40'])
