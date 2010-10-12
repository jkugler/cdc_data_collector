# OW Sensor
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
        # TODO: InvalidIdForConversion
        raise OwfsIdAlreadyConverted("Given id '%s' to convert, but id already has a "
                           "'.' in it. Something is wrong")

    return ''.join([sensor_id[-2:], '.'] +
                   [sensor_id[x*2:x*2+2] for x in xrange(6,0,-1)])

class Sensor(cchrc.sensors.SensorBase): # pragma: no cover
    sensor_type = 'ow'
    initialized_connection_type = None
    sensors = {}
    valid_kwargs = ['connection', 'sn', 'use_cache']

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

        if sensor_id[2] == '.':
            self.sensor_id = sensor_id
        else:
            self.sensor_id = _get_owfs_id(sensor_id)

        connection_type = kwargs['connection']
        self.sensor_attribute = kwargs.get('sa', 'temperature')

        x = kwargs.get('use_cache', 'False')
        if x.isdigit():
            x = int(x)
        if x != 'False' and bool(x):
            use_cache = True

        if not ow.initialized:
            self._initialize_ow(connection_type)
            Sensor.initialized_connection_type = connection_type
        elif (ow.initialized and
              (Sensor.initialized_connection_type != connection_type)):
            raise OwfsConnectionAlreadyInitialized("OneWire Connection already initialized to '%s' "
                                                   "but an attempt was made to initalize to '%s'" %
                                                   (Sensor.initialized_connection_type, connection_type))

        self.sensor = ow.Sensor(self.sensors[sensor_id])
        self.sensor.useCache(use_cache)

    def get_reading(self):
        self.lock.acquire()
        if (time.time() - self.last_sample_time) > 2:
            self.last_sample_value = getattr(self.sensor, self.sensor_attribute)
            self.last_sample_time = time.time()

        self.lock.release()
        return self.last_sample_value
