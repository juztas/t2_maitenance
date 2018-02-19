#!/usr/bin/python
import json
import subprocess
import time
import potsdb

MAPPING = ['Hadoop:service=NameNode,name=JvmMetrics', 'java.lang:type=Threading', 'java.lang:type=OperatingSystem', 'Hadoop:service=NameNode,name=FSNamesystem',
           'Hadoop:service=NameNode,name=NameNodeActivity', 'Hadoop:service=NameNode,name=NameNodeInfo']

def main(timestamp):
    """ Main method """
    out = gethdfsOut('http://10.3.10.66:50070/jmx')
    for item in out['beans']:
        if item['name'] in MAPPING:
            metrics = potsdb.Client('10.3.10.15', port=4242, qsize=10000, host_tag=True, mps=100, check_host=True)
            uniqKey = getUniqKey(item['name'])
            parsedOut = parseNumeric(item, uniqKey)
            sendMetrics(metrics, timestamp, parsedOut)
            for nodeKey, nodeVal in {'LiveNodes': 0, 'DeadNodes': 1, 'DecomNodes': 2}.items():
                if nodeKey in item:
                    nodeInfo = json.loads(item[nodeKey])
                    parsedOut = {}
                    for nodeName, nodeDict in nodeInfo.items():
                        nodeDict['statusofNode'] = nodeVal
                        parsedOut = appender(nodeDict, 'nodestatus')
                        sendMetrics(metrics, timestamp, parsedOut, nodeName, nodeKey)
            metrics.wait()


def getDirStats(directory):
    hdfs_cmd = "hadoop fs -du %s" % directory
    print 'About to run:'
    print hdfs_cmd

    out = subprocess.Popen(hdfs_cmd, shell=True, stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, _ = out.communicate()
    all_Files = stdout.decode().split("\n")
    return all_Files


def publishMetrics(startKey, cutFirst, allData, timestamp):
    metrics = potsdb.Client('10.3.10.15', port=4242, qsize=10000, host_tag=True, mps=100, check_host=True)
    for item in allData:
        if not item:
            continue
        tmpI = item.split()
        size = int(tmpI[0].strip())
        fullPath = tmpI[1].strip()[cutFirst:]
        metrics.send(startKey, size, timestamp=timestamp, statKey=fullPath)
    metrics.wait()


def runTimer():
    while True:
        startTime = int(time.time())
        print 'Running Main'
        main(startTime)
        print 'Getting dir stats'
        allDirStats = getDirStats('/store')
        publishMetrics('hadoop.spaceUsage.storeSpace', len('/store/'), allDirStats, startTime)
        allDirStats = getDirStats('/store/user/')
        publishMetrics('hadoop.spaceUsage.storeuserSpace', len('/store/user/'), allDirStats, startTime)
        allDirStats = getDirStats('/store/group/')
        publishMetrics('hadoop.spaceUsage.storegroupSpace', len('/store/group/'), allDirStats, startTime)
        endTime = int(time.time())
        totalRuntime = endTime - startTime
        print 'StartTime: %s, EndTime: %s, Runtime: %s' % (startTime, endTime, totalRuntime)
        if totalRuntime < 60:
            time.sleep(int(60 - totalRuntime))
        else:
            time.sleep(1)



if __name__ == "__main__":
    while True:
        runTimer()
    allDirStats = getDirStats('/store')
    publishMetrics('hadoop.spaceUsage.storeSpace', len('/store/'), allDirStats, int(time.time()))
    allDirStats = getDirStats('/store/user/')
    publishMetrics('hadoop.spaceUsage.storeuserSpace', len('/store/user/'), allDirStats, int(time.time()))