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
            self._p.setCentralWidget( PyQt5GreeterMessage(
                cfg.getInt('Picture', 'num_x'), cfg.getInt('Picture', 'num_y') ) )
            QtCore.QTimer.singleShot(cfg.getInt('Photobooth', 'greeter_time') * 1000, self.sendAck)

        elif isinstance(state, CountdownState):
            self._p.setCentralWidget(PyQt5CountdownMessage(cfg.getInt('Photobooth', 'countdown_time'), self.sendAck))

        elif isinstance(state, PreviewState):
            self._p.centralWidget().picture = ImageQt.ImageQt(state.picture)
            self._p.centralWidget().update()
            
        elif isinstance(state, PoseState):
            self._p.setCentralWidget(PyQt5PoseMessage())

        elif isinstance(state, AssembleState):
            self._p.setCentralWidget(Frames.WaitMessage('Processing picture...'))
            # self._p.setCentralWidget(PyQt5WaitMessage('Processing picture...'))

        elif isinstance(state, PictureState):
            img = ImageQt.ImageQt(state.picture)
            self._p.setCentralWidget(PyQt5PictureMessage(img))
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




class PyQt5GreeterMessage(QtWidgets.QFrame):

    def __init__(self, num_x, num_y):

        super().__init__()

        self._num_x = num_x
        self._num_y = num_y
        self._title = 'Get ready!'
        self._text = 'We will capture {} pictures!'.format(num_x * num_y)

        self.initFrame()


    def initFrame(self):

        self.setStyleSheet('background-color: black; color: white;')


    def paintEvent(self, event):

        painter = QtGui.QPainter(self)
        f = self.font()

        f.setPixelSize(self.height() / 5)
        painter.setFont(f)
        rect = QtCore.QRect(0, self.height() * 1 / 5, self.width(), self.height() * 3 / 10)
        painter.drawText(rect, QtCore.Qt.AlignCenter, self._title)

        f.setPixelSize(self.height() / 8)
        painter.setFont(f)
        rect = QtCore.QRect(0, self.height() * 3 / 5, self.width(), self.height() * 3 / 10)
        painter.drawText(rect, QtCore.Qt.AlignCenter, self._text)

        painter.end()



class PyQt5CountdownMessage(QtWidgets.QFrame):

    def __init__(self, time, action):
        
        super().__init__()

        self._step_size = 50
        self._counter = time * (1000 // self._step_size)
        self._action = action
        self._picture = None

        self.initFrame()
        self.initProgressBar(time)


    def initFrame(self):

        self.setStyleSheet('background-color: black; color: white;')


    def initProgressBar(self, time):

        self._bar = QRoundProgressBar()
        self._bar.setBarStyle(QRoundProgressBar.StyleLine)
        self._bar.setFixedSize(200, 200)

        self._bar.setDataPenWidth(7)
        self._bar.setOutlinePenWidth(10)

        self._bar.setDecimals(0)
        self._bar.setFormat('%v')

        self._bar.setRange(0, time)
        self._bar.setValue(time)


    def updateProgressBar(self):

        self._bar.setValue(self._counter / (1000 // self._step_size))


    @property
    def counter(self):
        
        return self._counter


    @property
    def picture(self):

        return self._picture

    
    @picture.setter
    def picture(self, pic):

        if not isinstance(pic, QtGui.QImage):
            raise ValueError('picture must be a QtGui.QImage')

        self._picture = pic


    def paintEvent(self, event):

        painter = QtGui.QPainter(self)

        if self._picture != None:
            pix = QtGui.QPixmap.fromImage(self._picture)
            pix = pix.scaled(self.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.FastTransformation)
            origin = ( (self.width() - pix.width()) // 2,
                       (self.height() - pix.height()) // 2 )
            painter.drawPixmap(QtCore.QPoint(*origin), pix)

        painter.end()

        offset = ( (self.width() - self._bar.width()) // 2, 
                   (self.height() - self._bar.height()) // 2 )
        self._bar.render(self, QtCore.QPoint(*offset), self._bar.visibleRegion(), QtWidgets.QWidget.DrawChildren)


    def showEvent(self, event):
    
        self._timer = self.startTimer(self._step_size)    
    

    def timerEvent(self, event):
    
        self._counter -= 1

        if self._counter == 0:
            self.killTimer(self._timer)
            self._action()
        else:
            self.updateProgressBar()
            self.update()



class PyQt5PoseMessage(QtWidgets.QFrame):

    def __init__(self):

        super().__init__()

        self.initFrame()


    def initFrame(self):

        self.setStyleSheet('background-color: black; color: white;')


    def paintEvent(self, event):

        painter = QtGui.QPainter(self)

        f = self.font()
        f.setPixelSize(self.height() / 3)
        painter.setFont(f)

        painter.drawText(event.rect(), QtCore.Qt.AlignCenter, 'Pose!')

        painter.end()



class PyQt5PictureMessage(QtWidgets.QFrame):

    def __init__(self, picture):
        
        super().__init__()

        self._picture = picture

        self.initFrame()


    def initFrame(self):

        self.setStyleSheet('background-color: black; color: white')


    def paintEvent(self, event):

        painter = QtGui.QPainter(self)

        if isinstance(self._picture, QtGui.QImage):
            pix = QtGui.QPixmap.fromImage(self._picture)
        else:
            pix = QtGui.QPixmap(self._picture)
        pix = pix.scaled(self.rect().size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

        origin = ( (self.rect().width() - pix.width()) // 2,
                   (self.rect().height() - pix.height()) // 2 )
        painter.drawPixmap(QtCore.QPoint(*origin), pix)

        painter.end()

