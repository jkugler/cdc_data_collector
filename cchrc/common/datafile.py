from cchrc.sensors import AveragingSensor

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

    return group, s, mode

class DataFile(object):
    def __init__(self, file_id, sc, out_file, cfg):
        """
        sensor_collection is a SensorCollection object
        out_file is
          - the path to the data file being written
          - OR a file-like object
        cfg is the config for the file (a dict from the config ini)
        """
        self.sensors = []

        # Get names of sensors and construct data file header row
        dg = cfg['DefaultGroup'].upper()
        dm = cfg['DefaultMode'].upper()
        st = cfg['Samplingtime']

        for s in cfg['Sensors']:
            group, name, mode = _split_sensor_info(s, dg, dm)
            # Sampling sensors should already be in the SC
            # An averaging sensor's sampling sensor should already be in the SC
            if not sc.contains(group, name):
                # TODO: MalformedConfigFile - ?
                raise RuntimeError("File '%s' is requesting non-existant sensor %s.%s" %
                                   (file_id, group, name))
            ########## Need to set names/friendly names
            if mode == 'SAMPLE':
                self.sensors.append(sc.get(group, name))
            elif mode == 'AVERAGE':
                if sc.contains(group, name, st):
                    self.sensors.append(sc.get(group, name, st))
                else:
                    new_sensor = AveragingSensor(sc.get(group, name), st)
                    sc.put(new_sensor, group, name, st)
                    self.sensors.append(new_sensor)
            else:
                # Should never get here
                raise("Invalid mode: '%s'" % mode)

        # Open out_path as CSV Dict
        # Check to make sure the header matches sensor names
        # If not, close file, rename using .0, .1, .2 etc
        #  The *higher* the number, the older the file
        #  Reopen file
        #

    def collect_data(self):
        pass
