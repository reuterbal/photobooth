#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pkg_resources import get_distribution, DistributionNotFound
try:
    __version__ = get_distribution('photobooth').version
except DistributionNotFound:
    __version__ = 'unknown'

from multiprocessing import Pipe, Process
import importlib

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


def start_worker(config, conn):

    while True:
        try:
            Camera = lookup_and_import(
                camera.modules, config.get('Camera', 'module'), 'camera')

            with Camera() as cap:
                photobooth = Photobooth(config, cap, conn)
                return photobooth.run()

        except BaseException as e:
            conn.send( gui.ErrorState('Camera error', str(e)) )
            event = conn.recv()
            if str(event) in ('cancel', 'ack'):
                return -1
            else:
                print('Unknown event received: ' + str(event))
                raise RuntimeError('Unknown event received', str(event))


def main_worker(config, conn):

    while True:
        event = conn.recv()

        if str(event) != 'start':
            continue

        status_code = start_worker(config, conn)
        print('Camera exit')

        if status_code != -1:
            return status_code


def run(argv):

    print('Photobooth version:', __version__)

    config = Config('photobooth.cfg')

    gui_conn, worker_conn = Pipe()

    worker = Process(target=main_worker, args=(config, worker_conn), daemon=True)
    worker.start()

    Gui = lookup_and_import(gui.modules, config.get('Gui', 'module'), 'gui')
    status_code = Gui(argv, config).run(gui_conn)

    worker.join(1)
    return status_code


def main(argv):

    known_status_codes = {
        -1: 'Initializing photobooth',
        -2: 'Restarting photobooth and reloading config'
    }

    status_code = -1

    while status_code in known_status_codes:
        print(known_status_codes[status_code])

        status_code = run(argv)

    return status_code
