import logging

import cchrc
import datafile

def parse_sensor_info(info_string):
    major_param, minor_params_string = info_string.split('/')

    minor_params = dict([x.split('=') for x in minor_params_string.split(';')])

    return major_param, minor_params

def is_true(x):
    """Test a config file value for truth"""
    rv = False
    if isinstance(x, basestring) and not x.isdigit():
        if x.lower() != 'false' and bool(x):
            rv = True
    else:
        x = int(x)
        if bool(x):
            rv = True

    return rv

def listify(v):
    """
    If v is a string, returns a list with a single element of v
    """
    if isinstance(v, basestring):
        v = [v]
    return v

def construct_sensor_collection(cfg):
    sc = cchrc.sensors.SensorContainer()
    log = logging.getLogger('cchrc.common.construct_sensor_collection')

    for group in cfg['SensorGroups']:
        if '/' in cfg['SensorGroups'][group]['SensorType']:
            stype, group_params = cchrc.common.parse_sensor_info(cfg['SensorGroups'][group]['SensorType'])
        else:
            stype = cfg['SensorGroups'][group]['SensorType']
            group_params = {}

        log.debug("Configuring group '%s' with SensorType '%s' and params '%s'",
                  group, stype, str(group_params))

        sensors = cfg['SensorGroups'][group]['Sensors']
        for sensor in sensors:
            name = sensor
            if '/' in sensors[sensor]:
                sensor_id, sensor_params = cchrc.common.parse_sensor_info(sensors[sensor])
            else:
                sensor_id = sensors[sensor]
                sensor_params = {}

            all_params = {}
            all_params.update(group_params)
            all_params.update(sensor_params)
            # TODO: This can throw a KeyError...catch it.
            # TODO: Create an exception a sensor module can throw upon
            # failure to initialize a sensor, and catch it here.
            log.debug("Configuring sensor '%s' with id '%s' and params '%s'",
                      name, sensor_id, str(all_params))
            sobject = cchrc.sensors.get(stype).Sensor(name, sensor_id, **all_params)
            if group + '.' + name in cfg['Names']:
                display_name = cfg['Names'][group + '.' + name]
                log.debug("Giving sensor '%s' display name '%s'",
                          name, display_name)
                sobject.display_name = display_name
            log.debug("Putting sensor '%s' in SC", name)
            sc.put(sobject, group)

    return sc

def construct_data_file_runner(cfg, test, sc):
    DF = datafile.DataFile
    log = logging.getLogger('cchrc.common.construct_data_file_runner')
    dfr = datafile.DataFileRunner()

    for data_file in cfg['Files']:
        fcfg = cfg['Files'][data_file]
        if test:
            sampling_time = 60
        else:
            sampling_time = int(fcfg['SamplingTime'])
        log.debug("Configuring datafile '%s' with sampling time %s",
                  data_file, sampling_time)
        dfr.put(DF(data_file, fcfg['FileName'], cfg['Main']['BaseDirectory'],
                   fcfg['DefaultGroup'], sampling_time,
                   fcfg['DefaultMode'], listify(fcfg['Sensors']), sc))
    return dfr
