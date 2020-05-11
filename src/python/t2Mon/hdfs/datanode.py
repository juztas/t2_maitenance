#!/usr/bin/python
import json
import time
from Queue import Queue
from threading import Thread
from t2Mon.common.Utilities import externalCommand
from t2Mon.common.Utilities import checkConfigForDB
from t2Mon.common.configReader import ConfigReader
from t2Mon.common.database.opentsdb import opentsdb
from common import gethdfsOut
from t2Mon.hdfs.common import getUniqKey
from t2Mon.hdfs.common import parseNumeric

MAPPING = ['Hadoop:service=DataNode,name=JvmMetrics', 'java.lang:type=Threading', 'java.lang:type=OperatingSystem', 'Hadoop:service=DataNode,name=DataNodeInfo']

q = Queue(maxsize=0)
num_threads = 10
results = []

def hdfsCaller(q, result):
    while True:
        inpDict = q.get()
        nodeOut = gethdfsOut('http://%s:50075/jmx' % inpDict['nodeName'])  # http://10.3.10.254:50075/jmx
        if nodeOut and 'beans' in nodeOut:
            for item in nodeOut['beans']:
                if item['name'] in MAPPING:
                    uniqKey = getUniqKey(item['name'])
                    parsedOut = parseNumeric(item, uniqKey)
                    if item['name'] == 'Hadoop:service=DataNode,name=DataNodeInfo':
                        diskid = 0
                        volsinfo = json.loads(item['VolumeInfo'])
                        for key in volsinfo.keys():
                            diskid += 1
                            totalspace = volsinfo[key]['usedSpace'] + volsinfo[key]['freeSpace']
                            results.append({'nodeName': inpDict['nodeName'], 'volume': key, 'totalspace': totalspace})
                            for valk, valval in volsinfo[key].items():
#                               print key, valk, valval, diskid
                                result.append({'nodeName': inpDict['nodeName'], 'key': valk, 'value': valval, 'tagkey': 'diskid', 'tagvalue': diskid})
                    for key, value in parsedOut.items():
                        result.append({'nodeName': inpDict['nodeName'], 'key': key, 'value': value})
                if 'NumFailedVolumes' in item:
                    result.append({'nodeName': inpDict['nodeName'], 'key': 'failedVolumes', 'value': item['NumFailedVolumes']})
        else:
            print 'Failed to get node info from %s' % inpDict['nodeName']
            result.append({'nodeName': inpDict['nodeName'], 'key': 'failedtoRetrieve', 'value': 1})
        q.task_done()


def main(timestamp, config, dbBackend):
    """ Main method """
    out = gethdfsOut('http://%s:50070/jmx' % config.getOption('hdfs', 'namenode'))
    if not (out and 'beans' in out):
        print out
        dbBackend.sendMetric('hadoop.monscript.faileddatanode', 1, {'timestamp': timestamp})
        return
    for item in out['beans']:
        if 'LiveNodes' in item.keys():
            nodeInfo = json.loads(item['LiveNodes'])
            for nodeName in nodeInfo.keys():
                qPut = {'nodeName': nodeName, 'timestamp': timestamp}
                q.put(qPut)
            q.join()
            for incr in xrange(len(results) - 1, -1, -1):
                element = results[incr]
                tags = {'timestamp': timestamp, 'datanode': element['nodeName']}
                #if element['key'] == 'failedvolumes':
                #    tags['haveFailed'] = 'Yes' if element['value'] else 'No'
                #    #dbBackend.sendMetric('hadoop.datanode.failedvolumes', element['value'], tags)
                #elif element['key'] == 'failedtoRetrieve':
                #    tags['failedtoRetrieve'] = element['value']
                #    #dbBackend.sendMetric('hadoop.datanode.failedtoRetrieve', element['value'], tags)
                #else:
                #    if 'tagkey' in element.keys():
                #        tags[element['tagkey']] = element['tagvalue']
                #    #dbBackend.sendMetric('hadoop.datanode.%s' % element['key'], element['value'], tags)
                if 'volume' in element.keys():
                    print element['nodeName'], element['volume'], element['totalspace']
                del results[incr]
    return

def execute():
    config = ConfigReader()
    dbInput = checkConfigForDB(config)
    dbBackend = opentsdb(dbInput)
    startTime = int(time.time())
    print 'Running Main'
    main(startTime, config, dbBackend)
    dbBackend.stopWriter()


for i in range(num_threads):
    worker = Thread(target=hdfsCaller, args=(q, results))
    worker.setDaemon(True)
    worker.start()


if __name__ == "__main__":
    execute()
