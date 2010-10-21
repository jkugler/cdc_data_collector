import cchrc
from collections import defaultdict
import config
import datafile
import logging
import threading
import time

from cchrc.common.exceptions import (InvalidObject, SensorAlreadyDefined,
                                     NotAnAveragingSensor, SensorNotDefined)

class SensorContainer(threading.Thread):
    def __init__(self):
        self.__end_thread = False
        self.__sensors = {}
        self.__sbsi = defaultdict(list) # sensors by sampling interval
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
                if elapsed_time % st == 0:
                    self.log.debug("Running '%s' files" % st)
                    # TODO: Make this use futures
                    for sensor in self.__sbsi[st]:
                        sensor.collect_reading()
                    pass

            time.sleep(1)

    def start_averaging_sensors(self):
        self.log.info('Starting')
        self.start()

    def put(self, sobject, group, interval=None):
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

def parse_sensor_info(info_string):
    major_param, minor_params_string = info_string.split('/')

    minor_params = dict([x.split('=') for x in minor_params_string.split(';')])

    return major_param, minor_params
