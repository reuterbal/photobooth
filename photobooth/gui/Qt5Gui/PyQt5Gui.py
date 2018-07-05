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

from .. import GuiState
from ..GuiSkeleton import GuiSkeleton
from ..GuiPostprocessor import GuiPostprocessor

from . import styles
from . import Frames
from . import Receiver


class PyQt5Gui(GuiSkeleton):

    def __init__(self, argv, config, camera_conn, worker_queue):

        super().__init__()

        self._cfg = config
        self._conn = camera_conn

        parser = argparse.ArgumentParser()
        parser.add_argument('--run', action='store_true',
                            help='omit welcome screen and run photobooth')
        parsed_args, unparsed_args = parser.parse_known_args()
        self._omit_welcome = parsed_args.run

        self._registerCallbacks()
        self._initUI(argv[:1] + unparsed_args)
        self._initReceiver()

        self._postprocess = GuiPostprocessor(self._cfg)

    def run(self):

        if self._omit_welcome:
            self._showStart(None)
        else:
            self._showWelcomeScreen()
        exit_code = self._app.exec_()
        self._gui = None
        return exit_code

    def close(self):

        self._gui.close()

    def restart(self):

        self._app.exit(123)

    def _registerCallbacks(self):

        self.idle = self._showIdle
        self.trigger = self._sendTrigger
        self.greeter = self._showGreeter
        self.countdown = self._showCountdown
        self.preview = self._showPreview
        self.pose = self._showPose
        self.assemble = self._showAssemble
        self.review = self._showReview
        self.teardown = self._sendTeardown
        self.error = self._showError

    def _initUI(self, argv):

        self._disableTrigger()

        style = self._cfg.get('Gui', 'style')
        filename = next((file for name, file in styles if name == style))

        with open(os.path.join(os.path.dirname(__file__), filename), 'r') as f:
            stylesheet = f.read()

        self._app = QtWidgets.QApplication(argv)
        self._app.setStyleSheet(stylesheet)
        self._gui = PyQt5MainWindow(self._cfg, self._handleKeypressEvent)

        fonts = ['photobooth/gui/Qt5Gui/fonts/AmaticSC-Regular.ttf',
                 'photobooth/gui/Qt5Gui/fonts/AmaticSC-Bold.ttf']
        self._fonts = QtGui.QFontDatabase()
        for font in fonts:
            self._fonts.addApplicationFont(font)

    def _initReceiver(self):

        self._receiver = Receiver.Receiver([self._conn])
        self._receiver.notify.connect(self.handleState)
        self._receiver.start()

    def _setWidget(self, widget):

        self._gui.setCentralWidget(widget)

    def _enableEscape(self):

        self._is_escape = True

    def _disableEscape(self):

        self._is_escape = False

    def _enableTrigger(self):

        self._is_trigger = True

    def _disableTrigger(self):

        self._is_trigger = False

    def _sendStart(self):

        self._conn.send('start')

    def _sendTrigger(self, state):

        self._conn.send('triggered')

    def _sendAck(self):

        self._conn.send('ack')

    def _sendCancel(self):

        self._conn.send('cancel')

    def _sendTeardown(self, state):

        self._conn.send('teardown')
        self._showWelcomeScreen()

    def _handleKeypressEvent(self, event):

        if self._is_escape and event.key() == QtCore.Qt.Key_Escape:
            self.handleState(GuiState.TeardownState())
        elif self._is_trigger and event.key() == QtCore.Qt.Key_Space:
            self.handleState(GuiState.TriggerState())

    def _showWelcomeScreen(self):

        self._disableTrigger()
        self._disableEscape()
        self._lastHandle = self._showWelcomeScreen
        self._setWidget(Frames.Start(self._showStart, self._showSetDateTime,
                                     self._showSettings, self.close))
        if QtWidgets.QApplication.overrideCursor() != 0:
            QtWidgets.QApplication.restoreOverrideCursor()

    def _showSetDateTime(self):

        self._disableTrigger()
        self._disableEscape()
        self._lastHandle = self._showSetDateTime
        self._setWidget(Frames.SetDateTime(self._showWelcomeScreen,
                                           self.restart))

    def _showSettings(self):

        self._disableTrigger()
        self._disableEscape()
        self._lastHandle = self._showSettings
        self._setWidget(Frames.Settings(self._cfg, self._showSettings,
                                        self._showWelcomeScreen, self.restart))

    def _showStart(self, state):

        self._disableTrigger()
        self._enableEscape()
        self._lastHandle = self._showWelcomeScreen
        self._sendStart()
        self._setWidget(Frames.WaitMessage('Starting the photobooth...'))
        if self._cfg.getBool('Gui', 'hide_cursor'):
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.BlankCursor)

    def _showIdle(self, state):

        self._enableEscape()
        self._enableTrigger()
        self._lastHandle = self._showIdle
        self._setWidget(Frames.IdleMessage())

    def _showGreeter(self, state):

        self._enableEscape()
        self._disableTrigger()

        num_pic = (self._cfg.getInt('Picture', 'num_x'),
                   self._cfg.getInt('Picture', 'num_y'))
        greeter_time = self._cfg.getInt('Photobooth', 'greeter_time') * 1000

        self._setWidget(Frames.GreeterMessage(*num_pic))
        QtCore.QTimer.singleShot(greeter_time, self._sendAck)

    def _showCountdown(self, state):

        countdown_time = self._cfg.getInt('Photobooth', 'countdown_time')
        self._setWidget(Frames.CountdownMessage(countdown_time, self._sendAck))

    def _showPreview(self, state):

        self._gui.centralWidget().picture = ImageQt.ImageQt(state.picture)
        self._gui.centralWidget().update()

    def _showPose(self, state):

        num_pic = (self._cfg.getInt('Picture', 'num_x'),
                   self._cfg.getInt('Picture', 'num_y'))
        self._setWidget(Frames.PoseMessage(state.num_picture, *num_pic))

    def _showAssemble(self, state):

        self._setWidget(Frames.WaitMessage('Processing picture...'))

    def _showReview(self, state):

        img = ImageQt.ImageQt(state.picture)
        review_time = self._cfg.getInt('Photobooth', 'display_time') * 1000
        self._setWidget(Frames.PictureMessage(img))
        QtCore.QTimer.singleShot(review_time, lambda:
                                 self._showPostprocess(state.picture))

    def _showPostprocess(self, picture):

        tasks = self._postprocess.get(picture)
        postproc_t = self._cfg.getInt('Photobooth', 'postprocess_time')

        Frames.PostprocessMessage(self._gui.centralWidget(), tasks,
                                  self._sendAck, postproc_t * 1000)

    def _showError(self, state):

        logging.error('%s: %s', state.title, state.message)

        def exec(*handles):
            for handle in handles:
                handle()

        MessageBox(self, MessageBox.RETRY, state.title, state.message,
                   exec(self._sendAck, self._lastState),
                   exec(self._sendCancel, self._showWelcomeScreen))


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
