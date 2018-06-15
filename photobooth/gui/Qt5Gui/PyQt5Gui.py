#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from PIL import ImageQt

from .. import GuiState
from ..GuiSkeleton import GuiSkeleton

from . import Frames
from . import Postprocessor
from . import Receiver


class PyQt5Gui(GuiSkeleton):

    def __init__(self, argv, config, camera_conn, worker_queue):

        super().__init__()

        self._cfg = config
        self._conn = camera_conn

        self._registerCallbacks()
        self._initUI(argv)
        self._initReceiver()

        self._postprocess = Postprocessor.Postprocessor(self._cfg)

    def run(self):

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

        self._app = QtWidgets.QApplication(argv)
        self._gui = PyQt5MainWindow(self._cfg, self._handleKeypressEvent)

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

    def _postprocessPicture(self, picture):

        self._postprocess.fill(picture)
        self._postprocess.work(MessageBox(self._gui))
        self._sendAck()

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
                   self._cfg.getInt('Picture', 'num_x'))
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
                   self._cfg.getInt('Picture', 'num_x'))
        self._setWidget(Frames.PoseMessage(state.num_picture, *num_pic))

    def _showAssemble(self, state):

        self._setWidget(Frames.WaitMessage('Processing picture...'))

    def _showReview(self, state):

        img = ImageQt.ImageQt(state.picture)
        review_time = self._cfg.getInt('Photobooth', 'display_time') * 1000
        self._setWidget(Frames.PictureMessage(img))
        QtCore.QTimer.singleShot(review_time, lambda:
                                 self._postprocessPicture(state.picture))

    def _showError(self, state):

        logging.error('%s: %s', state.title, state.message)
        reply = QtWidgets.QMessageBox.warning(self._gui, state.title,
                                              state.message,
                                              QtWidgets.QMessageBox.Close |
                                              QtWidgets.QMessageBox.Retry,
                                              QtWidgets.QMessageBox.Retry)
        if reply == QtWidgets.QMessageBox.Retry:
            self._sendAck()
            self._lastState()
        else:
            self._sendCancel()
            self._showWelcomeScreen()


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
            self.resize(self._cfg.getInt('Gui', 'width'),
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


class MessageBox:

    def __init__(self, parent):

        super().__init__()

        self._parent = parent

    def question(self, title, message):

        reply = QtWidgets.QMessageBox.question(self._parent, title, message,
                                               QtWidgets.QMessageBox.Yes |
                                               QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        return reply == QtWidgets.QMessageBox.Yes

    def information(self, title, message):

        QtWidgets.QMessageBox.information(self._parent, title, message,
                                          QtWidgets.QMessageBox.Ok)
