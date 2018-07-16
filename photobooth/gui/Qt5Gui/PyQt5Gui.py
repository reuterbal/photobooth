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

import argparse
import logging
import os

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from PIL import ImageQt

from ...StateMachine import GuiEvent, TeardownEvent
from ...Threading import Workers

from ..GuiSkeleton import GuiSkeleton
from ..GuiPostprocessor import GuiPostprocessor

from . import styles
from . import Frames
from . import Receiver


class PyQt5Gui(GuiSkeleton):

    def __init__(self, argv, config, communicator):

        super().__init__(communicator)

        self._cfg = config

        is_start, unparsed_args = self._parseArgs()
        self._initUI(argv[:1] + unparsed_args)
        self._initReceiver()

        self._picture = None
        self._postprocess = GuiPostprocessor(self._cfg)

        if is_start:
            self._comm.send(Workers.MASTER, GuiEvent('start'))

    def run(self):

        exit_code = self._app.exec_()
        self._gui = None
        return exit_code

    def _parseArgs(self):

        # Add parameter for direct startup
        parser = argparse.ArgumentParser()
        parser.add_argument('--run', action='store_true',
                            help='omit welcome screen and run photobooth')
        parsed_args, unparsed_args = parser.parse_known_args()

        return (parsed_args.run, unparsed_args)

    def _initUI(self, argv):

        self._disableTrigger()

        # Load stylesheet
        style = self._cfg.get('Gui', 'style')
        filename = next((file for name, file in styles if name == style))
        with open(os.path.join(os.path.dirname(__file__), filename), 'r') as f:
            stylesheet = f.read()

        # Create application and main window
        self._app = QtWidgets.QApplication(argv)
        self._app.setStyleSheet(stylesheet)
        self._gui = PyQt5MainWindow(self._cfg, self._handleKeypressEvent)

        # Load additional fonts
        fonts = ['photobooth/gui/Qt5Gui/fonts/AmaticSC-Regular.ttf',
                 'photobooth/gui/Qt5Gui/fonts/AmaticSC-Bold.ttf']
        self._fonts = QtGui.QFontDatabase()
        for font in fonts:
            self._fonts.addApplicationFont(font)

    def _initReceiver(self):

        # Create receiver thread
        self._receiver = Receiver.Receiver(self._comm)
        self._receiver.notify.connect(self.handleState)
        self._receiver.start()

    def _enableEscape(self):

        self._is_escape = True

    def _disableEscape(self):

        self._is_escape = False

    def _enableTrigger(self):

        self._is_trigger = True

    def _disableTrigger(self):

        self._is_trigger = False

    def _setWidget(self, widget):

        self._gui.setCentralWidget(widget)

    def close(self):

        if self._gui.close():
            self._comm.send(Workers.MASTER, TeardownEvent(TeardownEvent.EXIT))

    def teardown(self, state):

        if state.target == TeardownEvent.WELCOME:
            self._comm.send(Workers.MASTER, GuiEvent('welcome'))
        elif state.target in (TeardownEvent.EXIT, TeardownEvent.RESTART):
            self._app.exit(0)

    def showError(self, state):

        logging.error('%s: %s', state.title, state.message)

        MessageBox(self, MessageBox.RETRY, state.title, state.message,
                   lambda: self._comm.send(Workers.MASTER, GuiEvent('retry')),
                   lambda: self._comm.send(Workers.MASTER, GuiEvent('abort')))

    def showWelcome(self, state):

        self._disableTrigger()
        self._disableEscape()
        self._setWidget(Frames.Welcome(
            lambda: self._comm.send(Workers.MASTER, GuiEvent('start')),
            self._showSetDateTime, self._showSettings, self.close))
        if QtWidgets.QApplication.overrideCursor() != 0:
            QtWidgets.QApplication.restoreOverrideCursor()

    def showStartup(self, state):

        self._disableTrigger()
        self._enableEscape()
        self._setWidget(Frames.WaitMessage('Starting the photobooth...'))
        if self._cfg.getBool('Gui', 'hide_cursor'):
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.BlankCursor)

    def showIdle(self, state):

        self._enableEscape()
        self._enableTrigger()
        self._setWidget(Frames.IdleMessage(
            lambda: self._comm.send(Workers.MASTER, GuiEvent('trigger'))))

    def showGreeter(self, state):

        self._enableEscape()
        self._disableTrigger()

        num_pic = (self._cfg.getInt('Picture', 'num_x'),
                   self._cfg.getInt('Picture', 'num_y'))
        greeter_time = self._cfg.getInt('Photobooth', 'greeter_time') * 1000

        self._setWidget(Frames.GreeterMessage(
            *num_pic,
            lambda: self._comm.send(Workers.MASTER, GuiEvent('countdown'))))
        QtCore.QTimer.singleShot(
            greeter_time,
            lambda: self._comm.send(Workers.MASTER, GuiEvent('countdown')))

    def showCountdown(self, state):

        countdown_time = self._cfg.getInt('Photobooth', 'countdown_time')
        self._setWidget(Frames.CountdownMessage(
            countdown_time,
            lambda: self._comm.send(Workers.MASTER, GuiEvent('capture'))))

    def updateCountdown(self, event):

        self._gui.centralWidget().picture = ImageQt.ImageQt(event.picture)
        self._gui.centralWidget().update()

    def showCapture(self, state):

        num_pic = (self._cfg.getInt('Picture', 'num_x'),
                   self._cfg.getInt('Picture', 'num_y'))
        self._setWidget(Frames.CaptureMessage(state.num_picture, *num_pic))

    def showAssemble(self, state):

        self._setWidget(Frames.WaitMessage('Processing picture...'))

    def showReview(self, state):

        self._picture = ImageQt.ImageQt(state.picture)
        review_time = self._cfg.getInt('Photobooth', 'display_time') * 1000
        self._setWidget(Frames.PictureMessage(self._picture))
        QtCore.QTimer.singleShot(
            review_time,
            lambda: self._comm.send(Workers.MASTER, GuiEvent('postprocess')))

    def showPostprocess(self, state):

        tasks = self._postprocess.get(self._picture)
        postproc_t = self._cfg.getInt('Photobooth', 'postprocess_time')

        Frames.PostprocessMessage(
            self._gui.centralWidget(), tasks,
            lambda: self._comm.send(Workers.MASTER, GuiEvent('idle')),
            postproc_t * 1000)

    def _handleKeypressEvent(self, event):

        if self._is_escape and event.key() == QtCore.Qt.Key_Escape:
            self._comm.send(Workers.MASTER,
                            TeardownEvent(TeardownEvent.WELCOME))
        elif self._is_trigger and event.key() == QtCore.Qt.Key_Space:
            self._comm.send(Workers.MASTER, GuiEvent('trigger'))

    def _showSetDateTime(self):

        self._disableTrigger()
        self._disableEscape()
        self._setWidget(Frames.SetDateTime(
            self.showWelcome,
            lambda: self._comm.send(Workers.MASTER,
                                    TeardownEvent(TeardownEvent.RESTART))))

    def _showSettings(self):

        self._disableTrigger()
        self._disableEscape()
        self._setWidget(Frames.Settings(
            self._cfg, self._showSettings, self.showWelcome,
            lambda: self._comm.send(Workers.MASTER,
                                    TeardownEvent(TeardownEvent.RESTART))))


class PyQt5MainWindow(QtWidgets.QMainWindow):

    def __init__(self, config, keypress_handler):

        super().__init__()

        self._cfg = config
        self._handle_key = keypress_handler
        self._initUI()

    def _initUI(self):

        self.setWindowTitle('Photobooth')

        if self._cfg.getBool('Gui', 'fullscreen'):
            self.showFullScreen()
        else:
            self.setFixedSize(self._cfg.getInt('Gui', 'width'),
                              self._cfg.getInt('Gui', 'height'))
            self.show()

    def closeEvent(self, e):

        reply = QtWidgets.QMessageBox.question(self, 'Confirmation',
                                               "Quit Photobooth?",
                                               QtWidgets.QMessageBox.Yes |
                                               QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            e.accept()
        else:
            e.ignore()

    def keyPressEvent(self, event):

        self._handle_key(event)


class MessageBox(QtWidgets.QWidget):

    QUESTION = 1
    RETRY = 2
    INFORMATION = 3

    def __init__(self, parent, type, title, message, *handles):

        super().__init__(parent)

        if type == MessageBox.QUESTION:
            self.question(title, message, *handles)
        elif type == MessageBox.RETRY:
            self.retry(title, message, *handles)
        else:
            raise ValueError('Unknown type specified')

    def question(self, title, message, *handles):

        lbl_title = QtWidgets.QLabel(title)
        lbl_title.setObjectName('title')

        lbl_message = QtWidgets.QLabel(message)
        lbl_message.setObjectName('message')

        btn_yes = QtWidgets.QPushButton('Yes')
        btn_yes.clicked.connect(handles[0])

        btn_no = QtWidgets.QPushButton('No')
        btn_no.clicked.connect(handles[1])

        lay_buttons = QtWidgets.QHBoxLayout()
        lay_buttons.addWidget(btn_yes)
        lay_buttons.addWidget(btn_no)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_message)
        layout.addLayout(lay_buttons)
        self.setLayout(layout)

    def retry(self, title, message, *handles):

        lbl_title = QtWidgets.QLabel(title)
        lbl_title.setObjectName('title')

        lbl_message = QtWidgets.QLabel(message)
        lbl_message.setObjectName('message')

        btn_retry = QtWidgets.QPushButton('Retry')
        btn_retry.clicked.connect(handles[0])

        btn_cancel = QtWidgets.QPushButton('Cancel')
        btn_cancel.clicked.connect(handles[1])

        lay_buttons = QtWidgets.QHBoxLayout()
        lay_buttons.addWidget(btn_retry)
        lay_buttons.addWidget(btn_cancel)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_message)
        layout.addLayout(lay_buttons)
        self.setLayout(layout)
