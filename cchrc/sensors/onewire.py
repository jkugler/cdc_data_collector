# OW Sensor

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
    connection_initialized = False
    valid_kwargs = ['connection']

    def __init__(self, name, sensor_id, **kwargs):
        cchrc.sensors.SensorBase.__init__(self, name, **kwargs)

        if sensor_id[2] == '.':
            self.sensor_id = sensor_id
        else:
            self.sensor_id = _get_owfs_id(sensor_id)

        connection_type = kwargs['connection']

        if not Sensor.connection_initialized:
            ow.init(connection_type)
            Sensor.connection_initialized = True
            Sensor.initialized_connection_type = connection_type
        elif (Sensor.connection_initialized and
              (Sensor.initialized_connection_type != connection_type)):
            raise OwfsConnectionAlreadyInitialized("OneWire Connection already initialized to '%s' "
                                                   "but an attempt was made to initalize to '%s'" %
                                                   (Sensor.initialized_connection_type, connection_type))

    def get_reading(self):
        pass
