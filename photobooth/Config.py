#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import logging
import os


class Config:

    def __init__(self, filename):

        self._filename = filename

        self._cfg = configparser.ConfigParser(interpolation=None)
        self.defaults()
        self.read()

    @property
    def filename(self):

        return self._filename

    @filename.setter
    def filename(self, value):

        self._filename = value

    def defaults(self):

        filename = os.path.join(os.path.dirname(__file__), 'defaults.cfg')
        logging.info('Reading config file "%s"', filename)
        self._cfg.read(filename)

    def read(self):

        logging.info('Reading config file "%s"', self._filename)
        self._cfg.read(self._filename)

    def write(self):

        logging.info('Writing config file "%s"', self._filename)
        with open(self._filename, 'w') as configfile:
            self._cfg.write(configfile)

    def get(self, section, key):

        return self._cfg[section][key]

    def getInt(self, section, key):

        return self._cfg.getint(section, key)

    def getFloat(self, section, key):

        return self._cfg.getfloat(section, key)

    def getBool(self, section, key):

        return self._cfg.getboolean(section, key)

    def set(self, section, key, value):

        self._cfg[section][key] = value
