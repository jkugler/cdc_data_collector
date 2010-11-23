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

    sc = cchrc.common.construct_sensor_collection(cfg)
    dfr = cchrc.common.construct_data_file_runner(cfg, opts.test, sc)

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
