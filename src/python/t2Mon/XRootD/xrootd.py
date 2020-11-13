#!/usr/bin/python
import os
import time
import datetime
from tempfile import NamedTemporaryFile
from t2Mon.common.Utilities import checkConfigForDB
from t2Mon.common.configReader import ConfigReader
from t2Mon.common.database.opentsdb import opentsdb
from t2Mon.common.logger import getLogger

COMMANDS = {"login": "grep 'XrootdXeq' %s | grep 'login as' | awk '{split($2, a, \":\"); print a[1] \" \" a[2] \" \" $10}'",
            "disc": "grep 'XrootdXeq' %s | grep ' disc ' | awk '{split($2, a, \":\"); print a[1] \" \" a[2] \" \" 0 \" \" $7}'",
            "failedConnXRootdHDFS": "tail -n 1000000 %s | grep 'Failed to connect to' | awk '{split($2, a, \":\"); split($9, b, \":\"); print a[1] \" \" a[2] \" \" substr(b[1],2)}'"}

XROOTD_FILES = ['/var/log/xrootd/xrootd.log',
                '/var/log/xrootd/2/xrootd.log',
                '/var/log/xrootd/3/xrootd.log',
                '/var/log/xrootd/4/xrootd.log',
                '/var/log/xrootd/clustered/xrootd.log',
                '/var/log/xrootd/xcache/xrootd.log']

XROOTD_FILES_LOCAL = ['/var/log/xrootd/clusteredtier2/xrootd.log']


CONNECTIONS = "netstat -tuplna | grep xrootd | grep tcp | grep %s | grep %s"
# TODO for future;
# Grep out Transfer stats and ip information. Also it shows the time for the transfer and also how many bytes were transferred.


def getConnections(inputIP, portN):
    count = 0
    fd = NamedTemporaryFile(delete=False)
    fd.close()
    os.system("%s &> %s" % (CONNECTIONS % (inputIP, portN), fd.name))
    with open(fd.name, 'r') as fd1:
        for _ in fd1.readlines():
            count += 1
    os.unlink(fd.name)
    return count


def parseXRootDFiles(startTime, dbBackend, xrootd_files, flag, logger):
    """ """
    startTime -= 180  # Lets do all 2 minutes ago. and this has to be re-checked after run.
    parsedate = datetime.datetime.fromtimestamp(startTime)
    findLine = "%02d %02d " % (parsedate.hour, parsedate.minute)
    out = {}
    for inType, command in COMMANDS.items():
        out[inType] = {}
        fd = NamedTemporaryFile(delete=False)
        fd.close()
        for fileName in xrootd_files:
            if os.path.isfile(fileName):
                logger.debug("Call %s &> %s" % (command % fileName, fd.name))
                os.system("%s &> %s" % (command % fileName, fd.name))
                with open(fd.name, 'r') as fd1:
                    for line in fd1.readlines():
                        if line.startswith(findLine):
                            splLine = line.split()
                            out[inType].setdefault(splLine[2], 0)
                            out[inType][splLine[2]] += 1
        os.unlink(fd.name)
    if out['login']:
        for item, value in out['login'].items():
            dbBackend.sendMetric('xrootd.status.logins', value, {'timestamp': startTime, 'statuskey': item, 'flag': flag})
    if out['disc']:
        for item, value in out['disc'].items():
            dbBackend.sendMetric('xrootd.status.discon', value, {'timestamp': startTime, 'statuskey': item, 'flag': flag})
    if out['failedConnXRootdHDFS']:
        for item, value in out['failedConnXRootdHDFS'].items():
            dbBackend.sendMetric('xrootd.status.failedHDFS', value, {'timestamp': startTime, 'statuskey': item, 'flag': flag})
    logger.debug("Out: %s" % out)


def main(startTime, config, dbBackend, logger):
    parseXRootDFiles(startTime, dbBackend, XROOTD_FILES, 'remote', logger)
    parseXRootDFiles(startTime, dbBackend, XROOTD_FILES_LOCAL, 'local', logger)

    if config.hasOption('main', 'my_public_ip'):
        connCount = getConnections(config.getOption('main', 'my_public_ip'), '1094')
        dbBackend.sendMetric('xrootd.status.connOutside', connCount, {'timestamp': startTime})
    if config.hasOption('main', 'my_private_ip'):
        connCount = getConnections(config.getOption('main', 'my_private_ip'), '1094')
        dbBackend.sendMetric('xrootd.status.connPrivate', connCount, {'timestamp': startTime})
    if config.hasOption('main', 'my_public_ipv6'):
        connCount = getConnections(config.getOption('main', 'my_public_ipv6'), '1094')
        dbBackend.sendMetric('xrootd.status.connOutsidev6', connCount, {'timestamp': startTime})
    # 1095 is used for local access.
    if config.hasOption('main', 'my_public_ip'):
        connCount = getConnections(config.getOption('main', 'my_public_ip'), '1095')
        dbBackend.sendMetric('xrootd.status.connlocalipv4', connCount, {'timestamp': startTime})
    if config.hasOption('main', 'my_private_ip'):
        connCount = getConnections(config.getOption('main', 'my_private_ip'), '1095')
        dbBackend.sendMetric('xrootd.status.connlocalprivate', connCount, {'timestamp': startTime})
    if config.hasOption('main', 'my_public_ipv6'):
        connCount = getConnections(config.getOption('main', 'my_public_ipv6'), '1095')
        dbBackend.sendMetric('xrootd.status.connlocalipv6', connCount, {'timestamp': startTime})

    return


def publishMetrics(dbBackend, startKey, cutFirst, allData, timestamp):
    for item in allData:
        if not item:
            continue
        tmpI = item.split()
        size = int(tmpI[0].strip())
        fullPath = tmpI[1].strip()[cutFirst:]
        dbBackend.sendMetric(startKey, size, {'timestamp': timestamp, 'statKey': fullPath})


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
    DAEMONNAME = 'namenode-mon'
    LOGGER = getLogger('/var/log/t2Mon/%s/' % DAEMONNAME)
    execute(LOGGER)
