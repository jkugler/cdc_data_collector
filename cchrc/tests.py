import os
import time
import unittest

import cchrc

class MyTestSensor(cchrc.sensors.SensorBase):
    def __init__(self, sensor_id, name, **kwargs):
        self.sensor_id = sensor_id
        self.name = name
        self.value = 0

        if 'increment_value' in kwargs:
            self.incr = kwargs['increment_value']
        else:
            self.incr = 1

    def get_reading(self):
        self.value += self.incr
        return self.value

class TestSensorBase(unittest.TestCase):
    """Tests the base sensor"""

    def test_base_attributes(self):
        """Ensure SensorBase has all needed attributes"""
        self.assertTrue(hasattr(cchrc.sensors.SensorBase, '__init__') and
                        hasattr(cchrc.sensors.SensorBase, 'get_reading'))

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
        sc.put(MyTestSensor('X1', 'Y1'), 'Z1', 'Y1')
        sc.put(MyTestSensor('X2', 'Y2'), 'Z1', 'Y2')
        self.assertEqual(str(sc), "<SensorContainer: ('Z1', 'Y1'), ('Z1', 'Y2')>")

    def test_adding_invalid_object(self):
        """Ensure adding an invalid object raises an error"""
        sc = cchrc.common.SensorContainer()
        self.assertRaises(RuntimeError, sc.put, list(), 'X1', 'Y1')

    def test_adding_duplicate_sensor(self):
        """Ensure adding another sensor with a duplicate group/name raises and error"""
        sc = cchrc.common.SensorContainer()
        sc.put(MyTestSensor('X1', 'Y1'), 'Z1', 'Y1')
        self.assertRaises(RuntimeError, sc.put, MyTestSensor('X1', 'Y1'), 'Z1', 'Y1')
