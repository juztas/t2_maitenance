#!/usr/bin/python

import os
import configparser


class ConfigReader(object):

    def __init__(self, location='/etc/t2_maitenance.conf'):
        self.configLocation = location
        self.config = None
        self.getConfig()

    def getConfig(self):
        """ Get parsed configuration """
        self.config = configparser.ConfigParser()
        if os.path.isfile(self.configLocation):
            self.config.read(self.configLocation)
            return True
        return False

    def hasSection(self, sectionName):
        """ Check if section is available """
        if self.config.has_section(sectionName):
            return True
        return False

    def hasOption(self, sectionName, optionName):
        """ Check if option is available """
        if self.hasSection(sectionName):
            if self.config.has_option(sectionName, optionName):
                return True
        return False

    def getOption(self, sectionName, optionName):
        """ Get option Value """
        if self.hasOption(sectionName, optionName):
            return self.config.get(sectionName, optionName)
        return None

    def getOptions(self, sectionName):
        """ Get all Options keys """
        if self.hasSection(sectionName):
            return dict(self.config.items(sectionName))
        return {}