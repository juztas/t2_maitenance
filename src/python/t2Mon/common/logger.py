#!/usr/bin/python
import os
import logging
from logging import StreamHandler
from logging.handlers import TimedRotatingFileHandler


def createDirs(fullDirPath):
    """ Create Directories on fullDirPath"""
    dirname = os.path.dirname(fullDirPath)
    if not os.path.isdir(dirname):
        try:
            os.makedirs(dirname)
        except OSError as ex:
            print(('Received exception creating %s directory. Exception: %s' % (dirname, ex)))
            if not os.path.isdir(dirname):
                raise
    return


def getLogger(logFile='', logLevel='DEBUG', logOutName='api.log', rotateTime='midnight', backupCount=10):
    """ Get new Logger for logging """
    levels = {'FATAL': logging.FATAL,
              'ERROR': logging.ERROR,
              'WARNING': logging.WARNING,
              'INFO': logging.INFO,
              'DEBUG': logging.DEBUG}
    logger = logging.getLogger()
    createDirs(logFile)
    logFile += logOutName
    handler = TimedRotatingFileHandler(logFile, when=rotateTime, backupCount=backupCount)
    formatter = logging.Formatter("%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s",
                                  datefmt="%a, %d %b %Y %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(levels[logLevel])
    return logger


def getStreamLogger(logLevel='DEBUG'):
    """ Get Stream Logger """
    levels = {'FATAL': logging.FATAL,
              'ERROR': logging.ERROR,
              'WARNING': logging.WARNING,
              'INFO': logging.INFO,
              'DEBUG': logging.DEBUG}
    logger = logging.getLogger()
    handler = StreamHandler()
    formatter = logging.Formatter("%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s",
                                  datefmt="%a, %d %b %Y %H:%M:%S")
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    logger.setLevel(levels[logLevel])
    return logger
