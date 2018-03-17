#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser, os


class Config:

    def __init__(self, filename):

        self._filename = filename

        self._cfg = configparser.ConfigParser()
        self.defaults()
        self.read()


    @property
    def filename(self):

        return self._filename


    @filename.setter
    def filename(self, value):

        self._filename = value


    def defaults(self):

        self._cfg.read(os.path.join(os.path.dirname(__file__), 'defaults.cfg'))


    def read(self):

        self._cfg.read(self._filename)


    def write(self):

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
