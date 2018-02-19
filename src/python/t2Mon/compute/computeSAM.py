#!/usr/bin/python
""" """
import os
import time
import socket
from t2Mon.common.Utilities import externalCommand
from t2Mon.common.configReader import ConfigReader
from t2Mon.common.database.opentsdb import opentsdb

CURRENT_TIME = int(time.time())
HOST = socket.gethostname()

def appendOSEnviron():
    newEnv = os.environ.copy()
    newEnv['https_proxy'] = 'http://newman.ultralight.org:3128'
    newEnv['http_proxy'] = 'http://newman.ultralight.org:3128'
    newEnv['SAME_SENSOR_HOME'] = '/wntmp/nodeTest/$now/'  # TODO fix
    newEnv['X509_USER_PROXY'] = '/opt/dist/compute/test.proxy'
    newEnv['SAME_ERROR'] = '1'
    newEnv['SAME_WARNING'] = '2'
    newEnv['SAM_OK'] = '3'
    newEnv['SAME_NODATA'] = '0'
    newEnv['SAME_UNKNOWN'] = '0'
    return newEnv

def checkConfigForDB(config):
    if config.hasSection('opentsdb'):
        return config.getOptions('opentsdb')
    return {}

def execute():
    """Main Execution"""
    config = ConfigReader()
    dbInput = checkConfigForDB(config)
    dbBackend = opentsdb(dbInput)
    if config.hasSection('compute'):
        if config.hasOption('compute', 'checks'):
            newEnv = appendOSEnviron()
            allChecks = config.getOption('compute', 'checks').split(',')
            print allChecks
            # Execute all Checks, but before, we need to export few things
            # And send all metrics. after we done, close metrics sender.
            lowestReturn = 3 # 3 means that everything is ok
            for check in allChecks:
                key = check[:-3]  # Cut all not needed sh...
                value = 3
                newProc, newProcReturn = externalCommand('env', newEnv)
                # STDOUT newProc[0], STDERR newProc[1]
                dbBackend.sendMetric('compute.status.%s' % key,
                                     value, {'myhost': HOST, 'cmsCheck': key, 'timestamp': CURRENT_TIME})
            dbBackend.stopWriter()

if __name__ == "__main__":
    execute()
