#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from Config import Config
from PyQt5Gui import PyQt5Gui

from multiprocessing import Pipe, Process

from time import sleep


class Photobooth:

    def __init__(self):

        pass


    def run(self, send, recv):

        while True:
            try:
                event = recv.recv()
            except EOFError:
                return 1
            else:
                print('Photobooth: ' + event)
                self.trigger(send)

        return 0


    def trigger(self, send):

        send.send('Pose')

        sleep(3)

        send.send('Picture')

        sleep(2)

        send.send('idle')


def main_photobooth(send, recv):

    photobooth = Photobooth()
    return photobooth.run(send, recv)


def main(argv):

    config = Config('photobooth.cfg')

    event_recv, event_send = Pipe(duplex=False)
    gui_recv, gui_send = Pipe(duplex=False)

    photobooth = Process(target=main_photobooth, args=(gui_send, event_recv), daemon=True)
    photobooth.start()

    gui = PyQt5Gui(argv, config)
    return gui.run(event_send, gui_recv)
