#!/usr/bin/python

from collections import defaultdict
import logging
import optparse
import os
import signal
import sys
import time

import configobj
import daemon

import cchrc

class InvalidLoggingDestination(Exception):
    pass

def get_opts():
    usage = 'usage: %prog [options] path-to-ini'
    parser = optparse.OptionParser(usage=usage)
    a = parser.add_option
    a('-r', '--run-in-forground', action='store_true', dest='run_in_foreground',
      help=("Stay in the foreground and log to the console. "
            "(Will still log to file as well). Exit via Ctrl-C"))
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


    log_dir = cfg['Main'].get('LogDir', '/var/log/cdc_data_collector')
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError, ex:
            raise InvalidLoggingDestination(str(ex))
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

    if opts.run_in_foreground:
        console_logger = logging.StreamHandler()
        console_logger.setLevel(log_level)
        console_logger.setFormatter(logging.Formatter(log_format))
        logging.getLogger('').addHandler(console_logger)

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

def go(cfg, opts, log):

    if os.path.exists('/var/run/cdc.pid'):
        log.error('Will not start: existing process\n '
                  'If a previous CDC instance crashed, delete /var/run/cdc.pid before running.')
        return

    open('/var/run/cdc.pid', mode='w').write(str(os.getpid()))

    sc = cchrc.common.construct_sensor_collection(cfg)
    dfr = cchrc.common.construct_data_file_runner(cfg, opts.test, sc)

    mom = Mother([sc.start_averaging_sensors, dfr.start_data_files],
                 [sc.stop_averaging_sensors, dfr.stop_data_files])

    log.debug("Starting Mother")

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
            os.unlink('/var/run/cdc.pid')
            return

def main():
    opts, args = get_opts()
    cfg = configobj.ConfigObj(args[0], file_error=True)

    try:
        log = configure_logging(cfg, opts)
    except InvalidLoggingDestination, ex:
        print "Could not initialize logging:", str(ex)
        print "Exiting"
        sys.exit(1)

    if opts.run_in_foreground:
        go(cfg, opts, log)
    else:
        # Keep the log file open when converting to a daemon
        with daemon.DaemonContext(files_preserve=[log.root.handlers[0].stream]):
            go(cfg, opts, log)

if __name__ == '__main__':
    main()
    logging.shutdown()
