#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os.path import expanduser

import math

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from .. import modules
from ... import camera
from ... import printer


class Start(QtWidgets.QFrame):

    def __init__(self, start_action, settings_action, exit_action):

        super().__init__()

        self.initFrame(start_action, settings_action, exit_action)

    def initFrame(self, start_action, settings_action, exit_action):

        btnStart = QtWidgets.QPushButton('Start Photobooth')
        btnStart.clicked.connect(start_action)

        btnSettings = QtWidgets.QPushButton('Settings')
        btnSettings.clicked.connect(settings_action)

        btnQuit = QtWidgets.QPushButton('Quit')
        btnQuit.clicked.connect(exit_action)

        lay = QtWidgets.QHBoxLayout()
        lay.addWidget(btnStart)
        lay.addWidget(btnSettings)
        lay.addWidget(btnQuit)
        self.setLayout(lay)


class IdleMessage(QtWidgets.QFrame):

    def __init__(self):

        super().__init__()

        self._message = 'Hit the button!'

    def _paintMessage(self, painter):

        f = self.font()
        f.setPixelSize(self.height() / 5)
        painter.setFont(f)

        rect = self.rect()
        painter.drawText(rect, QtCore.Qt.AlignCenter, self._message)

    def paintEvent(self, event):

        painter = QtGui.QPainter(self)
        self._paintMessage(painter)
        painter.end()


class WaitMessage(QtWidgets.QFrame):
    # With spinning wait clock, inspired by
    # https://wiki.python.org/moin/PyQt/A%20full%20widget%20waiting%20indicator

    def __init__(self, message):

        super().__init__()

        self._message = message

    def showEvent(self, event):

        self._counter = 0
        self.startTimer(100)

    def timerEvent(self, event):

        self._counter += 1
        self.update()

    def _paintMessage(self, painter):

        f = self.font()
        f.setPixelSize(self.height() / 8)
        painter.setFont(f)

        rect = QtCore.QRect(0, self.height() * 3 / 5,
                            self.width(), self.height() * 3 / 10)
        painter.drawText(rect, QtCore.Qt.AlignCenter, self._message)

    def _paintClock(self, painter):

        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))

        center = (self.width() / 2, self.height() / 2)

        dots = 8
        pos = self._counter % dots

        for i in range(dots):

            distance = (pos - i) % dots
            color = (distance + 1) / (dots + 1) * 255
            painter.setBrush(QtGui.QBrush(QtGui.QColor(color, color, color)))

            painter.drawEllipse(
                center[0] + 180 / dots * math.cos(2 * math.pi * i / dots) - 20,
                center[1] + 180 / dots * math.sin(2 * math.pi * i / dots) - 20,
                15, 15)

    def paintEvent(self, event):

        painter = QtGui.QPainter(self)
        self._paintMessage(painter)
        self._paintClock(painter)
        painter.end()


class Settings(QtWidgets.QFrame):

    def __init__(self, config, reload_action, cancel_action, restart_action):

        super().__init__()

        self._cfg = config
        self._reloadAction = reload_action
        self._cancelAction = cancel_action
        self._restartAction = restart_action

        self.initFrame()

    def init(self, category):

        self._widgets[category] = {}

    def add(self, category, key, value):

        self._widgets[category][key] = value

    def get(self, category, key):

        return self._widgets[category][key]

    def initFrame(self):

        self._widgets = {}

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.createTabs())
        layout.addStretch(1)
        layout.addWidget(self.createButtons())
        self.setLayout(layout)

    def createTabs(self):

        tabs = QtWidgets.QTabWidget()
        tabs.addTab(self.createGuiSettings(), 'Interface')
        tabs.addTab(self.createPhotoboothSettings(), 'Photobooth')
        tabs.addTab(self.createCameraSettings(), 'Camera')
        tabs.addTab(self.createPictureSettings(), 'Picture')
        tabs.addTab(self.createGpioSettings(), 'GPIO')
        tabs.addTab(self.createPrinterSettings(), 'Printer')
        return tabs

    def createButtons(self):

        layout = QtWidgets.QHBoxLayout()
        layout.addStretch(1)

        btnSave = QtWidgets.QPushButton('Save and restart')
        btnSave.clicked.connect(self.storeConfigAndRestart)
        layout.addWidget(btnSave)

        btnCancel = QtWidgets.QPushButton('Cancel')
        btnCancel.clicked.connect(self._cancelAction)
        layout.addWidget(btnCancel)

        btnRestore = QtWidgets.QPushButton('Restore defaults')
        btnRestore.clicked.connect(self.restoreDefaults)
        layout.addWidget(btnRestore)

        widget = QtWidgets.QGroupBox()
        widget.setLayout(layout)
        return widget

    def createModuleComboBox(self, module_list, current_module):

        cb = QtWidgets.QComboBox()
        for m in module_list:
            cb.addItem(m[0])

        idx = [x for x, m in enumerate(module_list) if m[0] == current_module]
        cb.setCurrentIndex(idx[0] if len(idx) > 0 else -1)

        return cb

    def createGuiSettings(self):

        self.init('Gui')

        fullscreen = QtWidgets.QCheckBox()
        fullscreen.setChecked(self._cfg.getBool('Gui', 'fullscreen'))
        self.add('Gui', 'fullscreen', fullscreen)

        module = self.createModuleComboBox(modules,
                                           self._cfg.get('Gui', 'module'))
        self.add('Gui', 'module', module)

        width = QtWidgets.QLineEdit(self._cfg.get('Gui', 'width'))
        height = QtWidgets.QLineEdit(self._cfg.get('Gui', 'height'))
        self.add('Gui', 'width', width)
        self.add('Gui', 'height', height)

        cursor = QtWidgets.QCheckBox()
        cursor.setChecked(self._cfg.getBool('Gui', 'hide_cursor'))
        self.add('Gui', 'hide_cursor', cursor)

        lay_size = QtWidgets.QHBoxLayout()
        lay_size.addWidget(width)
        lay_size.addWidget(QtWidgets.QLabel('x'))
        lay_size.addWidget(height)

        layout = QtWidgets.QFormLayout()
        layout.addRow('Enable fullscreen:', fullscreen)
        layout.addRow('Gui module:', module)
        layout.addRow('Window size [px]:', lay_size)
        layout.addRow('Hide cursor:', cursor)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        return widget

    def createPhotoboothSettings(self):

        self.init('Photobooth')

        preview = QtWidgets.QCheckBox()
        preview.setChecked(self._cfg.getBool('Photobooth', 'show_preview'))
        self.add('Photobooth', 'show_preview', preview)

        greet_time = QtWidgets.QLineEdit(self._cfg.get('Photobooth',
                                                       'greeter_time'))
        count_time = QtWidgets.QLineEdit(self._cfg.get('Photobooth',
                                                       'countdown_time'))
        displ_time = QtWidgets.QLineEdit(self._cfg.get('Photobooth',
                                                       'display_time'))
        self.add('Photobooth', 'greeter_time', greet_time)
        self.add('Photobooth', 'countdown_time', count_time)
        self.add('Photobooth', 'display_time', displ_time)

        layout = QtWidgets.QFormLayout()
        layout.addRow('Show preview during countdown:', preview)
        layout.addRow('Greeter time before countdown [s]:', greet_time)
        layout.addRow('Countdown time [s]:', count_time)
        layout.addRow('Picture display time [s]:', displ_time)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        return widget

    def createCameraSettings(self):

        self.init('Camera')

        module = self.createModuleComboBox(camera.modules,
                                           self._cfg.get('Camera', 'module'))
        self.add('Camera', 'module', module)

        layout = QtWidgets.QFormLayout()
        layout.addRow('Camera module:', module)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        return widget

    def createPictureSettings(self):

        self.init('Picture')

        num_x = QtWidgets.QLineEdit(self._cfg.get('Picture', 'num_x'))
        num_y = QtWidgets.QLineEdit(self._cfg.get('Picture', 'num_y'))
        self.add('Picture', 'num_x', num_x)
        self.add('Picture', 'num_y', num_y)

        size_x = QtWidgets.QLineEdit(self._cfg.get('Picture', 'size_x'))
        size_y = QtWidgets.QLineEdit(self._cfg.get('Picture', 'size_y'))
        self.add('Picture', 'size_x', size_x)
        self.add('Picture', 'size_y', size_y)

        min_dist_x = QtWidgets.QLineEdit(self._cfg.get('Picture',
                                         'min_dist_x'))
        min_dist_y = QtWidgets.QLineEdit(self._cfg.get('Picture',
                                         'min_dist_y'))
        self.add('Picture', 'min_dist_x', min_dist_x)
        self.add('Picture', 'min_dist_y', min_dist_y)

        basedir = QtWidgets.QLineEdit(self._cfg.get('Picture', 'basedir'))
        basename = QtWidgets.QLineEdit(self._cfg.get('Picture', 'basename'))
        self.add('Picture', 'basedir', basedir)
        self.add('Picture', 'basename', basename)

        lay_num = QtWidgets.QHBoxLayout()
        lay_num.addWidget(num_x)
        lay_num.addWidget(QtWidgets.QLabel('x'))
        lay_num.addWidget(num_y)

        lay_size = QtWidgets.QHBoxLayout()
        lay_size.addWidget(size_x)
        lay_size.addWidget(QtWidgets.QLabel('x'))
        lay_size.addWidget(size_y)

        lay_dist = QtWidgets.QHBoxLayout()
        lay_dist.addWidget(min_dist_x)
        lay_dist.addWidget(QtWidgets.QLabel('x'))
        lay_dist.addWidget(min_dist_y)

        def file_dialog():
            dialog = QtWidgets.QFileDialog.getExistingDirectory
            basedir.setText(dialog(self, 'Select directory', expanduser('~'),
                                   QtWidgets.QFileDialog.ShowDirsOnly))

        file_button = QtWidgets.QPushButton('Select directory')
        file_button.clicked.connect(file_dialog)

        lay_file = QtWidgets.QHBoxLayout()
        lay_file.addWidget(basedir)
        lay_file.addWidget(file_button)

        layout = QtWidgets.QFormLayout()
        layout.addRow('Number of shots per picture:', lay_num)
        layout.addRow('Size of assembled picture [px]:', lay_size)
        layout.addRow('Minimum distance between shots in picture [px]:',
                      lay_dist)
        layout.addRow('Output directory (strftime directives possible):',
                      lay_file)
        layout.addRow('Basename of files (strftime directives possible):',
                      basename)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        return widget

    def createGpioSettings(self):

        self.init('Gpio')

        enable = QtWidgets.QCheckBox()
        enable.setChecked(self._cfg.getBool('Gpio', 'enable'))
        self.add('Gpio', 'enable', enable)

        exit_pin = QtWidgets.QLineEdit(self._cfg.get('Gpio', 'exit_pin'))
        trig_pin = QtWidgets.QLineEdit(self._cfg.get('Gpio', 'trigger_pin'))
        lamp_pin = QtWidgets.QLineEdit(self._cfg.get('Gpio', 'lamp_pin'))
        self.add('Gpio', 'exit_pin', exit_pin)
        self.add('Gpio', 'trigger_pin', trig_pin)
        self.add('Gpio', 'lamp_pin', lamp_pin)

        layout = QtWidgets.QFormLayout()
        layout.addRow('Enable GPIO:', enable)
        layout.addRow('Exit button pin (BCM numbering):', exit_pin)
        layout.addRow('Trigger button pin (BCM numbering):', trig_pin)
        layout.addRow('Idle lamp pin (BCM numbering):', lamp_pin)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        return widget

    def createPrinterSettings(self):

        self.init('Printer')

        enable = QtWidgets.QCheckBox()
        enable.setChecked(self._cfg.getBool('Printer', 'enable'))
        self.add('Printer', 'enable', enable)

        module = self.createModuleComboBox(printer.modules,
                                           self._cfg.get('Printer', 'module'))
        self.add('Printer', 'module', module)

        width = QtWidgets.QLineEdit(self._cfg.get('Printer', 'width'))
        height = QtWidgets.QLineEdit(self._cfg.get('Printer', 'height'))
        self.add('Printer', 'width', width)
        self.add('Printer', 'height', height)

        lay_size = QtWidgets.QHBoxLayout()
        lay_size.addWidget(width)
        lay_size.addWidget(QtWidgets.QLabel('x'))
        lay_size.addWidget(height)

        layout = QtWidgets.QFormLayout()
        layout.addRow('Enable printing:', enable)
        layout.addRow('Module:', module)
        layout.addRow('Paper size [mm]:', lay_size)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        return widget

    def storeConfigAndRestart(self):

        self._cfg.set('Gui', 'fullscreen',
                      str(self.get('Gui', 'fullscreen').isChecked()))
        self._cfg.set('Gui', 'module',
                      modules[self.get('Gui', 'module').currentIndex()][0])
        self._cfg.set('Gui', 'width', self.get('Gui', 'width').text())
        self._cfg.set('Gui', 'height', self.get('Gui', 'height').text())
        self._cfg.set('Gui', 'hide_cursor',
                      str(self.get('Gui', 'hide_cursor').isChecked()))

        self._cfg.set('Photobooth', 'show_preview',
                      str(self.get('Photobooth', 'show_preview').isChecked()))
        self._cfg.set('Photobooth', 'greeter_time',
                      str(self.get('Photobooth', 'greeter_time').text()))
        self._cfg.set('Photobooth', 'countdown_time',
                      str(self.get('Photobooth', 'countdown_time').text()))
        self._cfg.set('Photobooth', 'display_time',
                      str(self.get('Photobooth', 'display_time').text()))

        self._cfg.set('Camera', 'module',
                      camera.modules[self.get('Camera',
                                              'module').currentIndex()][0])

        self._cfg.set('Picture', 'num_x', self.get('Picture', 'num_x').text())
        self._cfg.set('Picture', 'num_y', self.get('Picture', 'num_y').text())
        self._cfg.set('Picture', 'size_x',
                      self.get('Picture', 'size_x').text())
        self._cfg.set('Picture', 'size_y',
                      self.get('Picture', 'size_y').text())
        self._cfg.set('Picture', 'min_dist_x',
                      self.get('Picture', 'min_dist_x').text())
        self._cfg.set('Picture', 'min_dist_y',
                      self.get('Picture', 'min_dist_y').text())
        self._cfg.set('Picture', 'basedir',
                      self.get('Picture', 'basedir').text())
        self._cfg.set('Picture', 'basename',
                      self.get('Picture', 'basename').text())

        self._cfg.set('Gpio', 'enable',
                      str(self.get('Gpio', 'enable').isChecked()))
        self._cfg.set('Gpio', 'exit_pin', self.get('Gpio', 'exit_pin').text())
        self._cfg.set('Gpio', 'trigger_pin',
                      self.get('Gpio', 'trigger_pin').text())
        self._cfg.set('Gpio', 'lamp_pin', self.get('Gpio', 'lamp_pin').text())

        self._cfg.set('Printer', 'enable',
                      str(self.get('Printer', 'enable').isChecked()))
        self._cfg.set('Printer', 'module',
                      printer.modules[self.get('Printer',
                                               'module').currentIndex()][0])
        self._cfg.set('Printer', 'width', self.get('Printer', 'width').text())
        self._cfg.set('Printer', 'height',
                      self.get('Printer', 'height').text())

        self._cfg.write()
        self._restartAction()

    def restoreDefaults(self):

        self._cfg.defaults()
        self._reloadAction()
