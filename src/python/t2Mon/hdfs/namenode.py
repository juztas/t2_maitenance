#!/usr/bin/python
import gc
import socket
import json
import shutil
import subprocess
import time
import copy
from t2Mon.common.Utilities import checkConfigForDB
from t2Mon.common.configReader import ConfigReader
from t2Mon.common.database.opentsdb import opentsdb
from t2Mon.common.logger import getStreamLogger
from t2Mon.hdfs.common import gethdfsOut
from t2Mon.hdfs.common import parseNumeric
from t2Mon.hdfs.common import appender
from t2Mon.hdfs.common import getUniqKey



MAPPING = ['Hadoop:service=NameNode,name=JvmMetrics', 'java.lang:type=Threading',
           'java.lang:type=OperatingSystem', 'Hadoop:service=NameNode,name=FSNamesystem',
           'Hadoop:service=NameNode,name=NameNodeActivity', 'Hadoop:service=NameNode,name=NameNodeInfo',
           'Hadoop:service=NameNode,name=BlockStats', 'Hadoop:service=NameNode,name=FSNamesystemState']


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
        print('Got Exception: %s' % ex)
        return 1


def main(timestamp, config, dbBackend, logger):
    """ Main method """
    out = gethdfsOut('http://%s:50070/jmx' % config.getOption('hdfs', 'namenode'))
    totalNodes = {'totalnodes': 0, 'livenodes': 0, 'deadnodes': 0, 'decomnodes': 0}
    if not (out and 'beans' in out):
        logger.debug('Error: %s' % out)
        dbBackend.sendMetric('hadoop.monscript.failednamenode', 1, {'timestamp': timestamp})
        return
    livenodesstats = {}
    for item in out['beans']:
        if item['name'] in MAPPING:
            uniqKey = getUniqKey(item['name'])
            if item['name'] == 'Hadoop:service=NameNode,name=FSNamesystemState':
                topusercount = {}
                try:
                    topusercount = json.loads(item['TopUserOpCounts'])['windows'][0]['ops']
                except:
                    logger.debug('Error get TopUserOpCounts')
                    break
                for item1 in topusercount:
                    opType = item1['opType']
                    opType = 'wildcard' if opType == '*' else opType
                    for user in item1['topUsers']:
                        dbBackend.sendMetric('hadoop.userops', user['count'], {'timestamp': timestamp,
                                                                               'user': user['user'],
                                                                               'operation': opType})
            parsedOut = parseNumeric(item, uniqKey)
            for key, value in parsedOut.items():
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
            logger.debug('Zero Division Error for %s %s. Exception: %s' % (nodename, str(nodevals), ex))
            continue
    for key, value in totalNodes.items():
        dbBackend.sendMetric('hadoop.nodestatus.%s' % key, value, {'timestamp': timestamp})


def getDirStats(directory, logger):
    hdfs_cmd = "sudo -u hdfs hadoop fs -du %s" % directory
    logger.info('About to run: %s' % hdfs_cmd)
    out = subprocess.Popen(hdfs_cmd, shell=True, stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, _ = out.communicate()
    all_Files = stdout.decode().split("\n")
    return all_Files


def publishMetrics(dbBackend, startKey, cutFirst, allData, timestamp, logger):
    for item in allData:
        if not item:
            continue
        tmpI = item.split()
        size = int(tmpI[0].strip())
        fullPath = tmpI[2].strip()[cutFirst:]
        logger.debug("Path: %s, Size: %s" % (fullPath, size))
        dbBackend.sendMetric(startKey, size, {'timestamp': timestamp, 'statKey': fullPath})


def execute(logger):
    config = ConfigReader()
    dbInput = checkConfigForDB(config)
    dbBackend = opentsdb(dbInput)
    startTime = int(time.time())
    logger.info('Running Main')
    main(startTime, config, dbBackend, logger)
    logger.info('Getting dir stats')
    allDirStats = getDirStats('/store', logger)
    publishMetrics(dbBackend, 'hadoop.spaceUsage.storeSpace', len('/store/'), allDirStats, startTime, logger)
    allDirStats = getDirStats('/store/user/', logger)
    publishMetrics(dbBackend, 'hadoop.spaceUsage.storeuserSpace', len('/store/user/'), allDirStats, startTime, logger)
    allDirStats = getDirStats('/store/group/', logger)
    publishMetrics(dbBackend, 'hadoop.spaceUsage.storegroupSpace', len('/store/group/'), allDirStats, startTime, logger)
    dbBackend.stopWriter()  # Flush out everything what is left.
    endTime = int(time.time())
    totalRuntime = endTime - startTime
    logger.info('StartTime: %s, EndTime: %s, Runtime: %s' % (startTime, endTime, totalRuntime))

if __name__ == "__main__":
    DAEMONNAME = 'namenode-mon'
    LOGGER = getStreamLogger()
    import pdb; pdb.set_trace()
    found_objects = gc.get_objects()
    print('%d objects before' % len(found_objects))
    execute(LOGGER)
    found_objects = gc.get_objects()
    print('%d objects after' % len(found_objects))
    execute(LOGGER)
    found_objects = gc.get_objects()
    print('%d objects after' % len(found_objects))
