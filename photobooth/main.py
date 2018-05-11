#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pkg_resources import get_distribution, DistributionNotFound
try:
    __version__ = get_distribution('photobooth').version
except DistributionNotFound:
    __version__ = 'unknown'

import multiprocessing as mp
import importlib
import sys

from . import camera, gui
from .Config import Config
from .Photobooth import Photobooth


def lookup_and_import(module_list, name, package=None):

    result = next(((mod_name, class_name) 
                for config_name, mod_name, class_name in module_list
                if name == config_name), None)
    
    if package == None:
        import_module = importlib.import_module('photobooth.' + result[0])
    else:
        import_module = importlib.import_module(
            'photobooth.' + package + '.' + result[0])

    if result[1] == None:
        return import_module
    else:
        return getattr(import_module, result[1])


class CameraProcess(mp.Process):

    def __init__(self, config, conn):

        super().__init__()
        self.daemon = True

        self.cfg = config
        self.conn = conn


    def run_camera(self):

        # while True:
        try:
            cap = lookup_and_import(
                camera.modules, self.cfg.get('Camera', 'module'), 'camera')

            photobooth = Photobooth(self.cfg, cap, self.conn)
            return photobooth.run()

        except BaseException as e:
            self.conn.send( gui.ErrorState('Camera error', str(e)) )
            event = self.conn.recv()
            if str(event) in ('cancel', 'ack'):
                return 123
            else:
                print('Unknown event received: ' + str(event))
                raise RuntimeError('Unknown event received', str(event))


    def run(self):

        status_code = 123

        while status_code == 123:
            event = self.conn.recv()

            if str(event) != 'start':
                continue

            status_code = self.run_camera()
            print('Camera exit')

        sys.exit(status_code)


class GuiProcess(mp.Process):

    def __init__(self, argv, config, conn):

        super().__init__()

        self.argv = argv
        self.cfg = config
        self.conn = conn


    def run(self):

        Gui = lookup_and_import(gui.modules, self.cfg.get('Gui', 'module'), 'gui')
        sys.exit(Gui(self.argv, self.cfg).run(self.conn))


def run(argv):

    print('Photobooth version:', __version__)

    config = Config('photobooth.cfg')

    gui_conn, camera_conn = mp.Pipe()

    camera_worker = CameraProcess(config, camera_conn)
    camera_worker.start()

    gui_worker = GuiProcess(argv, config, gui_conn)
    gui_worker.start()

    gui_conn.close()
    camera_conn.close()

    gui_worker.join()
    camera_worker.join(5)
    return gui_worker.exitcode


def main(argv):

    known_status_codes = {
        999: 'Initializing photobooth',
        123: 'Restarting photobooth and reloading config'
    }

    status_code = 999

    while status_code in known_status_codes:
        print(known_status_codes[status_code])

        status_code = run(argv)

    return status_code
