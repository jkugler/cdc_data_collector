import threading

import cchrc.common.mod

def list_all():
    return cchrc.common.mod.mod_list(__path__[0])

def get(name):
    return cchrc.common.mod.get(__name__, name)

class SensorBase(object):
    """
    This will be a base class and will probably never be instantiated directly.
    """
    def __init__(self, sensor_id, name, **kwargs):
        raise NotImplemented

    def get_reading(self):
        """
        Sensor-type-specifc read method
        """
        raise NotImplemented

class AveragingSensor(threading.Thread):
    """
    A "sensor" that will average over the given time period and return
    the average when asked for its reading
    """
    def __init__(self, sensor, time_period=15*60, samples=12):
        """
        sensor is a Sensor object
        time_period is in seconds
        samples is the number of samples to take in time_period.
        """
        self.reading = None

    def get_reading(self):
        """
        Return current value of self.average
        """
        pass
