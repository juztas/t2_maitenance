#!/usr/bin/python
""" """
import os
import time
import shutil
import datetime
import socket
from tempfile import NamedTemporaryFile
from t2Mon.common.Utilities import externalCommand
from t2Mon.common.configReader import ConfigReader
from t2Mon.common.Utilities import checkConfigForDB
from t2Mon.common.database.opentsdb import opentsdb

HOST = socket.gethostname()

COMMANDS = {"failingHDD": "tail -n 10000 /var/log/messages | grep 'Currently unreadable (pending) sectors' | awk '{split($3, a, \":\"); print a[1] \" \" a[2] \" \" 1}'",
            "failingPS1": "grep 'Power Supply sensor PS1 Status Failure detected' /var/log/messages | awk '{split($3, a, \":\"); print a[1] \" \" a[2] }'",
            "failingPS2": "grep 'Power Supply sensor PS2 Status Failure detected' /var/log/messages | awk '{split($3, a, \":\"); print a[1] \" \" a[2] }'",
            "failsshinvalid": "tail -n 10000 /var/log/secure | grep 'Failed password for' | awk '{testV=$9$10; split($3, a, \":\"); if (testV == \"invaliduser\") print  a[1] \" \" a[2] \" \" $13}'",
            "failsshroot": "tail -n 10000 /var/log/secure | grep 'Failed password for root' | awk '{split($3, a, \":\"); print a[1] \" \" a[2] \" \" $11}'",
            "failsshtotal": "tail -n 10000 /var/log/secure | grep 'Failed password for' | awk '{testV=$9$10; split($3, a, \":\"); if (testV == \"invaliduser\") print  a[1] \" \" a[2] \" \" $13; else print a[1] \" \" a[2] \" \" $11}'"}

def main(startTime, config, dbBackend):
    """Execute check"""
    startTime -= 60 # Lets do all 1 minutes ago. and this has to be re-checked after run.
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
    for dKey, dItems in out.items():
        for item, value in dItems.items():
            dbBackend.sendMetric('nodestatus.error.%s' % dKey, value, {'timestamp': startTime,
                                                                       'statuskey': item,
                                                                       'myhost': HOST,})


def execute():
    """Main Execution"""
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