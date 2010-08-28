# Gleaned from http://code.activestate.com/recipes/66531/

import configobj

class Config(object):
    """
    Implements a singlton/borg/hivemind/pick_your_name configuration
    object.  The main process will instantiate this with a file name
    and then instatiations by other modules or classes will always get
    the same configuration data without having to provide a path.
    """
    __shared_state = {}
    def __init__(self, config_file=None, test_mode=False):
        # 'test_mode' indicates you are testing reading all the configured sensors
        # Not to be confused with running the test suite
        self.__dict__ = self.__shared_state

        if config_file:
            if hasattr(self,'_Config__cfg'):
                # TODO: ConfigurationAlreadyInitialized
                raise RuntimeError("Configuration Already Initialized")
            else:
                self.__cfg = configobj.ConfigObj(config_file, file_error=True,
                                                 list_values=True)
                if test_mode:
                    for data_file in self.__cfg['Files']:
                        cfg['Files'][data_file]['SamplingTime'] = 60
        elif not hasattr(self,'_Config__cfg'):
            # TODO: ConfigurationNotInitialized
            raise RuntimeError("Configuration not initialized")

    def __getitem__(self, name):
        """
        Enables the object to behave as the ConfigObj object does
        """
        try:
            return self.__cfg[name]
        except KeyError, ex:
            if ex.args[0] == name:
                raise KeyError("No such section: '%s'" % name)
            else:
                raise

    def get(self, name, default=None):
        try:
            return self.__cfg[name]
        except KeyError:
            return default

    def __contains__(self, name):
        return name in self.__cfg
