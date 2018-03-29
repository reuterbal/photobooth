#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import Gui

from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLayout, QLineEdit, QMainWindow, QMessageBox, QPushButton, QVBoxLayout)
from PyQt5.QtGui import QImage, QPainter, QPixmap

class PyQt5Gui(Gui.Gui):

    def __init__(self, argv, config):

        super().__init__()

        global cfg
        cfg = config

        self._app = QApplication(argv)
        self._p = PyQt5MainWindow()


    def run(self, send, recv):

        receiver = PyQt5Receiver(recv)
        receiver.notify.connect(self.handleState)
        receiver.start()

        self._transport = send
        self._p.transport = send

        self.showStart()

        return self._app.exec_()


    def close(self):

        self._p.close()


    def handleKeypressEvent(self, event):

        if event.key() == Qt.Key_Escape:
            self.showStart()
        elif event.key() == Qt.Key_Space:
            self._p.handleKeypressEvent = lambda event : None
            self._transport.send('triggered')


    def handleState(self, state):

        if not isinstance(state, Gui.GuiState):
            raise ValueError('Invalid data received')

        if isinstance(state, Gui.IdleState):
            self.showIdle()
        elif isinstance(state, Gui.PoseState):
            self._p.setCentralWidget(PyQt5PictureMessage('Pose!'))
        elif isinstance(state, Gui.PreviewState):
            img = QImage(state.picture, state.picture.shape[1], state.picture.shape[0], QImage.Format_RGB888)
            self._p.setCentralWidget(PyQt5PictureMessage(state.message, img))
        elif isinstance(state, Gui.PictureState):
            img = QImage(state.picture, state.picture.shape[1], state.picture.shape[0], QImage.Format_RGB888)
            self._p.setCentralWidget(PyQt5PictureMessage('', QPixmap.fromImage(img)))
        else:
            raise ValueError('Unknown state')


    def showStart(self):

        self._p.handleKeypressEvent = lambda event : None
        self._p.setCentralWidget(PyQt5Start(self))


    def showSettings(self):

        self._p.handleKeypressEvent = lambda event : None
        self._p.setCentralWidget(PyQt5Settings(self))


    def showIdle(self):

        self._p.handleKeypressEvent = self.handleKeypressEvent
        self._p.setCentralWidget(PyQt5PictureMessage('Hit the button!', 'homer.jpg'))


class PyQt5Receiver(QThread):

    notify = pyqtSignal(object)

    def __init__(self, transport):

        super().__init__()

        self._transport = transport


    def handle(self, state):

        self.notify.emit(state)


    def run(self):

        while True:
            try:
                state = self._transport.recv()
            except EOFError:
                break
            else:
                self.handle(state)



class PyQt5MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.handleKeypressEvent = lambda event : None

        self.initUI()


    @property
    def transport(self):

        return self._transport


    @transport.setter
    def transport(self, new_transport):

        if not hasattr(new_transport, 'send'):
            raise ValueError('PyQt5MainWindow.transport must provide send()')

        self._transport = new_transport

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


    def showMessage(self, message, picture=None):

        content = PyQt5PictureMessage(message, picture)
        self.setCentralWidget(content)


    def closeEvent(self, e):

        reply = QMessageBox.question(self, 'Confirmation', "Quit Photobooth?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.transport.close()
            e.accept()
        else:
            e.ignore()


    def keyPressEvent(self, event):

        self.handleKeypressEvent(event)




class PyQt5Start(QFrame):

    def __init__(self, gui):
        
        super().__init__()

        self.initFrame(gui)


    def initFrame(self, gui):

        grid = QGridLayout()
        grid.setSpacing(100)
        self.setLayout(grid)

        btnStart = QPushButton('Start Photobooth')
        btnStart.resize(btnStart.sizeHint())
        btnStart.clicked.connect(gui.showIdle)
        grid.addWidget(btnStart, 0, 0)

        btnSettings = QPushButton('Settings')
        btnSettings.resize(btnSettings.sizeHint())
        btnSettings.clicked.connect(gui.showSettings)
        grid.addWidget(btnSettings, 0, 1)

        btnQuit = QPushButton('Quit')
        btnQuit.resize(btnQuit.sizeHint())
        btnQuit.clicked.connect(gui.close)
        grid.addWidget(btnQuit, 0, 2)



class PyQt5Settings(QFrame):

    def __init__(self, gui):
        
        super().__init__()

        self._gui = gui

        self.initFrame()


    def initFrame(self):

        self._value_widgets = {}

        grid = QGridLayout()
        grid.addWidget(self.createGuiSettings(), 0, 0)
        grid.addWidget(self.createGpioSettings(), 1, 0)
        grid.addWidget(self.createCameraSettings(), 0, 1)

        layout = QVBoxLayout()
        layout.addLayout(grid)
        layout.addStretch(1)
        layout.addWidget(self.createButtons())
        self.setLayout(layout)


    def createGuiSettings(self):

        global cfg

        self._value_widgets['Gui'] = {}
        self._value_widgets['Gui']['fullscreen'] = QCheckBox('Enable fullscreen')
        if cfg.getBool('Gui', 'fullscreen'):
            self._value_widgets['Gui']['fullscreen'].toggle()
        self._value_widgets['Gui']['width'] = QLineEdit(cfg.get('Gui', 'width'))
        self._value_widgets['Gui']['height'] = QLineEdit(cfg.get('Gui', 'height'))

        layout = QFormLayout()
        layout.addRow(self._value_widgets['Gui']['fullscreen'])
        layout.addRow(QLabel('Width:'), self._value_widgets['Gui']['width'])
        layout.addRow(QLabel('Height:'), self._value_widgets['Gui']['height'])

        widget = QGroupBox('Interface settings (restart required)')
        widget.setLayout(layout)
        return widget


    def createGpioSettings(self):

        global cfg

        self._value_widgets['Gpio'] = {}
        self._value_widgets['Gpio']['enable'] = QCheckBox('Enable GPIO (restart required)')
        if cfg.getBool('Gpio', 'enable'):
            self._value_widgets['Gpio']['enable'].toggle()
        self._value_widgets['Gpio']['exit_channel'] = QLineEdit(cfg.get('Gpio', 'exit_channel'))
        self._value_widgets['Gpio']['trigger_channel'] = QLineEdit(cfg.get('Gpio', 'trigger_channel'))
        self._value_widgets['Gpio']['lamp_channel'] = QLineEdit(cfg.get('Gpio', 'lamp_channel'))

        layout = QFormLayout()
        layout.addRow(self._value_widgets['Gpio']['enable'])
        layout.addRow(QLabel('Exit channel:'), self._value_widgets['Gpio']['exit_channel'])
        layout.addRow(QLabel('Trigger channel'), self._value_widgets['Gpio']['trigger_channel'])
        layout.addRow(QLabel('Lamp channel'), self._value_widgets['Gpio']['lamp_channel'])

        widget = QGroupBox('GPIO settings')
        widget.setLayout(layout)
        return widget


    def createCameraSettings(self):

        global cfg

        wrapper = QComboBox()
        wrapper.addItem('command line')
        wrapper.addItem('piggyphoto')
        wrapper.addItem('gphoto2-cffi')

        current_wrapper = cfg.get('Camera', 'gphoto2_wrapper')
        if current_wrapper == 'commandline':
            wrapper.setCurrentIndex(0)
        elif current_wrapper == 'piggyphoto':
            wrapper.setCurrentIndex(1)
        elif current_wrapper == 'gphoto2-cffi':
            wrapper.setCurrentIndex(2)
        else:
            wrapper.setCurrentIndex(-1)

        self._value_widgets['Camera'] = {}
        self._value_widgets['Camera']['gphoto2_wrapper'] = wrapper

        layout = QFormLayout()
        layout.addRow(QLabel('gPhoto2 wrapper:'), self._value_widgets['Camera']['gphoto2_wrapper'])

        widget = QGroupBox('Camera settings')
        widget.setLayout(layout)
        return widget


    def createButtons(self):

        layout = QHBoxLayout()
        layout.addStretch(1)

        btnSave = QPushButton('Save')
        btnSave.resize(btnSave.sizeHint())
        btnSave.clicked.connect(self.storeConfig)
        layout.addWidget(btnSave)

        btnCancel = QPushButton('Cancel')
        btnCancel.resize(btnCancel.sizeHint())
        btnCancel.clicked.connect(self._gui.showStart)
        layout.addWidget(btnCancel)

        btnRestore = QPushButton('Restore defaults')
        btnRestore.resize(btnRestore.sizeHint())
        btnRestore.clicked.connect(self.restoreDefaults)
        layout.addWidget(btnRestore)

        widget = QGroupBox()
        widget.setLayout(layout)
        return widget


    def storeConfig(self):

        global cfg

        cfg.set('Gui', 'fullscreen', str(self._value_widgets['Gui']['fullscreen'].isChecked()))
        cfg.set('Gui', 'width', self._value_widgets['Gui']['width'].text())
        cfg.set('Gui', 'height', self._value_widgets['Gui']['height'].text())

        cfg.set('Gpio', 'enable', str(self._value_widgets['Gpio']['enable'].isChecked()))
        cfg.set('Gpio', 'exit_channel', self._value_widgets['Gpio']['exit_channel'].text())
        cfg.set('Gpio', 'trigger_channel', self._value_widgets['Gpio']['trigger_channel'].text())
        cfg.set('Gpio', 'lamp_channel', self._value_widgets['Gpio']['lamp_channel'].text())

        wrapper_idx2val = [ 'commandline', 'piggyphoto', 'gphoto2-cffi' ]
        cfg.set('Camera', 'gphoto2_wrapper', wrapper_idx2val[self._value_widgets['Camera']['gphoto2_wrapper'].currentIndex()])

        cfg.write()
        self._gui.showStart()


    def restoreDefaults(self):

        global cfg

        cfg.defaults()
        self._gui.showSettings()



class PyQt5PictureMessage(QFrame):

    def __init__(self, message, picture=None):
        
        super().__init__()

        self._message = message
        self._picture = picture

        self.initFrame()


    def initFrame(self):

        self.setStyleSheet('background-color: white;')


    def paintEvent(self, event):

        painter = QPainter()
        painter.begin(self)

        if self._picture != None:
            pix = QPixmap(self._picture).scaled(self.rect().size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(pix.rect(), pix, pix.rect())

        painter.drawText(event.rect(), Qt.AlignCenter, self._message)
        painter.end()
