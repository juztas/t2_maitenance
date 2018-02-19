#!/usr/bin/python
""" """
import time
import socket
from t2Mon.common.Utilities import externalCommand
from t2Mon.common.configReader import ConfigReader
from t2Mon.common.database.opentsdb import opentsdb

CURRENT_TIME = int(time.time())
HOST = socket.gethostname()

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
            allChecks = config.getOption('compute', 'checks').split(',')
            print allChecks
            # Execute all Checks, but before, we need to export few things
            # And send all metrics. after we done, close metrics sender.
            for check in allChecks:
                key = check[:-3]  # Cut all not needed sh...
                value = 3
                dbBackend.sendMetric('compute.status.%s' % key, value, CURRENT_TIME, {'myhost': HOST, 'cmsCheck': key})

if __name__ == "__main__":
    execute()
