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

import logging
import os
import subprocess
import sys

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from .. import modules
from ... import camera
from ... import printer

from . import Widgets
from . import styles


class Start(QtWidgets.QFrame):

    def __init__(self, start_action, set_date_action, settings_action,
                 exit_action):

        super().__init__()

        self.initFrame(start_action, set_date_action, settings_action,
                       exit_action)

    def initFrame(self, start_action, set_date_action, settings_action,
                  exit_action):

        btnStart = QtWidgets.QPushButton('Start photobooth')
        btnStart.clicked.connect(start_action)

        btnSetDate = QtWidgets.QPushButton('Set date/time')
        btnSetDate.clicked.connect(set_date_action)

        btnSettings = QtWidgets.QPushButton('Settings')
        btnSettings.clicked.connect(settings_action)

        btnQuit = QtWidgets.QPushButton('Quit')
        btnQuit.clicked.connect(exit_action)

        btnLay = QtWidgets.QHBoxLayout()
        btnLay.addWidget(btnStart)
        btnLay.addWidget(btnSetDate)
        btnLay.addWidget(btnSettings)
        btnLay.addWidget(btnQuit)

        title = QtWidgets.QLabel('photobooth')

        url = 'https://github.com/reuterbal/photobooth'
        link = QtWidgets.QLabel('<a href="{0}">{0}</a>'.format(url))

        lay = QtWidgets.QVBoxLayout()
        lay.addWidget(title)
        lay.addLayout(btnLay)
        lay.addWidget(link)
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


class GreeterMessage(QtWidgets.QFrame):

    def __init__(self, num_x, num_y):

        super().__init__()

        self._title = 'Get ready!'
        if num_x * num_y > 1:
            self._text = ('Capturing {} pictures...'.format(num_x * num_y))
        else:
            self._text = 'Starting the countdown...'

    def _paintMessage(self, painter):

        f = self.font()

        f.setPixelSize(self.height() / 5)
        painter.setFont(f)
        rect = QtCore.QRect(0, self.height() * 1 / 5,
                            self.width(), self.height() * 3 / 10)
        painter.drawText(rect, QtCore.Qt.AlignCenter, self._title)

        f.setPixelSize(self.height() / 8)
        painter.setFont(f)
        rect = QtCore.QRect(0, self.height() * 3 / 5,
                            self.width(), self.height() * 3 / 10)
        painter.drawText(rect, QtCore.Qt.AlignCenter, self._text)

    def paintEvent(self, event):

        painter = QtGui.QPainter(self)
        self._paintMessage(painter)
        painter.end()


class PoseMessage(QtWidgets.QFrame):

    def __init__(self, num_picture, num_x, num_y):

        super().__init__()

        self._title = 'Pose!'
        if num_x * num_y > 1:
            self._text = 'Picture {} of {}...'.format(num_picture,
                                                      num_x * num_y)
        else:
            self._text = 'Taking a photo...'

    def _paintMessage(self, painter):

        f = self.font()

        f.setPixelSize(self.height() / 5)
        painter.setFont(f)
        rect = QtCore.QRect(0, self.height() * 1 / 5,
                            self.width(), self.height() * 3 / 10)
        painter.drawText(rect, QtCore.Qt.AlignCenter, self._title)

        f.setPixelSize(self.height() / 8)
        painter.setFont(f)
        rect = QtCore.QRect(0, self.height() * 3 / 5,
                            self.width(), self.height() * 3 / 10)
        painter.drawText(rect, QtCore.Qt.AlignCenter, self._text)

    def paintEvent(self, event):

        painter = QtGui.QPainter(self)
        self._paintMessage(painter)
        painter.end()


class PictureMessage(QtWidgets.QFrame):

    def __init__(self, picture):

        super().__init__()

        self._picture = picture

    def _paintPicture(self, painter):

        if isinstance(self._picture, QtGui.QImage):
            pix = QtGui.QPixmap.fromImage(self._picture)
        else:
            pix = QtGui.QPixmap(self._picture)
        pix = pix.scaled(self.rect().size(), QtCore.Qt.KeepAspectRatio,
                         QtCore.Qt.SmoothTransformation)

        origin = ((self.rect().width() - pix.width()) // 2,
                  (self.rect().height() - pix.height()) // 2)
        painter.drawPixmap(QtCore.QPoint(*origin), pix)

    def paintEvent(self, event):

        painter = QtGui.QPainter(self)
        self._paintPicture(painter)
        painter.end()


class WaitMessage(QtWidgets.QFrame):

    def __init__(self, message):

        super().__init__()

        self._message = message
        self._clock = Widgets.SpinningWaitClock()

    def showEvent(self, event):

        self.startTimer(100)

    def timerEvent(self, event):

        self._clock.value += 1
        self.update()

    def _paintMessage(self, painter):

        f = self.font()
        f.setPixelSize(self.height() / 8)
        painter.setFont(f)

        rect = QtCore.QRect(0, self.height() * 3 / 5, self.width(),
                            self.height() * 3 / 10)
        painter.drawText(rect, QtCore.Qt.AlignCenter, self._message)

    def paintEvent(self, event):

        offset = ((self.width() - self._clock.width()) // 2,
                  (self.height() - self._clock.height()) // 2)

        painter = QtGui.QPainter(self)
        self._paintMessage(painter)
        self._clock.render(painter, QtCore.QPoint(*offset),
                           self._clock.visibleRegion(),
                           QtWidgets.QWidget.DrawChildren)
        painter.end()


class CountdownMessage(QtWidgets.QFrame):

    def __init__(self, time, action):

        super().__init__()

        self._step_size = 50
        self._value = time * (1000 // self._step_size)
        self._action = action
        self._picture = None

        self._initProgressBar(time)

    @property
    def value(self):

        return self._value

    @value.setter
    def value(self, value):

        self._value = value

    @property
    def picture(self):

        return self._picture

    @picture.setter
    def picture(self, picture):

        if not isinstance(picture, QtGui.QImage):
            raise ValueError('picture must be a QtGui.QImage')

        self._picture = picture

    def _initProgressBar(self, time):

        self._bar = Widgets.RoundProgressBar(0, time, time)
        self._bar.setFixedSize(200, 200)

    def _updateProgressBar(self):

        self._bar.value = self._value / (1000 // self._step_size)

    def showEvent(self, event):

        self._timer = self.startTimer(self._step_size)

    def timerEvent(self, event):

        self.value -= 1

        if self.value == 0:
            self.killTimer(self._timer)
            self._action()
        else:
            self._updateProgressBar()
            self.update()

    def paintEvent(self, event):

        painter = QtGui.QPainter(self)

        # background image
        if self.picture is not None:

            pix = QtGui.QPixmap.fromImage(self.picture)
            pix = pix.scaled(self.size(), QtCore.Qt.KeepAspectRatio,
                             QtCore.Qt.FastTransformation)
            origin = ((self.width() - pix.width()) // 2,
                      (self.height() - pix.height()) // 2)
            painter.drawPixmap(QtCore.QPoint(*origin), pix)

        offset = ((self.width() - self._bar.width()) // 2,
                  (self.height() - self._bar.height()) // 2)
        self._bar.render(painter, QtCore.QPoint(*offset),
                         self._bar.visibleRegion(),
                         QtWidgets.QWidget.DrawChildren)

        painter.end()


class SetDateTime(QtWidgets.QFrame):

    def __init__(self, cancel_action, restart_action):

        super().__init__()

        self._cancelAction = cancel_action
        self._restartAction = restart_action

        self.initFrame()

    def initFrame(self):

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.createForm())
        layout.addStretch(1)
        layout.addWidget(self.createButtons())
        self.setLayout(layout)

    def createForm(self):

        self._date_widget = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
        self._date_widget.setCalendarPopup(True)

        self._time_widget = QtWidgets.QTimeEdit(QtCore.QTime.currentTime())

        layout = QtWidgets.QFormLayout()
        layout.addRow('Date:', self._date_widget)
        layout.addRow('Time:', self._time_widget)

        widget = QtWidgets.QGroupBox()
        widget.setTitle('Set system date and time:')
        widget.setLayout(layout)
        return widget

    def createButtons(self):

        layout = QtWidgets.QHBoxLayout()
        layout.addStretch(1)

        btnSave = QtWidgets.QPushButton('Save and restart')
        btnSave.clicked.connect(self.saveAndRestart)
        layout.addWidget(btnSave)

        btnCancel = QtWidgets.QPushButton('Cancel')
        btnCancel.clicked.connect(self._cancelAction)
        layout.addWidget(btnCancel)

        widget = QtWidgets.QGroupBox()
        widget.setLayout(layout)
        return widget

    def saveAndRestart(self):

        if os.name != 'posix':
            raise NotImplementedError(('Setting time/date not yet implemented '
                                       'for OS type "{}"'.format(os.name)))

        date = self._date_widget.date()
        time = self._time_widget.time()
        datetime = '{:04d}{:02d}{:02d} {:02d}:{:02d}'.format(date.year(),
                                                             date.month(),
                                                             date.day(),
                                                             time.hour(),
                                                             time.minute())
        logging.info(['sudo', '-A', 'date', '-s', datetime])
        logging.info('Setting date to "{}"'.format(datetime))

        try:
            subprocess.run(['sudo', '-A', 'date', '-s', datetime],
                           stderr=subprocess.PIPE).check_returncode()
        except subprocess.CalledProcessError as e:
            cmd = ' '.join(e.cmd)
            msg = e.stderr.decode(sys.stdout.encoding)
            logging.error('Failed to execute "{}": "{}"'.format(cmd, msg))

        self._restartAction()


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

        width = QtWidgets.QSpinBox()
        width.setRange(100, 999999)
        width.setValue(self._cfg.getInt('Gui', 'width'))
        self.add('Gui', 'width', width)

        height = QtWidgets.QSpinBox()
        height.setRange(100, 999999)
        height.setValue(self._cfg.getInt('Gui', 'height'))
        self.add('Gui', 'height', height)

        cursor = QtWidgets.QCheckBox()
        cursor.setChecked(self._cfg.getBool('Gui', 'hide_cursor'))
        self.add('Gui', 'hide_cursor', cursor)

        style = self.createModuleComboBox(styles,
                                          self._cfg.get('Gui', 'style'))
        self.add('Gui', 'style', style)

        lay_size = QtWidgets.QHBoxLayout()
        lay_size.addWidget(width)
        lay_size.addWidget(QtWidgets.QLabel('x'))
        lay_size.addWidget(height)

        layout = QtWidgets.QFormLayout()
        layout.addRow('Enable fullscreen:', fullscreen)
        layout.addRow('Gui module:', module)
        layout.addRow('Window size [px]:', lay_size)
        layout.addRow('Hide cursor:', cursor)
        layout.addRow('Appearance:', style)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        return widget

    def createPhotoboothSettings(self):

        self.init('Photobooth')

        preview = QtWidgets.QCheckBox()
        preview.setChecked(self._cfg.getBool('Photobooth', 'show_preview'))
        self.add('Photobooth', 'show_preview', preview)

        greet_time = QtWidgets.QSpinBox()
        greet_time.setRange(0, 1000)
        greet_time.setValue(self._cfg.getInt('Photobooth', 'greeter_time'))
        self.add('Photobooth', 'greeter_time', greet_time)

        count_time = QtWidgets.QSpinBox()
        count_time.setRange(0, 1000)
        count_time.setValue(self._cfg.getInt('Photobooth', 'countdown_time'))
        self.add('Photobooth', 'countdown_time', count_time)

        displ_time = QtWidgets.QSpinBox()
        displ_time.setRange(0, 1000)
        displ_time.setValue(self._cfg.getInt('Photobooth', 'display_time'))
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

        num_x = QtWidgets.QSpinBox()
        num_x.setRange(1, 99)
        num_x.setValue(self._cfg.getInt('Picture', 'num_x'))
        self.add('Picture', 'num_x', num_x)
        
        num_y = QtWidgets.QSpinBox()
        num_y.setRange(1, 99)
        num_y.setValue(self._cfg.getInt('Picture', 'num_y'))
        self.add('Picture', 'num_y', num_y)

        size_x = QtWidgets.QSpinBox()
        size_x.setRange(1, 999999)
        size_x.setValue(self._cfg.getInt('Picture', 'size_x'))
        self.add('Picture', 'size_x', size_x)
        
        size_y = QtWidgets.QSpinBox()
        size_y.setRange(1, 999999)
        size_y.setValue(self._cfg.getInt('Picture', 'size_y'))
        self.add('Picture', 'size_y', size_y)

        min_dist_x = QtWidgets.QSpinBox()
        min_dist_x.setRange(0, 999999)
        min_dist_x.setValue(self._cfg.getInt('Picture', 'min_dist_x'))
        self.add('Picture', 'min_dist_x', min_dist_x)

        min_dist_y = QtWidgets.QSpinBox()
        min_dist_y.setRange(0, 999999)
        min_dist_y.setValue(self._cfg.getInt('Picture', 'min_dist_y'))
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
            basedir.setText(dialog(self, 'Select directory',
                                   os.path.expanduser('~'),
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

        exit_pin = QtWidgets.QSpinBox()
        exit_pin.setRange(1, 40)
        exit_pin.setValue(self._cfg.getInt('Gpio', 'exit_pin'))
        self.add('Gpio', 'exit_pin', exit_pin)

        trig_pin = QtWidgets.QSpinBox()
        trig_pin.setRange(1, 40)
        trig_pin.setValue(self._cfg.getInt('Gpio', 'trigger_pin'))
        self.add('Gpio', 'trigger_pin', trig_pin)

        lamp_pin = QtWidgets.QSpinBox()
        lamp_pin.setRange(1, 40)
        lamp_pin.setValue(self._cfg.getInt('Gpio', 'lamp_pin'))
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

        width = QtWidgets.QSpinBox()
        width.setRange(0, 999999)
        width.setValue(self._cfg.getInt('Printer', 'width'))
        height = QtWidgets.QSpinBox()
        height.setRange(0, 999999)
        height.setValue(self._cfg.getInt('Printer', 'height'))
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
        self._cfg.set('Gui', 'style',
                      styles[self.get('Gui', 'style').currentIndex()][0])

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
