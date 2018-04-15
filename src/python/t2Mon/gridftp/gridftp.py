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

COMMANDS = {"exclude": "grep 'New connection from: 0.0.0.0' /var/log/gridftp-auth.log | awk '{split($5, a, \":\"); print a[1] \" \" a[2] \" \" $13 \" \" 0}'",
            "success": "grep 'ended with rc' /var/log/gridftp-auth.log | awk '{split($5, a, \":\"); print a[1] \" \" a[2] \" \" $15}'",
            "users": "grep 'successfully authorized.' /var/log/gridftp-auth.log | grep ':: User' | awk '{split($5, a, \":\"); print a[1] \" \" a[2] \" \" $9}'"}

CONNECTIONS = "netstat -tuplna | grep globus-gridf | grep tcp | grep %s"
# TODO for future;
# Grep out Transfer stats and ip information. Also it shows the time for the transfer and also how many bytes were transferred.

def getConnections(inputIP):
    count = 0
    fd = NamedTemporaryFile(delete=False)
    fd.close()
    os.system("%s &> %s" % (CONNECTIONS % (inputIP, fd.name)))
    with open(fd.name, 'r') as fd1:
        for line in fd1.readlines():
            count += 1
    os.unlink(fd.name)
    return count


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
        os.system("%s &> %s" % (command, fd.name))
        with open(fd.name, 'r') as fd1:
            for line in fd1.readlines():
                if line.startswith(findLine):
                    splLine = line.split()
                    out[inType].setdefault(splLine[2], 0)
                    out[inType][splLine[2]] += 1
        os.unlink(fd.name)
    print out
    if out['success'] and out['exclude']:
        out['success']['0'] -= out['exclude']['0']
    if out['success']:
        for item, value in out['success'].items():
            dbBackend.sendMetric('gridftp.status.transferStatus', value, {'timestamp': startTime, 'statuskey': item})
    if out['users']:
        for item, value in out['users'].items():
            dbBackend.sendMetric('gridftp.status.authorize', value, {'timestamp': startTime, 'statuskey': item})
    print out
    if config.hasoption('main', 'my_public_ip'):
        connCount = getConnections(config.getoption('main', 'my_public_ip'))
        dbBackend.sendMetric('gridftp.status.connOutside', connCount, {'timestamp': startTime})
    if config.hasoption('main', 'my_private_ip'):
        connCount = getConnections(config.getoption('main', 'my_private_ip'))
        dbBackend.sendMetric('gridftp.status.connOutside', connCount, {'timestamp': startTime})
    return

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
