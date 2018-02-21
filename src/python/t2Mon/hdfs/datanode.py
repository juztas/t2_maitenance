#!/usr/bin/python
import json
import time
from Queue import Queue
from threading import Thread
from t2Mon.common.Utilities import externalCommand
from t2Mon.common.Utilities import checkConfigForDB
from t2Mon.common.configReader import ConfigReader
from t2Mon.common.database.opentsdb import opentsdb
from t2Mon.hdfs.common import gethdfsOut


MAPPING = ['Hadoop:service=NameNode,name=JvmMetrics', 'java.lang:type=Threading', 'java.lang:type=OperatingSystem', 'Hadoop:service=NameNode,name=FSNamesystem',
           'Hadoop:service=NameNode,name=NameNodeActivity', 'Hadoop:service=NameNode,name=NameNodeInfo']

q = Queue(maxsize=0)
num_threads = 10
results = []

def hdfsCaller(q, result):
    while True:
        inpDict = q.get()
        nodeOut = gethdfsOut('http://%s:50075/jmx' % inpDict['nodeName'])  # http://10.3.10.254:50075/jmx
        if nodeOut and 'beans' in nodeOut:
            for item in nodeOut['beans']:
                if 'NumFailedVolumes' in item:
                    result.append({'nodeName': inpDict['nodeName'], 'failedVolumes': item['NumFailedVolumes']})
        else:
            print 'Failed to get node info from %s' % inpDict['nodeName']
        q.task_done()


def main(timestamp, config, dbBackend):
    """ Main method """
    out = gethdfsOut('http://%s:50070/jmx' % config.getOption('hdfs', 'namenode'))
    for item in out['beans']:
        if 'LiveNodes' in item.keys():
            nodeInfo = json.loads(item['LiveNodes'])
            for nodeName in nodeInfo.keys():
                qPut = {'nodeName': nodeName, 'timestamp': timestamp}
                q.put(qPut)
            q.join()
            for incr in xrange(len(results) - 1, -1, -1):
                element = results[incr]
                dbBackend.sendMetric('hadoop.datanode.failedvolumes', element['failedVolumes'],
                                     {'timestamp': timestamp, 'datanode': element['nodeName'],
                                      'haveFailed': 'Yes' if element['failedVolumes'] else 'No'})
                del results[incr]
            print results
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
