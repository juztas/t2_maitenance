#!/usr/bin/python
import socket
import json
import shutil
import subprocess
import time
import copy
from t2Mon.common.Utilities import externalCommand
from t2Mon.common.Utilities import checkConfigForDB
from t2Mon.common.configReader import ConfigReader
from t2Mon.common.database.opentsdb import opentsdb
from t2Mon.hdfs.common import gethdfsOut
from t2Mon.hdfs.common import parseNumeric
from t2Mon.hdfs.common import appender
from t2Mon.hdfs.common import getUniqKey

MAPPING = ['Hadoop:service=NameNode,name=JvmMetrics', 'java.lang:type=Threading', 'java.lang:type=OperatingSystem', 'Hadoop:service=NameNode,name=FSNamesystem',
           'Hadoop:service=NameNode,name=NameNodeActivity', 'Hadoop:service=NameNode,name=NameNodeInfo', 'Hadoop:service=NameNode,name=BlockStats']

def getipfromhostname(hostname):
    """ This is just a dummy way to exclude already removed datanodes.
        HDFS Requires namenode restart to clean this up. Solved only in 3.0
        'LiveNodes': 0, 'DeadNodes': 1, 'DecomNodes': 2
    """
    try:
        socket.gethostbyname(hostname)
        return 1
    except socket.gaierror:
        # This means host is not resolvable
        return 2
    except Exception as ex:
        # New exception unknown.
        print 'Got Exception: %s' % ex
        return 1


def main(timestamp, config, dbBackend):
    """ Main method """
    out = gethdfsOut('http://%s:50070/jmx' % config.getOption('hdfs', 'namenode'))
    totalNodes = {'totalnodes': 0, 'livenodes': 0, 'deadnodes': 0, 'decomnodes': 0}
    if not (out and 'beans' in out):
        print out
        dbBackend.sendMetric('hadoop.monscript.failednamenode', 1, {'timestamp': timestamp})
        return
    livenodesstats = {}
    percentremaining = 0
    for item in out['beans']:
        if item['name'] in MAPPING:
            uniqKey = getUniqKey(item['name'])
            parsedOut = parseNumeric(item, uniqKey)
            for key, value in parsedOut.items():
                if key == 'hadoop.NameNodeInfo.PercentRemaining':
                    percentremaining = int(value)
                dbBackend.sendMetric(key, value, {'timestamp': timestamp})
            for nodeKey, nodeVal in {'LiveNodes': 0, 'DeadNodes': 1, 'DecomNodes': 2}.items():
                if nodeKey in item:
                    nodeStatus = nodeVal
                    nodeInfo = json.loads(item[nodeKey])
                    if nodeKey == 'LiveNodes':
                        livenodesstats = copy.copy(nodeInfo)
                    parsedOut = {}
                    totalNodes[nodeKey.lower()] += len(nodeInfo)
                    totalNodes['totalnodes'] += len(nodeInfo)
                    for nodeName, nodeDict in nodeInfo.items():
                        if 'decommissioned' in nodeDict.keys() and nodeDict['decommissioned']:
                            continue
                        if nodeKey == 'DeadNodes':
                            nodeStatus = getipfromhostname(nodeName)
                            if nodeStatus == 2:
                                continue
                        nodeDict['statusofNode'] = nodeStatus
                        parsedOut = appender(nodeDict, 'nodestatus')
                        for key, value in parsedOut.items():
                            dbBackend.sendMetric(key, value, {'timestamp': timestamp,
                                                              'nodeName': nodeName,
                                                              'nodeKey': nodeKey})
    nodesizes = {}
    for nodename, nodevals in livenodesstats.items():
        usedSpace = float(nodevals.get('usedSpace', 0))
        capacity = float(nodevals.get('capacity', 0))
        try:
            leftpercentage = round(((capacity-usedSpace)*100) / capacity, 2)
            nodesizes[nodename] = leftpercentage
            dbBackend.sendMetric('hadoop.nodestatus.leftpercentage', leftpercentage, {'timestamp': timestamp,
                                                                                      'nodeName': nodename})
        except ZeroDivisionError as ex:
            print 'Zero Division Error for %s %s' % (nodename, str(nodevals))
            continue
    with open('/tmp/nodelistpercent.temp', 'a') as fd:
        counter = 20
        for key, value in sorted(nodesizes.iteritems(), key=lambda (k,v): (v,k)):
            if counter <= 0:
                break
            counter -= 1
            fd.write('%s\n' % socket.gethostbyname(key))
    shutil.move('/tmp/nodelistpercent.temp', '/tmp/nodelistpercent.list')
    for key, value in totalNodes.items():
        dbBackend.sendMetric('hadoop.nodestatus.%s' % key, value, {'timestamp': timestamp})

def getDirStats(directory):
    hdfs_cmd = "sudo -u hdfs hadoop fs -du %s" % directory
    print 'About to run:'
    print hdfs_cmd
    out = subprocess.Popen(hdfs_cmd, shell=True, stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, _ = out.communicate()
    all_Files = stdout.decode().split("\n")
    return all_Files


def publishMetrics(dbBackend, startKey, cutFirst, allData, timestamp):
    for item in allData:
        if not item:
            continue
        tmpI = item.split()
        size = int(tmpI[0].strip())
        fullPath = tmpI[2].strip()[cutFirst:]
        dbBackend.sendMetric(startKey, size, {'timestamp': timestamp, 'statKey': fullPath})

def execute():
    config = ConfigReader()
    dbInput = checkConfigForDB(config)
    dbBackend = opentsdb(dbInput)
    startTime = int(time.time())
    print 'Running Main'
    main(startTime, config, dbBackend)
    print 'Getting dir stats'
    allDirStats = getDirStats('/store')
    publishMetrics(dbBackend, 'hadoop.spaceUsage.storeSpace', len('/store/'), allDirStats, startTime)
    allDirStats = getDirStats('/store/user/')
    publishMetrics(dbBackend, 'hadoop.spaceUsage.storeuserSpace', len('/store/user/'), allDirStats, startTime)
    allDirStats = getDirStats('/store/group/')
    publishMetrics(dbBackend, 'hadoop.spaceUsage.storegroupSpace', len('/store/group/'), allDirStats, startTime)
    dbBackend.stopWriter()  # Flush out everything what is left.
    endTime = int(time.time())
    totalRuntime = endTime - startTime
    print 'StartTime: %s, EndTime: %s, Runtime: %s' % (startTime, endTime, totalRuntime)

if __name__ == "__main__":
    execute()
