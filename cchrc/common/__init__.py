def parse_sensor_type(type_string):
    stype, params_string = type_string.split('/')

    params = dict([x.split('=') for x in params_string.split(';')])

    return stype, params
