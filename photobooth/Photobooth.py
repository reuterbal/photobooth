#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from Config import Config
import Gui
from PyQt5Gui import PyQt5Gui
from CameraOpenCV import CameraOpenCV as Camera

from multiprocessing import Pipe, Process

from time import time, sleep


class Photobooth:

    def __init__(self):

        self._cap = Camera()


    def run(self, send, recv):

        while True:
            try:
                event = recv.recv()
            except EOFError:
                return 1
            else:
                self.trigger(send)

        return 0


    def trigger(self, send):

        send.send(Gui.PoseState())

        sleep(2)

        if self._cap.hasPreview:
            tic, toc = time(), 0

            while toc < 3:
                send.send( Gui.PreviewState(
                    message = str(3 - int(toc)), 
                    picture = self._cap.getPreview() ) )
                toc = time() - tic
        else:
            for i in range(3):
                send.send( Gui.PreviewState(str(i)) )
                sleep(1)

        send.send(Gui.PictureState(self._cap.getPicture()))

        sleep(2)

        send.send(Gui.IdleState())


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
