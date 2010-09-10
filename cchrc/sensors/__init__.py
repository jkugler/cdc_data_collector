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

    # This is also required to override threading.Thread's name property

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        self.__name = name

    def get_reading(self): # pragma: no cover
        """
        Sensor-type-specifc read method
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
