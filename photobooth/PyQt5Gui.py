#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLayout, QLineEdit, QMainWindow, QMessageBox, QPushButton, QVBoxLayout)

class PyQt5Gui(QMainWindow):

    def __init__(self):

        super().__init__()

        self.initUI()


    def initUI(self):

        global cfg

        self.showStart()
        self.setWindowTitle('Photobooth')

        if cfg.getBool('Gui', 'fullscreen'):
            self.showFullScreen()
        else:
            self.resize(cfg.getInt('Gui', 'width'), 
                        cfg.getInt('Gui', 'height'))
            self.show()


    def showStart(self):

        content = PyQt5Start(self)
        self.setCentralWidget(content)


    def showSettings(self):

        content = PyQt5Settings(self)
        self.setCentralWidget(content)


    def closeEvent(self, e):

        reply = QMessageBox.question(self, 'Confirmation', "Quit Photobooth?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            e.accept()
        else:
            e.ignore()


    def keyPressEvent(self, e):
        pass
        # if self.photobooth.status == Status.idle:
        #     if e.key() == Qt.Key_Escape:
        #         self.showStart()
            # elif e.key() == Qt.Key_Space:
            #     self.centralWidget().trigger()




class PyQt5Start(QFrame):

    def __init__(self, parent):
        
        super().__init__(parent)

        self.initFrame(parent)


    def initFrame(self, parent):

        grid = QGridLayout()
        grid.setSpacing(100)
        self.setLayout(grid)

        btnStart = QPushButton('Start Photobooth')
        btnStart.resize(btnStart.sizeHint())
        # btnStart.clicked.connect(parent.showPhotobooth)
        grid.addWidget(btnStart, 0, 0)

        btnSettings = QPushButton('Settings')
        btnSettings.resize(btnSettings.sizeHint())
        btnSettings.clicked.connect(parent.showSettings)
        grid.addWidget(btnSettings, 0, 1)

        btnQuit = QPushButton('Quit')
        btnQuit.resize(btnQuit.sizeHint())
        btnQuit.clicked.connect(parent.close)
        grid.addWidget(btnQuit, 0, 2)



class PyQt5Settings(QFrame):

    def __init__(self, parent):
        
        super().__init__(parent)

        self._parent = parent
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
        btnCancel.clicked.connect(self._parent.showStart)
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
        self._parent.showStart()


    def restoreDefaults(self):

        global cfg

        cfg.defaults()
        self._parent.showSettings()


def run(argv, config):

    global cfg
    cfg = config

    app = QApplication(argv)
    p = PyQt5Gui()
    return app.exec_()
