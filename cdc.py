#!/usr/bin/python

from collections import defaultdict
import optparse
import os
import sys

import cchrc

def listify(v):
    """
    If v is a string, returns a list with a single element of v
    """
    if isinstance(v, basestring):
        v = [v]
    return v

def get_opts():
    usage = 'usage: %prog [options] path-to-ini'
    parser = optparse.OptionParser(usage=usage)
    a = parser.add_option
    a('-t', '--test', action='store_true', dest='test',
      help='Run CDC in test mode. (Sampling every 60 seconds)')
    parser.set_defaults(test=False)

    opts, args = parser.parse_args()

    if not args:
        parser.error("Must provide an ini file on the command line")

    return opts, args

def main():
    DF = cchrc.common.datafile.DataFile
    sc = cchrc.common.SensorContainer()
    dfr = cchrc.common.datafile.DataFileRunner()
    opts, args = get_opts()

    cfg = cchrc.common.config.Config(args[0], opts.test)

    for group in cfg['SensorGroups']:
        stype, params = cchrc.common.parse_sensor_type(cfg['SensorGroups'][group]['SensorType'])
        sensors = cfg['SensorGroups'][group]['Sensors']
        for sensor in sensors:
            name = sensor
            sensor_id = sensors[sensor]
            sobject = cchrc.sensors.get(stype).Sensor(sensor_id, name, **params)
            if group + '.' + name in cfg['Names']:
                sobject.display_name = cfg['Names'][group + '.' + name]
            sc.put(sobject, group, name)

    for data_file in cfg['Files']:
        fcfg = cfg['Files'][data_file]
        dfr.put(DF(data_file, fcfg['FileName'], cfg['Main']['BaseDirectory'],
                   fcfg['DefaultGroup'], fcfg['SamplingTime'],
                   fcfg['DefaultMode'], listify(fcfg['Sensors']), sc))

if __name__ == '__main__':
    main()
