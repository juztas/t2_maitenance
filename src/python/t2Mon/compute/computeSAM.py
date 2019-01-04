#!/usr/bin/python
""" """
import os
import time
import shutil
import datetime
import socket
import traceback
from t2Mon.common.Utilities import externalCommand
from t2Mon.common.configReader import ConfigReader
from t2Mon.common.Utilities import checkConfigForDB
from t2Mon.common.database.opentsdb import opentsdb

HOST = socket.gethostname()

def appendOSEnviron(config):
    now = datetime.datetime.now()
    newEnv = os.environ.copy()
    if config.hasOption('main', 'https_proxy'):
        newEnv['https_proxy'] = config.getOption('main', 'https_proxy')
    if config.hasOption('main', 'http_proxy'):
        newEnv['http_proxy'] = config.getOption('main', 'https_proxy')
    if config.hasOption('main', 'wn_home_dir'):
        newEnv['SAME_SENSOR_HOME'] = '%s/%s/%s/%s/%s/%s' % (config.getOption('main', 'wn_home_dir'), now.year, now.month, now.day, now.hour, now.minute)
    else:
        raise Exception("wn_home_dir must be set")
    if config.hasOption('main', 'x509_proxy'):
        newEnv['X509_USER_PROXY'] = config.getOption('main', 'x509_proxy')
    else:
        raise Exception("x509_proxy must be set")
    if config.hasOption('main', 'sam_tests'):
        newEnv['SAM_TEST_LOCATION'] = config.getOption('main', 'sam_tests')
    else:
        raise Exception("sam_tests location is not set. I will not know what to run")
    newEnv['SAME_ERROR'] = '1'
    newEnv['SAME_WARNING'] = '2'
    newEnv['SAME_OK'] = '3'
    newEnv['SAME_NODATA'] = '0'
    newEnv['SAME_UNKNOWN'] = '0'
    return newEnv

def execute():
    """Main Execution"""
    CURRENT_TIME = int(time.time())
    config = ConfigReader()
    dbInput = checkConfigForDB(config)
    dbBackend = opentsdb(dbInput)
    try:
        if config.hasSection('compute'):
            if config.hasOption('compute', 'checks'):
                newEnv = appendOSEnviron(config)
                allChecks = config.getOption('compute', 'checks').split(',')
                # Copy subtree
                shutil.copytree(newEnv['SAM_TEST_LOCATION'], newEnv['SAME_SENSOR_HOME'])
                # Execute all Checks, but before, we need to export few things
                # And send all metrics. after we done, close metrics sender.
                averageStatus = 0  # 3 means that everything is ok
                for check in allChecks:
                    print check
                    startTimer = int(time.time())
                    scriptLocation = "%s/%s" % (newEnv['SAME_SENSOR_HOME'], check)
                    key = check[:-3]  # Cut all not needed sh...
                    newProc, newProcReturn = externalCommand(scriptLocation, newEnv)
                    endTimer = int(time.time())
                    averageStatus += newProcReturn
                    if newProcReturn != 3:
                        with open('%s-logstdout' % scriptLocation, 'w') as fd:
                            fd.write(newProc[0])
                            fd.write('Process exited: %s' % newProcReturn)
                        with open('%s-logstderr' % scriptLocation, 'w') as fd:
                            fd.write(newProc[1])
                            fd.write('Process exited: %s' % newProcReturn)
                    # STDOUT newProc[0], STDERR newProc[1]
                    print check, newProcReturn
                    dbBackend.sendMetric('compute.status.%s' % key,
                                         newProcReturn, {'myhost': HOST, 'cmsCheck': key, 'timestamp': CURRENT_TIME})
                    dbBackend.sendMetric('compute.status.runtime.%s' % key,
                                         int(endTimer - startTimer), {'myhost': HOST, 'cmsCheck': key, 'timestamp': CURRENT_TIME})
                dbBackend.sendMetric('compute.status.overall',
                                     float(averageStatus/len(allChecks)), {'myhost': HOST, 'cmsCheck': 'overall', 'timestamp': CURRENT_TIME})
                dbBackend.stopWriter()
    except:
        print 'Total Failure', traceback.format_exc()
        dbBackend.sendMetric('compute.status.overall', -1, {'myhost': HOST, 'cmsCheck': 'overall', 'timestamp': CURRENT_TIME})
        dbBackend.stopWriter()

if __name__ == "__main__":
    execute()
