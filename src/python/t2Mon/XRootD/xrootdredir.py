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
    CURRENT_TIME = int(time.time())
    sites = []
    with open('sites', 'r') as fd:
        sites = fd.readlines()
    for host in sites:
        host = host.strip()
        newfile = "root://cmsxrootd.fnal.gov//store/test/xrootd/%s/store/mc/SAM/GenericTTbar/AODSIM/CMSSW_9_2_6_91X_mcRun1_realistic_v2-v1/00000/A64CCCF2-5C76-E711-B359-0CC47A78A3F8.root" % host
        cmd = "timeout 180 xrdcp -f %s %s" % (newfile, "/dev/null")
        print cmd
        try:
            out = check_output(cmd.split())
            t = 0, out
        except CalledProcessError as e:
            t = e.returncode, e.message
        print t, host
        dbBackend.sendMetric('xrd.redir.status',
                             t[0], {'myhost': host, 'timestamp': CURRENT_TIME})
    dbBackend.stopWriter()


if __name__ == "__main__":
    while True:
        sttime = int(time.time())
        CURRENT_TIME = int(time.time())
        execute()
        endtime = int(time.time())
        difftime = endtime - sttime
        diffsleep = 3600 - difftime
        if diffsleep > 0:
            print 'Sleep %s ' % diffsleep 
            time.sleep(diffsleep)
