# Null Sensor
import cchrc

class Sensor(cchrc.sensors.SensorBase):
    """
    A "sensor" that will always return None or the configured value,
    when asked for its reading.
    Used when a sensor cannot be found during sensor initialization,
    or for testing.
    """
    sensor_type = 'null'
    valid_kwargs = ['value']

    def __init__(self, name, sensor_id=None, **kwargs):
        cchrc.sensors.SensorBase.__init__(self, name, **kwargs)
        self.value = kwargs.get('value', None)

    def get_reading(self):
        return self.value
