from t2Mon.common.configReader import ConfigReader
from t2Mon.common.Utilities import checkConfigForDB
from t2Mon.common.database.opentsdb import opentsdb
import time
import re
from subprocess import check_output, CalledProcessError

def execute():
    config = ConfigReader()
    dbInput = checkConfigForDB(config)
    dbBackend = opentsdb(dbInput)
    cmd = "xrdfs xrootd.t2.ucsd.edu:2040 locate /store/"
    # returns output as byte string
    returned_output = check_output(cmd.split())

    reghost = re.compile('\[::([0-9.]*)].*')
    CURRENT_TIME = int(time.time())
    for line in returned_output.decode("utf-8").split('\n'):
        regmatch = reghost.match(line)
        if regmatch:
            host = regmatch.group(1)
            newfile = "root://%s//store/user/jbalcas/18Jan2019_job0_outHist.root1" % regmatch.group(1)
            cmd = "timeout 60 xrdcp -f %s %s" % (newfile, "/dev/null")
            try:
                out = check_output(cmd.split())
                t = 0, out
            except CalledProcessError as e:
                t = e.returncode, e.message
            print t, host
            dbBackend.sendMetric('xrd.cache.status',
                                 t[0], {'myhost': host, 'timestamp': CURRENT_TIME})
    dbBackend.stopWriter()


if __name__ == "__main__":
    while True:
        sttime = int(time.time())
        execute()
        endtime = int(time.time())
        difftime = endtime - sttime
        diffsleep = 120 - difftime
        if diffsleep > 0:
            print 'Sleep %s ' % diffsleep 
            time.sleep(diffsleep)
