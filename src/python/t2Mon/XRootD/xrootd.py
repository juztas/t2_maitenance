import sys
import time
from t2Mon.common.Utilities import checkConfigForDB
from t2Mon.common.configReader import ConfigReader
from t2Mon.common.database.opentsdb import opentsdb
from t2Mon.common.Utilities import externalCommand
from t2Mon.common.Utilities import run_pipe_cmd
from t2Mon.common.Utilities import getItemPos
from t2Mon.common.procInfo import getProcInfo

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
    return itemOut

def execute():
    config = ConfigReader()
    dbInput = checkConfigForDB(config)
    dbBackend = opentsdb(dbInput)
    startTime = int(time.time())
    print 'Running Main'
    #main(startTime, config, dbBackend)
    get()
    dbBackend.stopWriter()

if __name__ == "__main__":
    print get()
