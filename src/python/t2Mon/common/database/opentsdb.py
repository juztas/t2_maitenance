#!/usr/bin/python
""" opentsdb client to publish information """
import potsdb

class opentsdb(object):

    def __init__(self, config):
        self.config = config
        self.ip = config['server']
        self.port = int(config['port'])
        self.qsize = int(config['qsize'])
        self.host_tag = bool(config['host_tag'])
        self.mps = int(config['mps'])
        self.check_host = bool(config['check_host'])
        self.metrics = None
        self.counter = 0

    def getWriter(self):
        """ """
        if self.metrics:
            self.counter = 0
            self.stopWriter()
        self.metrics = potsdb.Client(self.ip, port=self.port, qsize=self.qsize, host_tag=self.host_tag, mps=self.mps, check_host=self.check_host)

    def stopWriter(self):
        if self.metrics:
            self.metrics.wait()

    def sendMetric(self, key, value, extraTags):
        if not self.metrics:
            self.getWriter()
        self.metrics.send(key, value, **extraTags)
        self.counter += 1
        if self.counter >= self.qsize:
            # We need to flush everything as otherwise it can fail due to too many points
            self.stopWriter()
            self.counter = 0
