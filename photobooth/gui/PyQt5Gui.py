#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import multiprocessing as mp
import queue
import logging

from PIL import ImageQt

from PyQt5 import QtGui, QtCore, QtWidgets

import math

from .Qt5Gui import Frames

from .PyQt5GuiHelpers import QRoundProgressBar

from . import *


class PyQt5Gui(Gui):

    def __init__(self, argv, config):

        super().__init__()

        global cfg
        cfg = config

        self._app = QtWidgets.QApplication(argv)
        self._p = PyQt5MainWindow()
        self._lastState = self.showStart
        
        self._postprocessList = []
        self._postprocessQueue = queue.Queue()

        if cfg.getBool('Printer', 'enable'):
            self._postprocessList.append( PrintPostprocess( cfg.get('Printer', 'module'),
                    (cfg.getInt('Printer', 'width'), cfg.getInt('Printer', 'height')) ) )


    def run(self, camera_conn, worker_queue):

        receiver = PyQt5Receiver([camera_conn])
        receiver.notify.connect(self.handleState)
        receiver.start()

        self._conn = camera_conn
        self._queue = worker_queue

        self.showStart()

        exit_code = self._app.exec_()
        self._p = None

        return exit_code


    def close(self):

        self._p.close()


    def restart(self):

        self._app.exit(123)


    def sendAck(self):

        self._conn.send('ack')


    def sendCancel(self):

        self._conn.send('cancel')


    def sendTrigger(self):

        self._conn.send('triggered')


    def sendTeardown(self):

        self._conn.send('teardown')


    def handleKeypressEvent(self, event):

        if event.key() == QtCore.Qt.Key_Escape:
            self.handleState(TeardownState())
        elif event.key() == QtCore.Qt.Key_Space:
            self.handleState(TriggerState())


    def handleKeypressEventNoTrigger(self, event):

        if event.key() == QtCore.Qt.Key_Escape:
            self.handleState(TeardownState())


    def handleState(self, state):

        if not isinstance(state, GuiState):
            raise ValueError('Invalid data received')

        if isinstance(state, IdleState):
            self.showIdle()

        elif isinstance(state, TriggerState):
            self.sendTrigger()

        elif isinstance(state, GreeterState):
            global cfg
            self._p.handleKeypressEvent = self.handleKeypressEventNoTrigger
            # self._p.setCentralWidget( PyQt5GreeterMessage(
            self._p.setCentralWidget( Frames.GreeterMessage(
                cfg.getInt('Picture', 'num_x'), cfg.getInt('Picture', 'num_y') ) )
            QtCore.QTimer.singleShot(cfg.getInt('Photobooth', 'greeter_time') * 1000, self.sendAck)

        elif isinstance(state, CountdownState):
            # self._p.setCentralWidget(PyQt5CountdownMessage(cfg.getInt('Photobooth', 'countdown_time'), self.sendAck))
            countdown_time = cfg.getInt('Photobooth', 'countdown_time')
            self._p.setCentralWidget(Frames.CountdownMessage(countdown_time, 
                                                             self.sendAck))

        elif isinstance(state, PreviewState):
            self._p.centralWidget().picture = ImageQt.ImageQt(state.picture)
            self._p.centralWidget().update()
            
        elif isinstance(state, PoseState):
            # self._p.setCentralWidget(PyQt5PoseMessage())
            self._p.setCentralWidget(Frames.PoseMessage(state.num_picture, 
                cfg.getInt('Picture', 'num_x'), cfg.getInt('Picture', 'num_y')))

        elif isinstance(state, AssembleState):
            self._p.setCentralWidget(Frames.WaitMessage('Processing picture...'))
            # self._p.setCentralWidget(PyQt5WaitMessage('Processing picture...'))

        elif isinstance(state, PictureState):
            img = ImageQt.ImageQt(state.picture)
            # self._p.setCentralWidget(PyQt5PictureMessage(img))
            self._p.setCentralWidget(Frames.PictureMessage(img))
            QtCore.QTimer.singleShot(cfg.getInt('Photobooth', 'display_time') * 1000, 
                lambda : self.postprocessPicture(state.picture))

        elif isinstance(state, TeardownState):
            self._conn.send('teardown')
            self.showStart()

        elif isinstance(state, ErrorState):
            self.showError(state.title, state.message)

        else:
            raise ValueError('Unknown state')


    def postprocessPicture(self, picture):

        for task in self._postprocessList:
            self._postprocessQueue.put(task.get(picture))

        self.handleQueue()


    def handleQueue(self):

        while True:
            try:
                task = self._postprocessQueue.get(block = False)
            except queue.Empty:
                self.sendAck()
                break
            else:
                if isinstance(task, PrintState):
                    reply = QtWidgets.QMessageBox.question(self._p, 'Print picture?', 
                        'Do you want to print the picture?', 
                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
                    if reply == QtWidgets.QMessageBox.Yes:
                        task.handler()
                        QtWidgets.QMessageBox.information(self._p, 'Printing',
                            'Picture sent to printer.', QtWidgets.QMessageBox.Ok)
                else:
                    raise ValueError('Unknown task')


    def showStart(self):

        self._p.handleKeypressEvent = lambda event : None
        self._lastState = self.showStart
        self._p.setCentralWidget(Frames.Start(self.showStartPhotobooth, self.showSettings, self.close))
        if QtWidgets.QApplication.overrideCursor() != 0:
            QtWidgets.QApplication.restoreOverrideCursor()


    def showSettings(self):

        global cfg
        self._p.handleKeypressEvent = lambda event : None
        self._lastState = self.showSettings
        self._p.setCentralWidget(Frames.Settings(cfg, self.showSettings, self.showStart, self.restart))


    def showStartPhotobooth(self):

        self._lastState = self.showStartPhotobooth
        self._conn.send('start')
        # self._p.setCentralWidget(PyQt5WaitMessage('Starting the photobooth...'))
        self._p.setCentralWidget(Frames.WaitMessage('Starting the photobooth...'))
        if cfg.getBool('Gui', 'hide_cursor'):
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.BlankCursor)


    def showIdle(self):

        self._p.handleKeypressEvent = self.handleKeypressEvent
        self._lastState = self.showIdle
        self._p.setCentralWidget(Frames.IdleMessage())
        # self._p.setCentralWidget(PyQt5IdleMessage())


    def showError(self, title, message):

        logging.error('%s: %s', title, message)
        reply = QtWidgets.QMessageBox.warning(self._p, title, message, 
            QtWidgets.QMessageBox.Close | QtWidgets.QMessageBox.Retry, QtWidgets.QMessageBox.Retry) 
        if reply == QtWidgets.QMessageBox.Retry:
            self.sendAck()
            self._lastState()
        else:
            self.sendCancel()
            self.showStart()


class PyQt5Receiver(QtCore.QThread):

    notify = QtCore.pyqtSignal(object)

    def __init__(self, conn):

        super().__init__()

        self._conn = conn


    def handle(self, state):

        self.notify.emit(state)


    def run(self):

        while self._conn:
            for c in mp.connection.wait(self._conn):
                try:
                    state = c.recv()
                except EOFError:
                    break
                else:
                    self.handle(state)



class PyQt5MainWindow(QtWidgets.QMainWindow):

    def __init__(self):

        super().__init__()

        self.handleKeypressEvent = lambda event : None

        self.initUI()


    @property
    def handleKeypressEvent(self):

        return self._handle_key


    @handleKeypressEvent.setter
    def handleKeypressEvent(self, func):

        if not callable(func):
            raise ValueError('Keypress event handler must be callable')

        self._handle_key = func


    def initUI(self):

        global cfg

        self.setWindowTitle('Photobooth')

        if cfg.getBool('Gui', 'fullscreen'):
            self.showFullScreen()
        else:
            self.resize(cfg.getInt('Gui', 'width'), 
                        cfg.getInt('Gui', 'height'))
            self.show()


    def closeEvent(self, e):

        reply = QtWidgets.QMessageBox.question(self, 'Confirmation', "Quit Photobooth?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            e.accept()
        else:
            e.ignore()


    def keyPressEvent(self, event):

        self.handleKeypressEvent(event)
