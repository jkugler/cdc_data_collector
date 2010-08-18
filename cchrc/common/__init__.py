import cchrc

class SensorContainer(object):
    def __init__(self):
        self.__sensors = {}

    def put(self, sobject, group, name):
        if not isinstance(sobject, cchrc.sensors.SensorBase):
            # InvalidObject - ?
            raise RuntimeError("'%s' is not a Sensor object" % str(sobject))
        if (group, name) in self.__sensors:
            # SensorAlreadyDefined
            raise RuntimeError("Sensor in group '%s' with namne '%s' is already defined" % (group, name))
        self.__sensors[(group, name)] = sobject

    def get(self, group, name):
        try:
            return self.__sensors[(group, name)]
        except KeyError:
            # SensorNotDefined
            raise KeyError("No sensor defined for group '%s', name '%s'" % (group, name))

    def __str__(self):
        return '<SensorContainer: ' + ', '.join(sorted([str(x) for x in self.__sensors.keys()])) + '>'

def parse_sensor_type(type_string):
    stype, params_string = type_string.split('/')

    params = dict([x.split('=') for x in params_string.split(';')])

    return stype, params
