#!/usr/bin/python
import os
import time
import datetime
from tempfile import NamedTemporaryFile
from t2Mon.common.Utilities import checkConfigForDB
from t2Mon.common.configReader import ConfigReader
from t2Mon.common.database.opentsdb import opentsdb
from t2Mon.common.logger import getLogger

COMMANDS = {"exclude": "grep 'New connection from: 0.0.0.0' /var/log/gridftp-auth.log | awk '{split($5, a, \":\"); print a[1] \" \" a[2] \" \" $13 \" \" 0}'",
            "success": "grep 'ended with rc' /var/log/gridftp-auth.log | awk '{split($5, a, \":\"); print a[1] \" \" a[2] \" \" $15}'",
            "users": "grep 'successfully authorized.' /var/log/gridftp-auth.log | grep ':: User' | awk '{split($5, a, \":\"); print a[1] \" \" a[2] \" \" $9}'",
            "failedConnGriftpHDFS": "tail -n 10000 /var/log/gridftp-auth.log | grep 'Failed to connect to' | awk '{split($5, a, \":\"); split($17, b, \":\"); print a[1] \" \" a[2] \" \" substr(b[1],2)}'",
            "firstBadLink": "cat /var/log/gridftp-auth.log | grep 'Bad connect ack with firstBadLink' | awk '{split($5, a, \":\"); print a[1] \" \" a[2] \" \" 0 \" \" $16}'"}

CONNECTIONS = "netstat -tuplna | grep globus-g | grep tcp | grep %s"
UCSD_FALLBACK = "grep -E '169.228.13[0-3]' /var/log/gridftp-auth.log | grep 'Transfer stats' | grep '/store/temp/user' | awk '{split($5, a, \":\"); print a[1] \" \" a[2] \" \" 0}'"
CALTECH_TEMP = "grep -E '(192.84.88.*|198.32.4[3-4].*)' /var/log/gridftp-auth.log | grep 'Transfer stats' | grep '/store/temp/user' | awk '{split($5, a, \":\"); print a[1] \" \" a[2] \" \" 0}'"
# TODO for future;
# Grep out Transfer stats and ip information. Also it shows the time for the transfer and also how many bytes were transferred.


def getConnections(inputIP=None, call=None, filterIn=None):
    count = 0
    fd = NamedTemporaryFile(delete=False)
    fd.close()
    if inputIP:
        os.system("%s &> %s" % (call % inputIP, fd.name))
    else:
        os.system("%s &> %s" % (call, fd.name))
    with open(fd.name, 'r') as fd1:
        for line in fd1.readlines():
            if filterIn:
                if line.startswith(filterIn):
                    count += 1
            else:
                count += 1
    os.unlink(fd.name)
    return count


def main(startTime, config, dbBackend, logger):
    """ """
    startTime -= 180  # Lets do all 2 minutes ago. and this has to be re-checked after run.
    parsedate = datetime.datetime.fromtimestamp(startTime)
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
    logger.debug('Out %s' % out)
    if out['success'] and out['exclude']:
        out['success']['0'] -= out['exclude']['0']
    if out['success']:
        for item, value in out['success'].items():
            dbBackend.sendMetric('gridftp.status.transferStatus', value, {'timestamp': startTime, 'statuskey': item})
    if out['users']:
        for item, value in out['users'].items():
            dbBackend.sendMetric('gridftp.status.authorize', value, {'timestamp': startTime, 'statuskey': item})
    if out['failedConnGriftpHDFS']:
        for item, value in out['failedConnGriftpHDFS'].items():
            dbBackend.sendMetric('gridftp.status.failedConnGriftpHDFS', value, {'timestamp': startTime, 'statuskey': item})
    if out['firstBadLink']:
        for item, value in out['firstBadLink'].items():
            dbBackend.sendMetric('gridftp.status.firstBadLink', value, {'timestamp': startTime, 'statuskey': item})
    logger.debug('Out %s' % out)
    if config.hasOption('main', 'my_public_ip'):
        connCount = getConnections(config.getOption('main', 'my_public_ip'), CONNECTIONS)
        dbBackend.sendMetric('gridftp.status.connOutside', connCount, {'timestamp': startTime})
    if config.hasOption('main', 'my_private_ip'):
        connCount = getConnections(config.getOption('main', 'my_private_ip'), CONNECTIONS)
        dbBackend.sendMetric('gridftp.status.connPrivate', connCount, {'timestamp': startTime})
    if config.hasOption('main', 'my_public_ipv6'):
        connCount = getConnections(config.getOption('main', 'my_public_ipv6'), CONNECTIONS)
        dbBackend.sendMetric('gridftp.status.connOutsidev6', connCount, {'timestamp': startTime})
    connCount = getConnections(None, UCSD_FALLBACK, filterIn=findLine)
    dbBackend.sendMetric('gridftp.status.ucsdfallbacked', connCount, {'timestamp': startTime})
    connCount = getConnections(None, CALTECH_TEMP, filterIn=findLine)
    dbBackend.sendMetric('gridftp.status.caltechtemp', connCount, {'timestamp': startTime})
    return


def execute(logger):
    config = ConfigReader()
    dbInput = checkConfigForDB(config)
    dbBackend = opentsdb(dbInput)
    startTime = int(time.time())
    logger.info('Running Main')
    main(startTime, config, dbBackend, logger)
    dbBackend.stopWriter()  # Flush out everything what is left.
    endTime = int(time.time())
    totalRuntime = endTime - startTime
    logger.info('StartTime: %s, EndTime: %s, Runtime: %s' % (startTime, endTime, totalRuntime))

if __name__ == "__main__":
    DAEMONNAME = 'gridftp-mon'
    LOGGER = getLogger('/var/log/t2Mon/%s/' % DAEMONNAME)
    execute(LOGGER)
