import os

import cchrc

def get_file(*a):
    """Convenience function to return the contents of a file"""
    return open(os.path.join(*a)).read()

class MyTestSensor(cchrc.sensors.SensorBase):
    valid_kwargs = ['increment_value']

    def __init__(self, name, sensor_id = None, **kwargs):
        cchrc.sensors.SensorBase.__init__(self, name, **kwargs)
        self.sensor_id = sensor_id
        self.value = 0

        if 'increment_value' in kwargs:
            self.incr = kwargs['increment_value']
        else:
            self.incr = 1

    def get_reading(self):
        self.value += self.incr
        return self.value
