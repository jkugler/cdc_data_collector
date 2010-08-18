import collections
import threading
import time

import cchrc.common.mod

def list_all():
    return cchrc.common.mod.mod_list(__path__[0])

def get(name):
    return cchrc.common.mod.get(__name__, name)

class SensorBase(object):
    """
    This will be a base class and will probably never be instantiated directly.
    """
    sensor_type = 'base'
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
    def __init__(self, sensor, time_period=15*60, num_samples=12):
        """
        sensor is a Sensor object
        time_period is in seconds
        samples is the number of samples to take in time_period.
        """
        self.sensor = sensor
        self.readings = collections.deque([], num_samples)
        self.end_thread = False
        self.start_time = None
        self.check_interval = time_period/float(num_samples)
        threading.Thread.__init__(self)

    def run(self):
        self.start_time = time.time()
        while True:
            if self.end_thread:
                return
            self.readings.append(self.sensor.get_reading())
            time.sleep(self.check_interval - ((time.time() - self.start_time) % self.check_interval))

    def get_reading(self):
        """
        Return current average
        """
        if not self.readings:
            return None

        readings = list(self.readings)
        return sum(readings)/len(readings)

    def go(self):
        self.start()

    def stop(self):
        self.end_thread = True
