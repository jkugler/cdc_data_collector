Introduction
============
This is the handbook for the CDC Data Collector.  It won't be as quite as formal
as an actual manual, thus the name "Handbook."

Home Page
=========
For now the home page lives at: https://github.com/jkugler/cdc_data_collector

Dependencies
============
CDC uses the following python modules:

configobj
---------
For reading configuration files, we use the configobj module from
voidspace.org.uk.

http://pypi.python.org/pypi/configobj/

daemon
------
We use the daemon module to make it simple (two or three lines of code) to
put the collector process into the background.

http://pypi.python.org/pypi/daemon/

futures
-------
The Python Futures module allows us to easily "spin off" collection
processes and immediately return to the controlling thread
(i.e. asynchronous execution)

http://pypi.python.org/pypi/futures/2.0

unittest2
---------
Python 2.7's unittest module has some excellent new feature added. This module
backports these features to version prior to 2.7

http://pypi.python.org/pypi/unittest2/0.5.1

Installation
============
See the INSTALL file in this directory.

Starting and Stopping
=====================
Due to the current design, CDC must be run as root. This is due to a
couple reasons.

- On some machines, the OneWire USB device an only be accessed by root.
- CDC writes its PID file to /var/run/, which requires root privileges.

Starting
--------
To start CDC, as root, simply run the command:

``cdc.py config_file.ini``

Stopping
--------
The easiest way to stop CDC is to run this command as root:

``kill `cat /var/run/cdc.pid```

Available Sensor Types
======================
Currently the only two sensor type are:

 - onewire
 - null

onewire
-------
This sensor is used for reading values off of a onewire bus.

Valid Parameters
++++++++++++++++
connection
  The connection string which defines the source of the onewire readings.  This is the same string you might
  pass to one of the onewire utilities as a command-line option, such as "u", "server:8100", or some such.
sa
  The attribute of the sensor to return upon a call to ``get_reading()``. This defaults to "temperature."
use_cache
  True or False. Use values from the onewire cache. See the onewire documentation for more on the cache. Defaults
  to False.

null
----
The null sensor is used for testing.

Valid Parameters
++++++++++++++++
value
  Defines the value this sensor will return when ``get_reading()`` is called.

Configuration File
==================

The structure of the configuration file is rather simple, but still expressive
when the need is there.

The configuration file is broken up into four sections:

Main
  Some general settings
SensorGroups
  The sensors that will be read for Data
Names
  Allows custom naming of sensors for their output
Files
  Defines the files that will record data collected.

General Format
--------------
Each of the four main sections begins with the group's name in brackets. Thus,
the Main section begins with `[Main]`.  The SensorGroups and Files sections also
defines subsections (and in the case of SensorGroups, a sub-subsections.  Each
further subsection adds a layer of brackets. As:

  [Section]
    [[SubSection]]
      [[[SubSubSection]]]

Main
----
The main section defines three values.

BaseDirectory
  The directory where the data files will be written.

LogDir
  Optional.  The directory where the log file will be written.  Defaults to
  `/var/log/cdc_data_collector`

LogLevel
  Optional.  The log level given to the logging system.  Defaults to warning.

SensorGroups
------------
The SensorGroups section contains no configuration values directly, but
instead contains one or more sub-sections which define the sensor groups.

The name of the first subsection is an arbitrary name, e.g. GroupOne, but must
be unique among the SensorGroups sub-sections.

Under the subsection, there is one value, and then a sub-subsection named "Sensors."

The value is called "SensorType" and is of the form:

  SensorType = sensor_module/option_one=value1;option_two=value2;option_N=valueN

The "sensor_module" is the name of the module which implements the class for the
type of sensor from which the framework is reading.

After the slash are values which are passed to the sensor class upon initialization of each sensor.  These values serve as defaults, and can be overridden on a per-sensor basis.

For example, a sensor group reading onewire temperature sensors could look like:

  SensorType = onewire/connection=u;sa=temperature

The type of sensor is "onewire", the "connection" is defined as "u" for USB, and "sa" defines
which sensor attribute is being read.

The "Sensors" sub-subsections defines the "friendly" names of the sensors, their IDs,
and any desired configuration values.  The format is:

  SensorName = SENSOR_ID/option_one=value1;option_two=value2;option_N=valueN

Any option names with the same name as in SensorType definition will be overridden.

The SensorName is arbitrary, but must be unique for the Sensor Group.  It is the
name you will use to define which sensors you want in which data files.

The SENSOR_ID is the ID used by the sensor type to find the sensor.

The options are passed to the sensor class upon initialization.

This is an example sensor group section:

| [SensorGroups]
|   [[BlackWire]]
|     SensorType = onewire/connection=u;sa=temperature
|     [[[Sensors]]]
|       T1 = BA000002A8730C28
|       T2 = 3A000002A8812228
|       T3 = D1000002A868C728
|       T4 = D1000002A8831528
|       T5 = D0000002A88D0E28
|       T6 = AD000002A87E9128
|       T7 = E6000002A86AF428
|       T8 = 0E000002A86A6728
|       T9 = 66000002A8686228

Names
-----
The "Names" section allows for the definition of a sensor's column name when it is recorded
in a data file.  It is of the format:

  SensorGroupName.SensorName = A Custom Column Name

An example, using the sensor group defined above:

  BlackWire.T1 = Black 5cm Soil Sensor

When the BlackWire T1 sensor's readings are recorded in a data file, it will be in a column
named "Black 5cm Soil Sensor."

Files
-----
The Files section defines the parameters for the data files.

Each subsection has a arbitrary, but unique, name.  The values of the subsection are:

FileName
  This is the name of the file to which the data values will be written. It will be opened
  in the BaseDirectory defined in the Main section.

DefaultGroup
  The SensorGroup from which the sensors will be sourced, if not qualified (see "Sensors"
  value below)

SamplingTime
  How often the file will record its values. This also (currently) affects the sampling for
  averaging sensors.  The averaging sensors pull data 12 times per this interval.  This value
  is in seconds.

DefaultMode
  The mode with which the sensor will be used, if not qualified (see "Sensors" value below
  for more).  Valid values are SAMPLE or AVERAGE.

Sensors
  The sensors which will be recorded in the data file.  It is a comma delimited list of the
  "friendly" names defined in the sensor groups.  Optionally, the sensor names can be qualified
  with sensor group names and mode names.  For example, given a DefaultGroup of "BlackWire,"
  and a default mode of SAMPLE:

  - T1
  - T1/SAMPLE
  - BlackWire.T1
  - BlackWire.T1/SAMPLE

  all refer to the same sensor and readings.  To instantiate an averaging sensor, you would use
  something of this form:

  - T1/AVERAGE

  A second example, given a default group of "BlackWire" and a default mode of "AVERAGE,":

  - T1
  - T1/AVERAGE
  - BlackWire.T1
  - BlackWire.T1/AVERAGE

  all refer to the same sensor and readings.

An example of a data file using the BlackWire sensor group above:

| [Files]
|   [[BlackWireFile]]
|     FileName = 15MinWestEdgeSensors.dat
|     DefaultGroup = BlackWire
|     SamplingTime = 900
|     DefaultMode = SAMPLE
|     Sensors = T1,T2,T3,T1/AVERAGE,T2/AVERAGE,T3/AVERAGE

Development
===========

There is not much developer documentation at this point.

For an example of a barebones sensor, see ``cchrc/sensors/null.py``. For an
example of a more complicated sensor, see ``cchrc/sensors/onewire.py``.
