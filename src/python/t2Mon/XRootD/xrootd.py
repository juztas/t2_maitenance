import sys, time
import psutil
from t2Mon.daemon import Daemon
from t2Mon.common.Utilities import externalCommand
from t2Mon.common.Utilities import tryConvertToNumeric
from t2Mon.common.Utilities import run_pipe_cmd
from t2Mon.common.Utilities import getItemPos
from t2Mon.common.Utilities import getProcInfo

def get():
    """Get memory info from /proc/meminfo"""
    itemOut = {}
    tmpOut = run_pipe_cmd('ps auxf', 'grep xrootd')
    configFiles = []
    pids = []
    for item in tmpOut:
        if not item:
            continue
        for desc in item.split('\n'):
            if not desc:
                continue
            vals = [val for val in desc.split() if val]
            configPos = getItemPos('-c', vals)
            if configPos == -1:
                continue
            if vals[configPos + 1] not in configFiles:
                configFiles.append(vals[configPos+1])
                pids.append(vals[1])
    counter = -1
    for fileName in configFiles:
        counter += 1
        tmpOut = externalCommand('cat %s' % fileName)
        itemOut[pids[counter]] = getProcInfo(pids[counter])
        itemOut[pids[counter]]['Config'] = {}
        for item in tmpOut:
            for desc in item.split('\n'):
                if desc.startswith('#'):
                    continue
                if not desc:
                    continue
                vals = desc.split(' ', 1)
                if len(vals) == 1:
                    vals.append(True)
    return itemOut

class MyDaemon(Daemon):
    def run(self):
        while True:
            print get()
            time.sleep(100)

if __name__ == "__main__":
    print get()
