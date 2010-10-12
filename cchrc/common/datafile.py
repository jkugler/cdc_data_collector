from collections import defaultdict
import csv
import datetime
import os
import threading
import time

import cchrc
from cchrc.common.exceptions import (InvalidSensorMode, InvalidObject,
                                     DuplicateObject, BaseDirDoesNotExist,
                                     MalformedConfigFile)

VALID_MODES = ('SAMPLE', 'AVERAGE')

def _split_sensor_info(s, default_group, default_mode):
    """Takes the sensor string from the ini, derive the group
    mode from it
    """
    if '.' in s:
        group, s = s.split('.', 1)
    else:
        group = default_group

    if '/' in s:
        s, mode = s.split('/')
    else:
        mode = default_mode

    if mode not in VALID_MODES:
        raise InvalidSensorMode("Invalid mode '%s' in sensor '%s'" % (mode, s))

    return group, s, mode.upper()

def _rotate_files(full_path):
    count = 1

    # First we find out how many data files there are
    while True:
        test_path = full_path + '.' + str(count)
        if not os.path.exists(test_path):
            break
        count += 1

    # Then we do the renaming
    while count > 0:
        new_path = full_path + '.' + str(count)
        count -= 1
        if count == 0:
            old_path = full_path
        else:
            old_path = full_path + '.' + str(count)

        os.rename(old_path, new_path)

class DataFileRunner(threading.Thread):
    def __init__(self):
        self.__end_thread = False
        self.__data_files = defaultdict(list)
        threading.Thread.__init__(self)

    def run(self):
        while True:
            if self.__end_thread:
                return # pragma: no cover
            cur_time = int(time.time())
            for rt in self.__data_files:
                if cur_time % rt == 0:
                    # TODO: Make this use futures
                    for df in self.__data_files[rt]:
                        df.collect_data(cur_time)
            time.sleep(1)

    def start_data_files(self):
        self.start()

    def stop_data_files(self):
        self.__end_thread = True

    def put(self, df_object):
        if not isinstance(df_object, DataFile):
            raise InvalidObject("'%s' is not a DataFile object" % str(df_object))
        if df_object in self.__data_files[df_object.sampling_time]:
            raise DuplicateObject("DataFile '%s' is already in the DataFileRunner"
                               % os.path.join(df_object.base_dir, df_object.file_name))
        self.__data_files[df_object.sampling_time].append(df_object)

class DataFile(object):
    def __init__(self, file_id, file_name, base_dir, default_group, sampling_time,
                 default_mode, sensor_list, sensor_collection):
        """
        file_id is the name of the file's section in the config file
        base_dir is the path to which the file will be written
        default_group is the default group of the sensors
        sampling_time is the sampling time of the file
        default_mode is the default mode of the sensors
        sensor_list is a list of sensor names to be pulled from the SensorCollection
        sensor_collection is a SensorCollection object
        """
        self.file_id = file_id
        self.file_name = file_name
        self.base_dir = base_dir
        self.sampling_time = sampling_time
        self.sensors = []
        AS = cchrc.sensors.AveragingSensor

        # Get names of sensors and construct data file header row
        dg = default_group
        dm = default_mode.upper()

        for s in sensor_list:
            group, name, mode = _split_sensor_info(s, dg, dm)
            # Sampling sensors should already be in the SC
            # An averaging sensor's sampling sensor should already be in the SC
            if not sensor_collection.contains(group, name):
                raise MalformedConfigFile("File '%s' is requesting non-existant sensor %s.%s" %
                                   (file_id, group, name))

            if mode == 'SAMPLE':
                self.sensors.append(sensor_collection.get(group, name))
            elif mode == 'AVERAGE':
                if sensor_collection.contains(group, name, sampling_time):
                    self.sensors.append(sensor_collection.get(group, name,
                                                              sampling_time))
                else:
                    new_sensor = AS(sensor_collection.get(group, name))
                    sensor_collection.put(new_sensor, group, sampling_time)
                    self.sensors.append(new_sensor)

        self.header = ['Timestamp'] + [s.display_name for s in self.sensors]

        self.open_file()

    def open_file(self):
        full_path = os.path.join(self.base_dir, self.file_name)
        if not os.path.exists(self.base_dir):
            raise BaseDirDoesNotExist("Base Directory '%s' does not exist" % self.base_dir)

        if os.path.exists(full_path):
            test_header = csv.reader(open(full_path)).next()
            if self.header != test_header:
                _rotate_files(full_path)

        # TODO: Don't write header if it already exists
        # AND TEST THAT IT DOESN'T
        self.csv = csv.DictWriter(open(full_path, mode='a', buffering=0),
                                  self.header)
        self.csv.writer.writerow(self.header)

    def collect_data(self, ts=None):
        data = dict([(s.display_name, s.get_reading())
                     for s in self.sensors])
        if ts:
            cur_time = datetime.datetime.fromtimestamp(ts)
        else:
            cur_time = datetime.datetime.now()
        data['Timestamp'] = cur_time.strftime('%Y-%m-%d %H:%M:%S')
        self.csv.writerow(data)
