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
                                            10, 5)
        avs.go()
        time.sleep(11)
        value = avs.get_reading()
        avs.stop()
        self.assertEqual(value, 4)

    def test_odd_interval_averaging(self):
        """Ensure interval collection works even when time_period % num_samples != 0"""
        avs = cchrc.sensors.AveragingSensor(TestSensor('', ''),
                                            10, 3)
        avs.go()
        time.sleep(10)
        value = avs.get_reading()
        avs.stop()
        self.assertEqual(value, 3)
