import os
import time
import unittest

import cchrc

class TestSensor(cchrc.sensors.SensorBase):
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
        avs = cchrc.sensors.AveragingSensor(TestSensor('', ''))
        self.assertEqual(avs.get_reading(), None)

    def test_simple_averaging(self):
        """Ensure interval collection"""
        avs = cchrc.sensors.AveragingSensor(TestSensor('', ''),
                                            1, 5)
        avs.go()
        time.sleep(1)
        value = avs.get_reading()
        avs.stop()
        self.assertEqual(value, 4)

    def test_odd_interval_averaging(self):
        """Ensure interval collection works even when time_period % num_samples != 0"""
        avs = cchrc.sensors.AveragingSensor(TestSensor('', ''),
                                            1, 3)
        avs.go()
        time.sleep(1)
        value = avs.get_reading()
        avs.stop()
        self.assertEqual(value, 3)

class TestOwfsSensor(unittest.TestCase):
    """Test the various OWFS sensor functions and utilities"""

    def test_id_conversion(self):
        """Test conversion of IDs from documentation form to OWFS form"""
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
