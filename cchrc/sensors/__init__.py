from collections import defaultdict, deque
import logging
import math
import threading
import time

import cchrc.common.mod

class InvalidSensorArg(Exception):
    pass

def list_all():
    return cchrc.common.mod.mod_list(__path__[0])

def get(name):
    return cchrc.common.mod.get(__name__, name)

def _my_sum(values):
    # Yes, I know I could do this in-line, but it is more
    # easily testable this way.
    return sum([x for x in values if (x is not None and not math.isnan(x))])

import futures

from cchrc.common.exceptions import (InvalidObject, SensorAlreadyDefined,
                                     NotAnAveragingSensor, SensorNotDefined)

class SensorContainer(threading.Thread):
    def __init__(self):
        self.__end_thread = False
        self.__sensors = {}
        self.__sbsi = defaultdict(list) # sensors by sampling interval
        self.__silr = defaultdict(int) # sampling interval k was run at v seconds
        self.__start_time = None
        self.log = logging.getLogger('cchrc.common.SensorContainer')
        threading.Thread.__init__(self)

    def run(self):
        self.__start_time = int(time.time())
        while True:
            if self.__end_thread:
                return # pragma: no cover
            elapsed_time = int(time.time()) - self.__start_time
            for st in self.__sbsi:
                if ((elapsed_time % st == 0) or
                    ((elapsed_time - self.__silr[st]) > st)):
                    self.log.debug("Running '%s second' averaging sensors; "
                                   "last run %s seconds ago",
                                   st, elapsed_time - self.__silr[st])
                    self.__silr[st] = elapsed_time
                    with futures.ThreadPoolExecutor(len(self.__sbsi[st])) as executor:
                        for sensor in self.__sbsi[st]:
			    executor.submit(sensor.collect_reading)
            # Sleep to the top of the next second
            cur_time = time.time()
            time.sleep(math.ceil(cur_time) - cur_time)

    def start_averaging_sensors(self):
        self.log.info('Starting')
        self.start()

    def put(self, sobject, group, interval=None):
        # TODO: Put the group into the sensor itself
        name = sobject.name
        if not isinstance(sobject, cchrc.sensors.SensorBase):
            raise InvalidObject("'%s' is not a Sensor object" % str(sobject))
        if self.contains(group, name, interval):
            raise SensorAlreadyDefined("Sensor in group '%s' with name '%s' is already defined" % (group, name))
        if interval and not isinstance(sobject, cchrc.sensors.AveragingSensor):
            # Trying to store a Sampling sensor as an averaging sensor?
            # Something is broken
            raise NotAnAveragingSensor("Sensor %s.%s is not an averaging sensor"
                               % (group, name))
        self.log.info("Adding %s, %s with interval %s" % (group, name, interval))
        self.__sensors[(group, name, interval)] = sobject
        if interval:
            self.__sbsi[interval/sobject.num_samples].append(sobject)

    def get(self, group, name, interval=None):
        try:
            return self.__sensors[(group, name, interval)]
        except KeyError:
            raise SensorNotDefined("No sensor defined for group '%s', name '%s'" % (group, name))

    def contains(self, group, name, interval=None):
        return (group, name, interval) in self.__sensors

    def __str__(self):
        return '<SensorContainer: ' + ', '.join(sorted([str(x) for x in self.__sensors.keys()])) + '>'

    def stop_averaging_sensors(self):
        self.log.info('Stopping')
        self.__end_thread = True


class SensorBase(object):
    """
    This will be a base class and will probably never be instantiated directly.
    TODO: Add something to the API that will store an "internal name" that
    can be extracted for log messages and the like, because sensor.name
    could be non-unique across sensor groups. Maybe store the sensor's group
    in the sensor data.  Yeah...storing the sensor's group in the sensor would
    probably be the best idea.
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
        self.readings = deque([], num_samples)
        self.display_name = sensor.name + '_avg'
        self.log = logging.getLogger('cchrc.sensors.AveragingSensor')

    def get_reading(self):
        """
        Return current average
        """
        if not self.readings:
            return None

        readings = list(self.readings)
        return _my_sum(readings)/float(len(readings))

    def collect_reading(self):
        self.log.debug("Getting reading for sensor '%s'" % self.sensor.name)
        self.readings.append(self.sensor.get_reading())

