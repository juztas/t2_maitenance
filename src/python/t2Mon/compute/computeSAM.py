#!/usr/bin/python
""" """
from t2Mon.common.Utilities import externalCommand
from t2Mon.common.configReader import ConfigReader
from t2Mon.common.database.opentsdb import opentsdb

def checkConfigForDB(config):
    if config.hasSection('opentsdb'):
        return config.getOptions('opentsdb')
    return {}

def execute():
    """Main Execution"""
    config = ConfigReader()
    dbInput = checkConfigForDB(config)
    dbBack = opentsdb(dbInput)
    if config.hasSection('compute'):
        if config.hasOption('checks'):
            allChecks = config.getOption('compute', 'checks').split(',')
            print allChecks


if __name__ == "__main__":
    execute()
