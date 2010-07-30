#!/usr/bin/python

from collections import defaultdict
import optparse
import os
import sys

from configobj import ConfigObj
import pubsub

import cchrc.common.mod

class DataFile(object):
    def __init__(self, sensors, out_path, interval=60*60):
        """
        sensors is a list of Sensor objects
        out_path is the path to the data file being written
        internval is the interval to sample and record (in seconds)
        """

        # Get names of sensors and construct data file header row
        # Open out_path as CSV Dict
        # Check to make sure the header matches sensor names
        # If not, close file, rename using .0, .1, .2 etc
        #  The *higher* the number, the older the file
        #  Reopen file
        #

    def collect_data(self):
        pass

class SensorContainer(object):
    def __init__(self):
        pass

    def put_sensor(self, sobject, group, name, mode='SAMPLE'):
        pass

    def get_sensor(self, group, name, mode='SAMPLE'):
        pass

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

def get_config(ini_file, test_mode):
    cfg = ConfigObj(ini_file, list_values=True, file_error=True)

    if test_mode:
        for data_file in cfg['Files']:
            cfg['Files'][data_file]['SamplingTime'] = 60

    return cfg

def main():
    sc = SensorContainer()
    opts, args = get_opts()

    cfg = get_config(args[0], opts.test)

    for group in cfg['SensorGroups']:
        stype, params = cchrc.common.parse_sensor_type(cfg['SensorGroups'][group]['SensorType'])
        sensors = cfg['SensorGroups'][group]['Sensors']
        for sensor in sensors:
            name = sensor
            sensor_id = sensors[sensor]
            sobject = cchrc.sensors.get(stype)(sensor_id, name, **params)
            sc.put_sensor(sobject, group, name)

if __name__ == '__main__':
    main()
