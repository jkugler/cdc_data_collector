# OW Sensor

import ow

import cchrc.sensors

initialized_connection_type = None
connection_initialized = False

def _get_owfs_id(sensor_id):
    """
    Converts ids from the form found on the packaging (BF000002A86AF728)
    to the form required by owfs to address the sensors (28.F76AA8020000)
    """
    if '.' in sensor_id:
        raise RuntimeError("Given id '%s' to convert, but id already has a "
                           "'.' in it. Something is wrong")

    return ''.join([sensor_id[-2:], '.'] +
                   [sensor_id[x*2:x*2+2] for x in xrange(6,0,-1)])

class Sensor(cchrc.sensors.SensorBase):
    sensor_type = 'ow'
    def __init__(self, sensor_id, name, **kwargs):
        self.name = name

        if sensor_id[2] == '.':
            self.sensor_id = sensor_id
        else:
            self.sensor_id = _get_owfs_id(sensor_id)

        connection_type = kwargs['connection']

        if not connection_initialized:
            ow.init(connection_type)
            connection_initialized = True
            initialized_connection_type = connection_type
        elif (connection_initialized and
              (initialized_connection_type != connection_type)):
            raise RuntimeError("OneWire Connection already initialized to '%s' "
                               "but an attempt was made to initalize to '%s'" %
                               (initialized_connection_type, connection_type))

    def get_reading(self):
        pass
