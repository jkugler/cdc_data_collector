import collections
import threading
import time

import cchrc.common.mod

class InvalidSensorArg(Exception):
    pass

def list_all():
    return cchrc.common.mod.mod_list(__path__[0])

def get(name):
    return cchrc.common.mod.get(__name__, name)

class SensorBase(object):
    """
    This will be a base class and will probably never be instantiated directly.
    """
    sensor_type = 'base'
    _display_name = None
    def __init__(self, name, sensor_id=None, **kwargs):
        if self.__class__ is SensorBase:
            raise NotImplementedError

        for key in kwargs.keys():
            if key not in self.valid_kwargs:
                raise InvalidSensorArg("Arg '%s' is invalid for sensor type '%s'"
                                       % (key, type(self)))
        self.__name = name

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        self.__name = name

    def get_reading(self): # pragma: no cover
        """
        Sensor-type-specifc read method
        A valid reading MUST be float or int
        A Python None indicates a reading was not available
            Will be recorded as "N/A" in the data file.
        A float('nan') indicates some undefined error
            (sensor-type dependent)
        """
        raise NotImplementedError

    @property
    def display_name(self):
        if self._display_name:
            return self._display_name
        else:
            return self.__name

    @display_name.setter
    def display_name(self, value):
        self._display_name = value

class AveragingSensor(SensorBase):
    """
    A "sensor" that will record readings when instructed, and return
    an average when asked for its reading.
    """

    def __init__(self, sensor, num_samples=12):
        """
        sensor is a Sensor object
        time_period is in seconds
        samples is the number of samples to take in time_period.
        """
        SensorBase.__init__(self, sensor.name)
        self.sensor = sensor
        self.num_samples = num_samples
        self.readings = collections.deque([], num_samples)
        self.display_name = sensor.name + '_avg'

    def get_reading(self):
        """
        Return current average
        """
        if not self.readings:
            return None

        readings = list(self.readings)
        return sum(readings)/float(len(readings))

    def collect_reading(self):
        self.readings.append(self.sensor.get_reading())

class NullSensor(SensorBase):
    """
    A "sensor" that will always return None or the configured value,
    when asked for its reading.
    Used when a sensor cannot be found during sensor initialization,
    or for testing.
    """
    sensor_type = 'null'
    valid_kwargs = ['value']

    def __init__(self, name, sensor_id=None, **kwargs):
        cchrc.sensors.SensorBase.__init__(self, name, **kwargs)
        self.value = kwargs.get('value', None)

    def get_reading(self):
        return self.value
