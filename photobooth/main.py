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
        import_module = importlib.import_module('photobooth.' + package + '.' + result[0])

    if result[1] == None:
        return import_module
    else:
        return getattr(import_module, result[1])


def start_photobooth(config, send, recv):

    while True:
        try:
            Camera = lookup_and_import(camera.modules, config.get('Camera', 'module'), 'camera')

            with Camera() as cap:
                photobooth = Photobooth(config, cap, send, recv)
                return photobooth.run()

        except BaseException as e:
            send.send( gui.ErrorState('Camera error', str(e)) )
            event = recv.recv()
            if str(event) in ('cancel', 'ack'):
                return -1
            else:
                print('Unknown event received: ' + str(event))
                raise RuntimeError('Unknown event received', str(event))


def main_photobooth(config, send, recv):

    while True:
        event = recv.recv()

        if str(event) != 'start':
            continue

        status_code = start_photobooth(config, send, recv)
        print('Camera exit')

        if status_code != -1:
            return status_code


def run(argv):

    print('Photobooth version:', __version__)

    config = Config('photobooth.cfg')

    event_recv, event_send = Pipe(duplex=False)
    gui_recv, gui_send = Pipe(duplex=False)

    photobooth = Process(target=main_photobooth, args=(config, gui_send, event_recv), daemon=True)
    photobooth.start()

    Gui = lookup_and_import(gui.modules, config.get('Gui', 'module'), 'gui')
    status_code = Gui(argv, config).run(event_send, gui_recv)

    photobooth.join(1)
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
