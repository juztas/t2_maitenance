#!/usr/bin/python
import os
import time
import re
import socket
from subprocess import check_output, CalledProcessError
from datetime import datetime, timedelta
from t2Mon.common.configReader import ConfigReader
from t2Mon.common.Utilities import checkConfigForDB
from t2Mon.common.database.opentsdb import opentsdb
from t2Mon.common.logger import getStreamLogger

CURRENT_TIME = int(time.time())


def preparefiles(currdate, logger):
    if not os.path.isfile('/tmp/xrd-cache-test'):
        _ = check_output("fallocate -l 16M /tmp/xrd-cache-test", shell=True)
    for i in range(0, 24):
        newdate = currdate + timedelta(hours=i)
        fullLfn = '/mnt/hadoop/store/temp/user/jbalcas.cachetest/%s-%s-%s-%s-cache-test' % (newdate.year, newdate.month,
                                                                                            newdate.day, newdate.hour)
        cmd = "cp /tmp/xrd-cache-test %s" % fullLfn
        logger.info('Call CMD: %s', cmd)
        if not os.path.isfile(fullLfn):
            _ = check_output(cmd, shell=True)


def main(currdate, redirector, dbBackend, logger):
    currLFN = '/store/temp/user/jbalcas.cachetest/%s-%s-%s-%s-cache-test' % (currdate.year, currdate.month,
                                                                             currdate.day, currdate.hour)
    cmd = "X509_USER_PROXY=/root/x509UserProxy timeout 30 xrdfs %s locate /store/" % redirector
    # returns output as byte string
    logger.info('Calling %s' % cmd)
    timeNow = int(time.time())
    retOutput = []
    try:
        retOutput = check_output(cmd, shell=True)
    except CalledProcessError as ex:
        exCode = ex.returncode
        logger.critical('Got Error: %s, Redirector: %s ' % (str(ex), redirector))
        dbBackend.sendMetric('xrd.cache.status',
                             exCode, {'myhost': 'REDIRECTOR_URGENT-%s' % redirector, 'timestamp': timeNow})
        return
    logger.info('Returned out from Redirector: %s' % retOutput)
    reghost = re.compile(r'\[::([0-9.]*)].*')
    reghostipv6 = re.compile(r'\[([0-9a-z.:]*)].*')
    timeNow = int(time.time())
    for line in retOutput.decode("utf-8").split('\n'):
        if not line:
            break
        host = 'localhost'
        regmatch = reghost.match(line)
        regmatchipv6 = reghostipv6.match(line)
        if regmatch:
            host = regmatch.group(1)
        elif regmatchipv6:
            print regmatchipv6.group(1)
            try:
                host = socket.gethostbyaddr(regmatchipv6.group(1))[0]
            except socket.herror:
                host = str(regmatchipv6.group(1))
        else:
            logger.critical('Failed to parse %s' % line)
            dbBackend.sendMetric('xrd.cache.status',
                                 exCode, {'myhost': 'FAILED-%s' % line.replace(' ' '-'), 'timestamp': timeNow})
            break
        newfile = "root://%s/%s" % (host, currLFN)
        cmd = "X509_USER_PROXY=/root/x509UserProxy timeout 60 xrdcp -f %s %s" % (newfile, "/dev/null")
        try:
            logger.info('Call command %s' % cmd)
            _ = check_output(cmd, shell=True)
            exCode = 0
            logger.info('Got Exit: %s, Host: %s ' % (exCode, host))
        except CalledProcessError as ex:
            exCode = ex.returncode
            logger.critical('Got Error: %s, Host: %s ' % (str(ex), host))
        dbBackend.sendMetric('xrd.cache.status',
                             exCode, {'myhost': host, 'timestamp': timeNow})


def execute(logger):
    config = ConfigReader()
    dbInput = checkConfigForDB(config)
    dbBackend = opentsdb(dbInput)
    redirector = ""
    if config.hasSection('xcache'):
        redirector = config.getOptions('xcache')['redirector']
    if not redirector:
        raise Exception('Redirector not set in configuration')
    startTime = int(time.time())
    logger.info('Running Main')
    currdate = datetime.now()
    preparefiles(currdate, logger)
    main(currdate, redirector, dbBackend, logger)
    dbBackend.stopWriter()  # Flush out everything what is left.
    endTime = int(time.time())
    totalRuntime = endTime - startTime
    logger.info('StartTime: %s, EndTime: %s, Runtime: %s' % (startTime, endTime, totalRuntime))


if __name__ == "__main__":
    DAEMONNAME = 'xcache-mon'
    LOGGER = getStreamLogger()
    execute(LOGGER)
