#!/usr/bin/python

from collections import defaultdict
import logging
import optparse
import os
import signal
import sys
import time

import configobj

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
    a('-r', '--run-in-forground', action='store_true', dest='run_in_foreground',
      help="Stay in the foreground and log to the console. Exit via Ctrl-C")
    a('-t', '--test', action='store_true', dest='test',
      help='Run CDC in test mode. (Sampling every 60 seconds)')
    a('-v', action='count', dest='verbose', help = 'Verbosity. '
      "Default is 'warning'; specify once for 'info' and twice for 'debug'")
    parser.set_defaults(run_in_foreground=False, test=False, verbose=0)

    opts, args = parser.parse_args()

    if not args:
        parser.error("Must provide an ini file on the command line")

    return opts, args

def configure_logging(cfg, opts):
    """Configures the root logger and returns it"""
    LEVELS = {'debug': logging.DEBUG,
              'info': logging.INFO,
              'warning': logging.WARNING,
              'error': logging.ERROR,
              'critical': logging.CRITICAL}
    log_args = {}
    log_format = cfg['Main'].get('LogFormat',
                                 "%(asctime)s %(name)s [%(levelname)s] %(message)s")

    if not opts.run_in_foreground:
        log_dir = cfg['Main'].get('LogDir', '/var/log/cchrc_data_collector')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_args['filename'] = os.path.join(log_dir, 'cdc.log')

    if opts.verbose != 0:
        log_level = max([logging.WARNING - 10 * opts.verbosity, logging.DEBUG])
    else:
        cfg_log_level = cfg['Main'].get('LogLevel', 'warning').lower()
        if cfg_log_level not in LEVELS:
            print "Invalid log level '%s' used in config files. Defaulting to 'warning'" % cfg_log_level
            cfg_log_level = 'warning'
        log_level = LEVELS[cfg_log_level]

    log_args['level'] = log_level
    log_args['format'] = log_format

    logging.basicConfig(**log_args)

    logger = logging.getLogger('cdc')

    return logger

class Mother(object):
    def __init__(self, start_callables, stop_callables):
        self.start_callables = start_callables
        self.stop_callables = stop_callables
        self.ended = False
        self.log = logging.getLogger('cdc.Mother')

    def start(self):
        for c in self.start_callables:
            self.log.debug("Starting '%s'", str(c.im_self))
            c()

    def stop(self, sig, stack_frame):
        for c in self.stop_callables:
            self.log.debug("Stopping '%s'", str(c.im_self))
            c()
            c.im_self.join()
        self.ended = True

def main():
    opts, args = get_opts()
    cfg = configobj.ConfigObj(args[0], file_error=True)

    log = configure_logging(cfg, opts)

    DF = cchrc.common.datafile.DataFile
    sc = cchrc.common.SensorContainer()
    dfr = cchrc.common.datafile.DataFileRunner()

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

    for data_file in cfg['Files']:
        fcfg = cfg['Files'][data_file]
        if opts.test:
            sampling_time = 60
        else:
            sampling_time = int(fcfg['SamplingTime'])
        log.debug("Configuring datafile '%s' with sampling time %s",
                  data_file, sampling_time)
        dfr.put(DF(data_file, fcfg['FileName'], cfg['Main']['BaseDirectory'],
                   fcfg['DefaultGroup'], sampling_time,
                   fcfg['DefaultMode'], listify(fcfg['Sensors']), sc))

    mom = Mother([sc.start_averaging_sensors, dfr.start_data_files],
                 [sc.stop_averaging_sensors, dfr.stop_data_files])

    log.debug("Starting Mother")

    # TODO: Handle case for logging/threading/closed files, etc.
    # File "/usr/lib/python2.6/logging/__init__.py", line 789, in emit
    # stream.write(fs % msg)
    # ValueError: I/O operation on closed file

    mom.start()

    signal.signal(signal.SIGTERM, mom.stop)
    signal.signal(signal.SIGINT, mom.stop)

    while True:
        # Putting a 'while True' loop here for "future expansion," such as
        # printing out system stats on a SIGUSR1 or some such
        log.debug("Waiting for signals")
        signal.pause()
        if mom.ended:
            log.debug("Mother ended. Shutting down")
            return

if __name__ == '__main__':
    main()
    logging.shutdown()
