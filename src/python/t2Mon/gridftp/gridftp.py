import sys, time
import psutil
from t2Mon.daemon import Daemon
from t2Mon.common.Utilities import externalCommand
from t2Mon.common.Utilities import tryConvertToNumeric
from t2Mon.common.Utilities import run_pipe_cmd
from t2Mon.common.Utilities import getItemPos
from t2Mon.common.Utilities import getProcInfo

IGNORE_USERS = ['root']

def get():
    """Get memory info from /proc/meminfo"""
    memInfo = {}
    tmpOut = externalCommand('cat /etc/gridftp.conf')
    for item in tmpOut:
        for desc in item.split('\n'):
            if desc.startswith('#'):
                continue
            if not desc:
                continue
            vals = desc.split(' ', 1)
            if len(vals) == 2:
                # We strip it to remove white spaces and split to remove kb in the end
                value = vals[1].strip().split(' ')
                name = vals[0].strip()
                if name.startswith('log_'):
                    continue
                if len(value) == 2:
                    name += "_%s" % value[1]
                memInfo[name] = tryConvertToNumeric(value[0])
            else:
                print 'MemInfo: Skipped this item: ', vals
    # Get current running statistics
    tmpOut = run_pipe_cmd('ps auxf', 'grep globus-gridftp-server')
    totalTransferCount = 0
    for item in tmpOut:
        if not item:
            continue
        for desc in item.split('\n'):
            if not desc:
                continue
            vals = [val for val in desc.split() if val]
            if vals[0] in IGNORE_USERS:
                continue
            totalTransferCount += 1
            if 'UserStats' not in memInfo.keys():
                memInfo['UserStats'] = {}
            if str(vals[0]) not in memInfo['UserStats'].keys():
                memInfo['UserStats'][str(vals[0])] = {}
                memInfo['UserStats'][str(vals[0])]['Active'] = 0
                memInfo['UserStats'][str(vals[0])]['procStats'] = []
            memInfo['UserStats'][str(vals[0])]['Active'] += 1
            memInfo['UserStats'][str(vals[0])]['procStats'].append(getProcInfo(vals[1]))
    memInfo['TotalActiveTransfers'] = totalTransferCount
    return memInfo

class MyDaemon(Daemon):
    def run(self):
        while True:
            print get()
            time.sleep(100)

if __name__ == "__main__":
    print get()
