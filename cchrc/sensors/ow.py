# OW Sensor

import cchrc.sensors

class Sensor(cchrc.sensors.SensorBase):
    sensor_type = 'ow'
    def __init__(self, sensor_id, name, **kwargs):
        pass

    def get_reading(self):
        pass
