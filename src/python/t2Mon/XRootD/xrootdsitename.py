from t2Mon.common.configReader import ConfigReader
from t2Mon.common.Utilities import checkConfigForDB
from t2Mon.common.database.opentsdb import opentsdb
import time
import socket
import subprocess
import re
from subprocess import check_output, CalledProcessError

def getHosts(out, host):
    newout = []
    cmd = "xrdfs %s locate /store/mc" % host
    # returns output as byte string
    try:
        returned_output = check_output(cmd.split())
    except subprocess.CalledProcessError as er:
        print er
        return []

    reghost = re.compile('\[:?:?([0-9.a-zA-Z\:]*)].*')
    CURRENT_TIME = int(time.time())
    for line in returned_output.decode("utf-8").split('\n'):
        regmatch = reghost.match(line)
        if regmatch:
            host = regmatch.group(1)
            if host not in out:
               print host
               host1 = socket.gethostbyaddr(host)[0]
               newout.append(host1)
    return newout

def execute():
    outS = []
    hosts  = getHosts(outS, 'cmsxrootd.fnal.gov')
    for host in hosts:
        outS.append(host)
    for host in outS:
        print host
        hosts = getHosts(outS, host)
        print host
        for host1 in hosts:
            outS.append(host1)
        newoutS = outS
        cmd = "xrdfs %s query config sitename" % host
        try:
            out = check_output(cmd.split())
            t = 0, out
        except CalledProcessError as e:
            t = e.returncode, e.message
        print t, host

if __name__ == "__main__":
    execute()
