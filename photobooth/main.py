#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pkg_resources import get_distribution, DistributionNotFound
try:
    __version__ = get_distribution('photobooth').version
except DistributionNotFound:
    __version__ = 'unknown'

import multiprocessing as mp
import sys

from . import camera, gui
from .Config import Config
from .Photobooth import Photobooth
from .util import lookup_and_import

class CameraProcess(mp.Process):

    def __init__(self, config, conn, worker_queue):

        super().__init__()
        self.daemon = True

        self.cfg = config
        self.conn = conn
        self.worker_queue = worker_queue


    def run_camera(self):

        try:
            cap = lookup_and_import(
                camera.modules, self.cfg.get('Camera', 'module'), 'camera')

            photobooth = Photobooth(
                self.cfg, cap, self.conn, self.worker_queue)
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
            print('Camera exit: ', str(status_code))

        sys.exit(status_code)


class WorkerProcess(mp.Process):

    def __init__(self, config, queue):

        super().__init__()
        self.daemon = True

        self.cfg = config
        self.queue = queue


    def run(self):

        print('Started Worker')
        print('Exit Worker')


class GuiProcess(mp.Process):

    def __init__(self, argv, config, conn, queue):

        super().__init__()

        self.argv = argv
        self.cfg = config
        self.conn = conn
        self.queue = queue


    def run(self):

        Gui = lookup_and_import(gui.modules, self.cfg.get('Gui', 'module'), 'gui')
        sys.exit(Gui(self.argv, self.cfg).run(self.conn, self.queue))


def run(argv):

    print('Photobooth version:', __version__)

    config = Config('photobooth.cfg')

    gui_conn, camera_conn = mp.Pipe()
    worker_queue = mp.SimpleQueue()

    camera_proc = CameraProcess(config, camera_conn, worker_queue)
    camera_proc.start()

    worker_proc = WorkerProcess(config, worker_queue)
    worker_proc.start()

    gui_proc = GuiProcess(argv, config, gui_conn, worker_queue)
    gui_proc.start()

    gui_conn.close()
    camera_conn.close()

    gui_proc.join()
    camera_proc.join(5)
    return gui_proc.exitcode


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
