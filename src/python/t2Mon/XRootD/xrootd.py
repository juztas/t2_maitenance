#!/usr/bin/python
import os
import time
import hashlib
import datetime
import shlex
from tempfile import NamedTemporaryFile
from t2Mon.common.Utilities import checkConfigForDB
from t2Mon.common.configReader import ConfigReader
from t2Mon.common.database.opentsdb import opentsdb
from t2Mon.common.logger import getStreamLogger

COMMANDS = {"login": "grep -E '(XrootdXeq|XrootdBridge)' %s | grep 'login as' | awk '{split($2, a, \":\"); print a[1] \" \" a[2] \" \" $10}'",
            "disc": "grep -E '(XrootdXeq|XrootdBridge)' %s | grep ' disc ' | awk '{split($2, a, \":\"); print a[1] \" \" a[2] \" \" 0 \" \" $7}'",
            "finishedTransfers": "cat %s | grep 'TPC_PullRequest'",
            "finishedTransfers1": "cat %s | grep 'TPC_PushRequest'"}

XROOTD_FILES = ['/var/log/xrootd/xrootd.log',
                '/var/log/xrootd/2/xrootd.log',
                '/var/log/xrootd/3/xrootd.log',
                '/var/log/xrootd/4/xrootd.log',
                '/var/log/xrootd/clustered/xrootd.log',
                '/var/log/xrootd/xcache/xrootd.log',
                '/var/log/xrootd/stageout/xrootd.log']


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

def netlogger(inLine, flag):
    inLine = inLine.strip().split(';')
    errMsg = ""
    if len(inLine) > 1:
        errMsg = " ".join(inLine[1:])
    print((inLine, flag))
    ntLogLine = inLine[0].split('%s:' % flag)[1].replace(" ", "")
    lexLine = shlex.shlex(ntLogLine, posix=True)
    lexLine.whitespace_split = True
    lexLine.whitespace = ','
    mappedDict = dict(pair.split('=', 1) for pair in lexLine)
    outDict = {'tmode': flag}
    if errMsg:
        hashObject = hashlib.md5(errMsg.encode())
        mdHash = hashObject.hexdigest()
        outDict['errHash'] = mdHash
    for key in ['user', 'tpc_status', 'event', 'errHash']:
        if key in list(mappedDict.keys()):
            outDict[key] = mappedDict[key]
    return outDict
    
    #print inLine, out

def parseXRootDFiles(startTime, dbBackend, xrootd_files, flag, logger, config):
    """ """
    startTime -= 180  # Lets do all 2 minutes ago. and this has to be re-checked after run.
    parsedate = datetime.datetime.fromtimestamp(startTime)
    findLine = "%02d %02d " % (parsedate.hour, parsedate.minute)
    #findLineTPC = "%02d%02d%02d %02d:%02d" % (parsedate.year-2000, parsedate.month, parsedate.day, parsedate.hour, parsedate.minute)
    findLineTPC = "%02d%02d%02d" % (parsedate.year-2000, parsedate.month, parsedate.day)
    out = {}
    for inType, command in list(COMMANDS.items()):
        out[inType] = {}
        if inType in ['finishedTransfers', 'finishedTransfers1']:
            out[inType] = []
        fd = NamedTemporaryFile(delete=False)
        fd.close()
        for fileName in xrootd_files:
            if os.path.isfile(fileName):
                logger.debug("Call %s &> %s" % (command % fileName, fd.name))
                os.system("%s &> %s" % (command % fileName, fd.name))
                with open(fd.name, 'r') as fd1:
                    for line in fd1.readlines():
                        if inType == 'finishedTransfers' and line.startswith(findLineTPC):
                            out[inType].append(netlogger(line, 'TPC_PullRequest'))
                        if inType == 'finishedTransfers1' and line.startswith(findLineTPC):
                            out[inType].append(netlogger(line, 'TPC_PushRequest'))
                        elif line.startswith(findLine):
                            splLine = line.split()
                            out[inType].setdefault(splLine[2], 0)
                            out[inType][splLine[2]] += 1
        os.unlink(fd.name)
    if out['login']:
        for item, value in list(out['login'].items()):
            dbBackend.sendMetric('xrootd.status.logins', value, {'timestamp': startTime, 'statuskey': item, 'flag': flag, 'xrootd_type': config.getOption('main', 'xrootd_type')})
    if out['disc']:
        for item, value in list(out['disc'].items()):
            dbBackend.sendMetric('xrootd.status.discon', value, {'timestamp': startTime, 'statuskey': item, 'flag': flag, 'xrootd_type': config.getOption('main', 'xrootd_type')})
    if out['finishedTransfers']:
        for item in out['finishedTransfers']:
            exitCode = item['tpc_status'] if 'tpc_status' in item else 0
            item['timestamp'] = startTime
            item['xrootd_type'] = config.getOption('main', 'xrootd_type')
            dbBackend.sendMetric('xrootd.status.tpc', exitCode, item)
    if out['finishedTransfers1']:
        for item in out['finishedTransfers1']:
            exitCode = item['tpc_status'] if 'tpc_status' in item else 0
            item['timestamp'] = startTime
            item['xrootd_type'] = config.getOption('main', 'xrootd_type')
            dbBackend.sendMetric('xrootd.status.tpc', exitCode, item)
    logger.debug("Out: %s" % out)


def main(startTime, config, dbBackend, logger):
    parseXRootDFiles(startTime, dbBackend, XROOTD_FILES, 'remote', logger, config)

    if config.hasOption('main', 'my_public_ip'):
        connCount = getConnections(config.getOption('main', 'my_public_ip'), config.getOption('main', 'xrootd_port'))
        dbBackend.sendMetric('xrootd.status.connOutside', connCount, {'timestamp': startTime, 'xrootd_type': config.getOption('main', 'xrootd_type')})
    if config.hasOption('main', 'my_public_ipv6'):
        connCount = getConnections(config.getOption('main', 'my_public_ipv6'), config.getOption('main', 'xrootd_port'))
        dbBackend.sendMetric('xrootd.status.connOutsidev6', connCount, {'timestamp': startTime, 'xrootd_type': config.getOption('main', 'xrootd_type')})
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
    DAEMONNAME = 'namenode-mon'
    LOGGER = getStreamLogger()
    while True:
        execute(LOGGER)
        time.sleep(60)
