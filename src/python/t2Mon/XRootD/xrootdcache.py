import os
import sys
import socket
from t2Mon.common.configReader import ConfigReader
from t2Mon.common.Utilities import checkConfigForDB
from t2Mon.common.database.opentsdb import opentsdb
import time
import re
from subprocess import check_output, CalledProcessError
from datetime import datetime, timedelta
import logging

logger = logging.getLogger('dev')
logger.setLevel(logging.INFO)

consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.INFO)

logger.addHandler(consoleHandler)

formatter = logging.Formatter('%(asctime)s  %(name)s  %(levelname)s: %(message)s')
consoleHandler.setFormatter(formatter)

CURRENT_TIME = int(time.time())

def preparefiles(currdate):
    out = check_output("fallocate -l 16M /tmp/xrd-cache-test", shell=True)
    for i in range(0,24):
        newdate = currdate + timedelta(hours=i)
        fullLfn = '/mnt/hadoop/store/temp/user/jbalcas.cachetest/%s-%s-%s-%s-cache-test' % (newdate.year, newdate.month, newdate.day, newdate.hour)
        cmd = "cp /tmp/xrd-cache-test %s" % fullLfn
        logger.info('Call CMD: %s', cmd)
        out = check_output(cmd, shell=True)


def execute(currdate, redirector):
    currLFN = '/store/temp/user/jbalcas.cachetest/%s-%s-%s-%s-cache-test' % (currdate.year, currdate.month, currdate.day, currdate.hour)
    config = ConfigReader()
    dbInput = checkConfigForDB(config)
    dbBackend = opentsdb(dbInput)
    cmd = "X509_USER_PROXY=/root/x509UserProxy timeout 30 xrdfs %s locate /store/" % redirector
    # returns output as byte string
    print 'Calling %s' % cmd
    CURRENT_TIME = int(time.time())
    try:
        returned_output = check_output(cmd, shell=True)
    except CalledProcessError as e:
        t = e.returncode
        print t, 'xrootd.t2.ucsd.edu'
        dbBackend.sendMetric('xrd.cache.status',
                             t, {'myhost': 'REDIRECTOR_URGENT-xrootd.t2.ucsd.edu', 'timestamp': CURRENT_TIME})
        return
    print returned_output
    reghost = re.compile('\[::([0-9.]*)].*')
    reghostipv6 = re.compile('\[([0-9a-z.:]*)].*')
    CURRENT_TIME = int(time.time())
    for line in returned_output.decode("utf-8").split('\n'):
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
            print 'FAILED PARSE'
            break
        print host
        newfile = "root://%s/%s" % (host, currLFN)
        cmd = "X509_USER_PROXY=/root/x509UserProxy timeout 60 xrdcp -f %s %s" % (newfile, "/dev/null")
        try:
            print cmd
            out = check_output(cmd, shell=True)
            t = 0
        except CalledProcessError as e:
            t = e.returncode
        print t, host
        dbBackend.sendMetric('xrd.cache.status',
                             t, {'myhost': host, 'timestamp': CURRENT_TIME})
            
    dbBackend.stopWriter()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print 'Please provide redirector host:port as argument'
        exit(1)
    currhour = None
    while True:
        currdate = datetime.now()
        newhour = currdate.hour
        if newhour != currhour:
            preparefiles(currdate)
            currhour = newhour
        exit
        sttime = int(time.time())
        execute(currdate, sys.argv[1])
        endtime = int(time.time())
        difftime = endtime - sttime
        diffsleep = 120 - difftime
        if diffsleep > 0:
            print 'Sleep %s ' % diffsleep 
            time.sleep(diffsleep)
