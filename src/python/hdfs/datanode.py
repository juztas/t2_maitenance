#!/usr/bin/python
import json
from Queue import Queue
from threading import Thread
import subprocess
import time
import potsdb
import socket
MAPPING = ['Hadoop:service=NameNode,name=JvmMetrics', 'java.lang:type=Threading', 'java.lang:type=OperatingSystem', 'Hadoop:service=NameNode,name=FSNamesystem',
           'Hadoop:service=NameNode,name=NameNodeActivity', 'Hadoop:service=NameNode,name=NameNodeInfo']

q = Queue(maxsize=0)
num_threads = 10
results = []

def hdfsCaller(q, result):
    while True:
        inpDict = q.get()
        #print inpDict
        nodeOut = gethdfsOut('http://%s:50075/jmx' % inpDict['nodeName'])  # http://10.3.10.254:50075/jmx
        if nodeOut and 'beans' in nodeOut:
            for item in nodeOut['beans']:
                if 'NumFailedVolumes' in item:
                    #print inpDict['nodeName'], item['NumFailedVolumes']
                    result.append({'nodeName': inpDict['nodeName'], 'failedVolumes': item['NumFailedVolumes']})
        else:
            print 'Failed to get node info from %s' % inpDict['nodeName']
        #print len(nodeOut)
        q.task_done()


def main(timestamp):
    """ Main method """
    out = gethdfsOut('http://10.3.10.66:50070/jmx')
    for item in out['beans']:
        if 'LiveNodes' in item.keys():
            #metrics = potsdb.Client('10.3.10.15', port=4242, qsize=10000, host_tag=True, mps=100, check_host=True)
            nodeInfo = json.loads(item['LiveNodes'])
            parsedOut = {}
            for nodeName, nodeDict in nodeInfo.items():
                 qPut = {'nodeName': nodeName, 'timestamp': timestamp}
                 q.put(qPut)
                 #nodeOut = gethdfsOut('http://%s:50075/jmx' % nodeName)  # http://10.3.10.254:50075/jmx
                 #sendMetrics(metrics, timestamp, parsedOut, nodeName, nodeKey)
            # metrics.wait()
            q.join()
            metrics = None
            while not metrics:
                try:
                    metrics = potsdb.Client('10.3.10.15', port=4242, qsize=10000, host_tag=True, mps=100, check_host=True)
                except socket.timeout as ex:
                    print 'Got Socket timeout. %s' % ex
                    time.sleep(1)
            for i in xrange(len(results) - 1, -1, -1):
                element = results[i]
                metrics.send('hadoop.datanode.failedvolumes', element['failedVolumes'], timestamp=timestamp, datanode=element['nodeName'], haveFailed='Yes' if element['failedVolumes'] else 'No')
                del results[i]
            metrics.wait()
            print results


def runTimer():
    while True:
        startTime = int(time.time())
        print 'Running Main'
        main(startTime)
        endTime = int(time.time())
        totalRuntime = endTime - startTime
        print 'StartTime: %s, EndTime: %s, Runtime: %s' % (startTime, endTime, totalRuntime)
        if totalRuntime < 60:
            time.sleep(int(60-totalRuntime))
        else:
            time.sleep(1)

for i in range(num_threads):
    worker = Thread(target=hdfsCaller, args=(q, results))
    worker.setDaemon(True)
    worker.start()


if __name__ == "__main__":
    while True:
        runTimer()