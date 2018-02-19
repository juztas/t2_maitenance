""" """
import potsdb

class opentsdb(object):

    def __init__(self, config):
        self.config = config
        self.metrics = None

    def getWriter(self):
        """ """
        if self.metrics:
            self.stopWriter()
        self.metrics = potsdb.Client('10.3.10.15', port=4242, qsize=10000, host_tag=True, mps=100, check_host=True)

    def stopWriter(self):
        if self.metrics:
            self.metrics.wait()

    def sendMetric(self, key, value, timestamp, extraTags):
        if not self.metrics:
            self.getWriter()
        if extraTags:
            self.metrics.send(key, value, timestamp=timestamp, *extraTags)
        else:
            self.metrics.send(key, value, timestamp=timestamp)
