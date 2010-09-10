import csv
import os
import datetime
import threading

import cchrc

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
        # InvalidSensorMode
        raise RuntimeError("Invalid mode '%s'" % mode)

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
        self.__data_files = {}
        threading.Thread.__init__(self)

    def run(self):
        while True:
            if self.__end_thread:
                return
            # Check for data files that need to be "collected"
            # and spin them off
            time.sleep(1)

    def start_data_files(self):
        self.start()

    def put(self, data_file_object):
        pass

    def __str__(self):
        return '<DataFileRunner: ' + ', '.join(sorted([str(x) for x in self.__data_files.keys()])) + '>'

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
                # TODO: MalformedConfigFile - ?
                raise RuntimeError("File '%s' is requesting non-existant sensor %s.%s" %
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
            # TODO: BaseDirDoesNotExist
            raise RuntimeError("Base Directory '%s' does not exist" % self.base_dir)

        if os.path.exists(full_path):
            test_header = csv.reader(open(full_path)).next()
            if self.header != test_header:
                _rotate_files(full_path)

        self.csv = csv.DictWriter(open(full_path, mode='a', buffering=0),
                                  self.header)
        self.csv.writer.writerow(self.header)

    def collect_data(self):
        data = dict([(s.display_name, s.get_reading())
                     for s in self.sensors])
        data['Timestamp'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.csv.writerow(data)
