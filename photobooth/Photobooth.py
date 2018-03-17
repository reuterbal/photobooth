#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import Config, PyQt5Gui

def main(argv):

    config = Config.Config('photobooth.cfg')
    return PyQt5Gui.run(argv, config)
