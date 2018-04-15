#!/usr/bin/python
import os
import json
import subprocess
import time
import datetime
from tempfile import NamedTemporaryFile
from t2Mon.common.Utilities import externalCommand
from t2Mon.common.Utilities import checkConfigForDB
from t2Mon.common.configReader import ConfigReader
from t2Mon.common.database.opentsdb import opentsdb

COMMANDS = {"login": "grep 'XrootdXeq' %s | grep 'login as' | awk '{split($2, a, \":\"); print a[1] \" \" a[2] \" \" $10}'",
            "disc": "grep 'XrootdXeq' %s | grep ' disc ' | awk '{split($2, a, \":\"); print a[1] \" \" a[2] \" \" 0 \" \" $7}'", # Later we need to group timing
            } # Later we need to group timing

XROOTD_FILES = ['/var/log/xrootd/xrootd.log',
                '/var/log/xrootd/2/xrootd.log',
                '/var/log/xrootd/3/xrootd.log',
                '/var/log/xrootd/4/xrootd.log',
                '/var/log/xrootd/clustered/xrootd.log']


def main(startTime, config, dbBackend):
    """ """
    startTime -= 180 # Lets do all 2 minutes ago. and this has to be re-checked after run.
    parsedate = datetime.datetime.fromtimestamp(startTime)
    print parsedate.hour, parsedate.minute
    findLine = "%02d %02d " % (parsedate.hour, parsedate.minute)
    out = {}
    for inType, command in COMMANDS.items():
        out[inType] = {}
        fd = NamedTemporaryFile(delete=False)
        fd.close()
        for fileName in XROOTD_FILES:
            print fileName
            if os.path.isfile(fileName):
                print "%s &> %s" % (command % fileName, fd.name)
                os.system("%s &> %s" % (command % fileName, fd.name))
                with open(fd.name, 'r') as fd1:
                    for line in fd1.readlines():
                        if line.startswith(findLine):
                            splLine = line.split()
                            out[inType].setdefault(splLine[2], 0)
                            out[inType][splLine[2]] += 1

    for item, value in out['login'].items():
        dbBackend.sendMetric('xrootd.status.logins', value, {'timestamp': startTime, 'statuskey': item})
    for item, value in out['disc'].items():
        dbBackend.sendMetric('xrootd.status.discon', value, {'timestamp': startTime, 'statuskey': item})
    print out
    return

def publishMetrics(dbBackend, startKey, cutFirst, allData, timestamp):
    for item in allData:
        if not item:
            continue
        tmpI = item.split()
        size = int(tmpI[0].strip())
        fullPath = tmpI[1].strip()[cutFirst:]
        dbBackend.sendMetric(startKey, size, {'timestamp': timestamp, 'statKey': fullPath})

def execute():
    config = ConfigReader()
    dbInput = checkConfigForDB(config)
    dbBackend = opentsdb(dbInput)
    startTime = int(time.time())
    print 'Running Main'
    main(startTime, config, dbBackend)
    dbBackend.stopWriter()  # Flush out everything what is left.
    endTime = int(time.time())
    totalRuntime = endTime - startTime
    print 'StartTime: %s, EndTime: %s, Runtime: %s' % (startTime, endTime, totalRuntime)

if __name__ == "__main__":
    execute()