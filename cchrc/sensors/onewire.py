# OW Sensor
import logging
import os
import threading
import time

import ow

import cchrc.sensors

class OwfsConnectionAlreadyInitialized(Exception):
    pass

class OwfsIdAlreadyConverted(Exception):
    pass

def _get_owfs_id(sensor_id):
    """
    Converts ids from the form found on the packaging (BF000002A86AF728)
    to the form required by owfs to address the sensors (28.F76AA8020000)
    """
    if '.' in sensor_id:
        raise OwfsIdAlreadyConverted("Given id '%s' to convert, but id already has a "
                           "'.' in it. Something is wrong")

    return ''.join([sensor_id[-2:], '.'] +
                   [sensor_id[x*2:x*2+2] for x in xrange(6,0,-1)])

class Sensor(cchrc.sensors.SensorBase):
    sensor_type = 'ow'
    initialized_connection_type = None
    sensors = {}
    valid_kwargs = ['connection', 'sa', 'use_cache']

    @classmethod
    def _get_all(klass, sensor, sensors):
        for s in sensor.sensors():
            sensors[os.path.basename(s._path)] = s._path
            klass._get_all(s, sensors)

    @classmethod
    def _initialize_ow(klass, connection_type):
        ow.init(connection_type)
        klass._get_all(ow.Sensor('/'), klass.sensors)

    def __init__(self, name, sensor_id, **kwargs):
        cchrc.sensors.SensorBase.__init__(self, name, **kwargs)
        self.sensor = None
        self.last_sample_time = 0
        self.last_sample_value = None
        self.lock = threading.Lock()
        self.log = logging.getLogger('cchrc.sensors.onewire.Sensor')

        self.original_sensor_id = sensor_id
        if sensor_id[2] == '.':
            self.sensor_id = sensor_id
        else:
            self.sensor_id = _get_owfs_id(sensor_id)

        connection_type = kwargs['connection']
        # TODO: Check that this attribute actually exists on the sensor
        # being initialized.
        self.sensor_attribute = kwargs.get('sa', 'temperature')

        x = kwargs.get('use_cache', 'False')
        if x.isdigit():
            x = int(x)
        if x != 'False' and bool(x):
            use_cache = True
        else:
            use_cache = False

        if not ow.initialized:
            self.log.debug("Initializing OW connection")
            self._initialize_ow(connection_type)
            Sensor.initialized_connection_type = connection_type
        elif (ow.initialized and
              (Sensor.initialized_connection_type != connection_type)):
            raise OwfsConnectionAlreadyInitialized("OneWire Connection already initialized to '%s' "
                                                   "but an attempt was made to initalize to '%s'" %
                                                   (Sensor.initialized_connection_type, connection_type))

        # TODO: This can generage a KeyError. Need to catch it
        self.log.info("Initializing OW sensor '%s'" % self.original_sensor_id)
        self.sensor = ow.Sensor(self.sensors[self.sensor_id])
        self.sensor.useCache(use_cache)

    def get_reading(self):
        self.lock.acquire()
        self.log.debug("Getting reading for '%s'" % self.sensor_id)
        if (time.time() - self.last_sample_time) > 2:
            try:
                self.last_sample_value = float(getattr(self.sensor, self.sensor_attribute))
            except ow.exUnknownSensor, ex:
                self.log.critical("Error getting reading from sensor '%s': '%s'" %
                                  self.original_sensor_id, str(ex))
                self.last_sample_value = None
            except Exception, ex:
                self.log.critical("Unhandlded exception getting reading from sensor '%s': '%s'" %
                                  self.original_sensor_id, str(ex))

            self.last_sample_time = time.time()

        self.lock.release()
        return self.last_sample_value
