import os
from t2Mon.common.configReader import ConfigReader
from t2Mon.common.Utilities import checkConfigForDB
from t2Mon.common.database.opentsdb import opentsdb
import time
import re
from subprocess import check_output, CalledProcessError
from datetime import datetime, timedelta

def preparefiles(currdate):
    out = check_output("fallocate -l 16M /tmp/xrd-cache-test", shell=True)
    for i in range(0,24):
        newdate = currdate + timedelta(hours=i)
        fullLfn = '/mnt/hadoop/store/temp/user/jbalcas.cachetest/%s-%s-%s-%s-cache-test' % (newdate.year, newdate.month, newdate.day, newdate.hour)
        cmd = "cp /tmp/xrd-cache-test %s" % fullLfn
        print cmd
        out = check_output(cmd, shell=True)


def execute(currdate):
    currLFN = '/store/temp/user/jbalcas.cachetest/%s-%s-%s-%s-cache-test' % (currdate.year, currdate.month, currdate.day, currdate.hour)
    config = ConfigReader()
    dbInput = checkConfigForDB(config)
    dbBackend = opentsdb(dbInput)
    cmd = "X509_USER_PROXY=/root/x509UserProxy timeout 30 xrdfs xrootd.t2.ucsd.edu:2040 locate /store/"
    # returns output as byte string
    print 'Calling %s' % cmd
    try:
        returned_output = check_output(cmd, shell=True)
    except CalledProcessError as e:
        t = e.returncode
        print t, 'xrootd.t2.ucsd.edu'
        dbBackend.sendMetric('xrd.cache.status',
                             t, {'myhost': 'REDIRECTOR_URGENT-xrootd.t2.ucsd.edu', 'timestamp': CURRENT_TIME})
        returned_output = []
    print returned_output
    reghost = re.compile('\[::([0-9.]*)].*')
    CURRENT_TIME = int(time.time())
    for line in returned_output.decode("utf-8").split('\n'):
        regmatch = reghost.match(line)
        if regmatch:
            host = regmatch.group(1)
            print host
            newfile = "root://%s/%s" % (regmatch.group(1), currLFN)
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
    currhour = None
    while True:
        currdate = datetime.now()
        newhour = currdate.hour
        if newhour != currhour:
            preparefiles(currdate)
            currhour = newhour
        exit
        sttime = int(time.time())
        execute(currdate)
        endtime = int(time.time())
        difftime = endtime - sttime
        diffsleep = 120 - difftime
        if diffsleep > 0:
            print 'Sleep %s ' % diffsleep 
            time.sleep(diffsleep)
