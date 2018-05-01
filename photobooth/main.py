#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pkg_resources import get_distribution, DistributionNotFound
try:
    __version__ = get_distribution('photobooth').version
except DistributionNotFound:
    __version__ = 'unknown'

from multiprocessing import Pipe, Process
import importlib

import camera, gui
from Config import Config
from Photobooth import Photobooth


def lookup_and_import(module_list, name, package=None):

    result = next(((mod_name, class_name) 
                for config_name, mod_name, class_name in module_list
                if name == config_name), None)
    
    if package == None:
        import_module = importlib.import_module(result[0])
    else:
        import_module = importlib.import_module('.' + result[0], package)

    if result[1] == None:
        return import_module
    else:
        return getattr(import_module, result[1])


def main_photobooth(config, send, recv):

    event = recv.recv()
    if str(event) != 'start':
        print('Unknown event received: ' + str(event))
        raise RuntimeError('Unknown event received', str(event))

    while True:
        try:
            Camera = lookup_and_import(camera.modules, config.get('Camera', 'module'), 'camera')

            with Camera() as cap:
                photobooth = Photobooth(config, cap)
                return photobooth.run(send, recv)

        except BaseException as e:
            send.send( gui.ErrorState('Camera error', str(e)) )
            event = recv.recv()
            if str(event) == 'cancel':
                return 1
            elif str(event) == 'ack':
                pass
            else:
                print('Unknown event received: ' + str(event))
                raise RuntimeError('Unknown event received', str(event))


def run(argv):
    print('Photobooth version:', __version__)

    config = Config('photobooth.cfg')

    event_recv, event_send = Pipe(duplex=False)
    gui_recv, gui_send = Pipe(duplex=False)

    photobooth = Process(target=main_photobooth, args=(config, gui_send, event_recv), daemon=True)
    photobooth.start()

    Gui = lookup_and_import(gui.modules, config.get('Gui', 'module'), 'gui')
    return Gui(argv, config).run(event_send, gui_recv)


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
