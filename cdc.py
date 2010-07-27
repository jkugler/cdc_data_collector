#!/usr/bin/python

import os
import sys

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

def get_opts():
    usage = 'usage: %prog [options] path-to-ini'
    parser = optparse.OptionParser(usage=usage)
    a = parser.add_option
    a('-t', '--test', action='store_true', dest='test',
      help='Run CDC in test mode. (Sampling every 15 seconds)')
    parser.set_defaults(test=False)

    return parser.parse_args()

def main():
    pass

if __name__ == '__main__':
    main()
