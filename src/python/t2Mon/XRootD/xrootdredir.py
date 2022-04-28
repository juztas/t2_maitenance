import os
from t2Mon.common.configReader import ConfigReader
from t2Mon.common.Utilities import checkConfigForDB
from t2Mon.common.database.opentsdb import opentsdb
import time
import re
from subprocess import Popen, STDOUT, CalledProcessError, PIPE

def writelog(subp, outf):
    with open(outf, 'w') as fd:
        for line in subp.split('\n'):
            line = line.rstrip()
            fd.write("%s\n" % line)
            print line

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
        outfile = 'output/%s-%s' % (host, CURRENT_TIME)
        cmd = "timeout 300 xrdcp --debug 3 -f %s %s" % (newfile, "/dev/null")
        print cmd
        streamdata = ""
        try:
            out = Popen(cmd.split(), stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
            streamdata = out.communicate()[0]
            rc = out.returncode
            t = rc, streamdata
        except CalledProcessError as e:
            t = e.returncode, e.message
        if int(t[0] != 0):
            writelog(streamdata, outfile)
        print(host)
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
        diffsleep = 1800 - difftime
        if diffsleep > 0:
            print 'Sleep %s ' % diffsleep 
            time.sleep(diffsleep)
