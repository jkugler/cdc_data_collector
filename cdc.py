#!/usr/bin/python

from collections import defaultdict
import signal
import optparse
import os
import sys
import time

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

class Mother(object):
    def __init__(self, start_callables, stop_callables):
        self.start_callables = start_callables
        self.stop_callables = stop_callables
        self.ended = False

    def start(self):
        for c in self.start_callables:
            c()

    def stop(self, sig, stack_frame):
        for c in self.stop_callables:
            c()
        self.ended = True

def main():
    DF = cchrc.common.datafile.DataFile
    sc = cchrc.common.SensorContainer()
    dfr = cchrc.common.datafile.DataFileRunner()
    opts, args = get_opts()

    cfg = cchrc.common.config.Config(args[0])

    for group in cfg['SensorGroups']:
        stype, group_params = cchrc.common.parse_sensor_info(cfg['SensorGroups'][group]['SensorType'])
        sensors = cfg['SensorGroups'][group]['Sensors']
        for sensor in sensors:
            name = sensor
            sensor_id, sensor_params = cchrc.common.parse_sensor_info(sensors[sensor])
            params = {}
            params.update(group_params)
            params.update(sensor_params)
            sobject = cchrc.sensors.get(stype).Sensor(sensor_id, name, **params)
            if group + '.' + name in cfg['Names']:
                sobject.display_name = cfg['Names'][group + '.' + name]
            sc.put(sobject, group, name)

    for data_file in cfg['Files']:
        fcfg = cfg['Files'][data_file]
        if opts.test:
            sampling_time = 60
        else:
            sample_time = int(fcfg['SamplingTime'])
        dfr.put(DF(data_file, fcfg['FileName'], cfg['Main']['BaseDirectory'],
                   fcfg['DefaultGroup'], sample_time,
                   fcfg['DefaultMode'], listify(fcfg['Sensors']), sc))

    mom = Mother([sc.start_averaging_sensors, dfr.start_data_files],
                 [sc.stop_averaging_sensors, dfr.stop_data_files])

    mom.start()

    signal.signal(signal.SIGTERM, mom.stop)
    signal.signal(signal.SIGINT, mom.stop)

    while True:
        # Putting a 'while True' loop here for "future expansion," such as
        # printing out system stats on a SIGUSR1 or some such
        signal.pause()
        if mom.ended:
            return

if __name__ == '__main__':
    main()
