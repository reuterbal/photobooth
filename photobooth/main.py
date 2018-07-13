#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Photobooth - a flexible photo booth software
# Copyright (C) 2018  Balthasar Reuter <photobooth at re - web dot eu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from pkg_resources import get_distribution, DistributionNotFound
try:
    __version__ = get_distribution('photobooth').version
except DistributionNotFound:
    __version__ = 'unknown'

import logging
import logging.handlers
import multiprocessing as mp
import sys

from . import camera, gui
from .Config import Config
# from .Photobooth import Photobooth
from .util import lookup_and_import
from .StateMachine import Context, ErrorEvent
from .Threading import Communicator, Workers
from .Worker import Worker


class CameraProcess(mp.Process):

    def __init__(self, config, comm):  # conn, worker_queue):

        super().__init__()
        self.daemon = True

        self.cfg = config
        self.comm = comm
        # self.conn = conn
        # self.worker_queue = worker_queue

    # def run_camera(self):

        # try:
        #    # cap = lookup_and_import(
        #    #     camera.modules, self.cfg.get('Camera', 'module'), 'camera')

        #    # photobooth = Photobooth(
        #    #     self.cfg, cap, self.conn, self.worker_queue)
        #    # return photobooth.run()

        # except BaseException as e:
        #     self.conn.send(gui.GuiState.ErrorState('Camera error', str(e)))
        #     event = self.conn.recv()
        #     if str(event) in ('cancel', 'ack'):
        #         return 123
        #     else:
        #         logging.error('Unknown event received: %s', str(event))
        #         raise RuntimeError('Unknown event received', str(event))

    def run(self):

        CameraModule = lookup_and_import(camera.modules,
                                         self.cfg.get('Camera', 'module'),
                                         'camera')
        cap = camera.Camera(self.cfg, self.comm, CameraModule)

        while True:
            try:
                cap.run()
            except Exception as e:
                self.comm.send(Workers.MASTER, ErrorEvent(e))

        # status_code = 123

        # while status_code == 123:
        #     event = self.conn.recv()

        #     if str(event) != 'start':
        #         logging.warning('Unknown event received: %s', str(event))
        #         continue

        #     status_code = self.run_camera()
        #     logging.info('Camera exited with status code %d', status_code)

        # sys.exit(status_code)


class WorkerProcess(mp.Process):

    def __init__(self, config, queue):

        super().__init__()
        self.daemon = True

        self.cfg = config
        self.queue = queue

    def run(self):

        sys.exit(Worker(self.cfg, self.queue).run())


class GuiProcess(mp.Process):

    def __init__(self, argv, config, conn, queue, communicator):

        super().__init__()

        self.argv = argv
        self.cfg = config
        self.conn = conn
        self.queue = queue
        self.comm = communicator

    def run(self):

        Gui = lookup_and_import(gui.modules, self.cfg.get('Gui', 'module'),
                                'gui')
        sys.exit(Gui(self.argv, self.cfg, self.conn, self.queue,
                     self.comm).run())


def run(argv):

    logging.info('Photobooth version: %s', __version__)

    # Load configuration
    config = Config('photobooth.cfg')

    comm = Communicator()
    context = Context(comm)

    # Create communication objects:
    # 1. We use a pipe to connect GUI and camera process
    # 2. We use a queue to feed tasks to the postprocessing process
    gui_conn, camera_conn = mp.Pipe()
    worker_queue = mp.SimpleQueue()

    # Initialize processes: We use three processes here:
    # 1. Camera processing
    # 2. Postprocessing
    # 3. GUI
    camera_proc = CameraProcess(config, comm)  # camera_conn, worker_queue)
    camera_proc.start()

    worker_proc = WorkerProcess(config, worker_queue)
    worker_proc.start()

    gui_proc = GuiProcess(argv, config, gui_conn, worker_queue, comm)
    gui_proc.start()

    for event in comm.iter(Workers.MASTER):
        context.handleEvent(event)

    # Close endpoints
    gui_conn.close()
    camera_conn.close()

    # Wait for processes to finish
    gui_proc.join()
    worker_queue.put('teardown')
    worker_proc.join()
    camera_proc.join(1)
    return gui_proc.exitcode


def main(argv):

    # Setup log level and format
    log_level = logging.DEBUG
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # create console handler and set format
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    # create file handler and set format
    fh = logging.handlers.TimedRotatingFileHandler('photobooth.log', when='d',
                                                   interval=1, backupCount=10)
    fh.setFormatter(formatter)

    # Apply config
    logging.basicConfig(level=log_level, handlers=(ch, fh))

    # Set of known status codes which trigger a restart of the application
    known_status_codes = {
        999: 'Initializing photobooth',
        123: 'Restarting photobooth and reloading config'
    }

    # Run the application until a status code not in above list is encountered
    status_code = 999

    while status_code in known_status_codes:
        logging.info(known_status_codes[status_code])

        status_code = run(argv)

    logging.info('Exiting photobooth with status code %d', status_code)

    return status_code
