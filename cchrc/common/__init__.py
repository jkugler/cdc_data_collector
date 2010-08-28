import cchrc

class SensorContainer(object):
    def __init__(self):
        self.__sensors = {}

    def put(self, sobject, group, name, interval=None):
        if not isinstance(sobject, cchrc.sensors.SensorBase):
            # TODO: InvalidObject
            raise RuntimeError("'%s' is not a Sensor object" % str(sobject))
        if self.contains(group, name, interval):
            # TODO: SensorAlreadyDefined
            raise RuntimeError("Sensor in group '%s' with namne '%s' is already defined" % (group, name))
        if interval and not self.contains(group, name, None):
            # Averaging sensor needs sampling sensor defined, or something
            # is wrong.
            # TODO: OrphanAveragingSensor
            raise RuntimeError("No sampling sensor for averaging sensor %s.%s"
                               % (group, name))
        if interval and not isinstance(sobject, cchrc.sensors.AveragingSensor):
            # Trying to store a Sampling sensor as an averaging sensor?
            # Something is broken
            # TODO: NotAnAveragingSensor
            raise RuntimeError("Sensor %s.%s is not an averaging sensor"
                               % (group, name))
        self.__sensors[(group, name, interval)] = sobject

    def get(self, group, name, interval=None):
        try:
            return self.__sensors[(group, name, interval)]
        except KeyError:
            # TODO: SensorNotDefined
            raise KeyError("No sensor defined for group '%s', name '%s'" % (group, name))

    def contains(self, group, name, interval=None):
        return (group, name, interval) in self.__sensors

    def __str__(self):
        return '<SensorContainer: ' + ', '.join(sorted([str(x) for x in self.__sensors.keys()])) + '>'

def parse_sensor_type(type_string):
    stype, params_string = type_string.split('/')

    params = dict([x.split('=') for x in params_string.split(';')])

    return stype, params
