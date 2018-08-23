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


class Welcome(QtWidgets.QFrame):

    def __init__(self, start_action, set_date_action, settings_action,
                 exit_action):

        super().__init__()

        self.initFrame(start_action, set_date_action, settings_action,
                       exit_action)

    def initFrame(self, start_action, set_date_action, settings_action,
                  exit_action):

        btnStart = QtWidgets.QPushButton(_('Start photobooth'))
        btnStart.clicked.connect(start_action)

        btnSetDate = QtWidgets.QPushButton(_('Set date/time'))
        btnSetDate.clicked.connect(set_date_action)

        btnSettings = QtWidgets.QPushButton(_('Settings'))
        btnSettings.clicked.connect(settings_action)

        btnQuit = QtWidgets.QPushButton(_('Quit'))
        btnQuit.clicked.connect(exit_action)

        btnLay = QtWidgets.QHBoxLayout()
        btnLay.addWidget(btnStart)
        btnLay.addWidget(btnSetDate)
        btnLay.addWidget(btnSettings)
        btnLay.addWidget(btnQuit)

        title = QtWidgets.QLabel(_('photobooth'))

        url = 'https://github.com/reuterbal/photobooth'
        link = QtWidgets.QLabel('<a href="{0}">{0}</a>'.format(url))

        lay = QtWidgets.QVBoxLayout()
        lay.addWidget(title)
        lay.addLayout(btnLay)
        lay.addWidget(link)
        self.setLayout(lay)


class IdleMessage(QtWidgets.QFrame):

    def __init__(self, trigger_action):

        super().__init__()
        self.setObjectName('IdleMessage')

        self._message_label = _('Hit the')
        self._message_button = _('Button!')

        self.initFrame(trigger_action)

    def initFrame(self, trigger_action):

        lbl = QtWidgets.QLabel(self._message_label)
        btn = QtWidgets.QPushButton(self._message_button)
        btn.clicked.connect(trigger_action)

        lay = QtWidgets.QVBoxLayout()
        lay.addWidget(lbl)
        lay.addWidget(btn)
        self.setLayout(lay)


class GreeterMessage(QtWidgets.QFrame):

    def __init__(self, num_x, num_y, skip_last, countdown_action):

        super().__init__()
        self.setObjectName('GreeterMessage')

        self._text_title = _('Get ready!')
        self._text_button = _('Start countdown')

        num_pictures = max(num_x * num_y - int(skip_last), 1)
        if num_pictures > 1:
            self._text_label = _('for {} pictures...').format(num_pictures)
        else:
            self._text_label = ''

        self.initFrame(countdown_action)

    def initFrame(self, countdown_action):

        ttl = QtWidgets.QLabel(self._text_title)
        ttl.setObjectName('title')
        btn = QtWidgets.QPushButton(self._text_button)
        btn.setObjectName('button')
        btn.clicked.connect(countdown_action)
        lbl = QtWidgets.QLabel(self._text_label)
        lbl.setObjectName('message')

        lay = QtWidgets.QVBoxLayout()
        lay.addWidget(ttl)
        lay.addWidget(btn)
        lay.addWidget(lbl)
        self.setLayout(lay)


class CaptureMessage(QtWidgets.QFrame):

    def __init__(self, num_picture, num_x, num_y, skip_last):

        super().__init__()
        self.setObjectName('PoseMessage')

        num_pictures = max(num_x * num_y - int(skip_last), 1)
        if num_pictures > 1:
            self._text = _('Picture {} of {}...').format(num_picture,
                                                         num_pictures)
        else:
            self._text = 'Taking a photo...'

        self.initFrame()

    def initFrame(self):

        lbl = QtWidgets.QLabel(self._text)
        lay = QtWidgets.QVBoxLayout()
        lay.addWidget(lbl)
        self.setLayout(lay)


class PictureMessage(QtWidgets.QFrame):

    def __init__(self, picture):

        super().__init__()
        self.setObjectName('PictureMessage')

        self._picture = picture

    def _paintPicture(self, painter):

        if isinstance(self._picture, QtGui.QImage):
            pix = QtGui.QPixmap.fromImage(self._picture)
        else:
            pix = QtGui.QPixmap(self._picture)
        pix = pix.scaled(self.contentsRect().size(), QtCore.Qt.KeepAspectRatio,
                         QtCore.Qt.SmoothTransformation)

        origin = ((self.width() - pix.width()) // 2,
                  (self.height() - pix.height()) // 2)
        painter.drawPixmap(QtCore.QPoint(*origin), pix)

    def paintEvent(self, event):

        painter = QtGui.QPainter(self)
        self._paintPicture(painter)
        painter.end()


class WaitMessage(QtWidgets.QFrame):

    def __init__(self, message):

        super().__init__()
        self.setObjectName('WaitMessage')

        self._text = message
        self._clock = Widgets.SpinningWaitClock()

        self.initFrame()

    def initFrame(self):

        lbl = QtWidgets.QLabel(self._text)
        lay = QtWidgets.QVBoxLayout()
        lay.addWidget(lbl)
        self.setLayout(lay)

    def showEvent(self, event):

        self.startTimer(100)

    def timerEvent(self, event):

        self._clock.value += 1
        self.update()

    def paintEvent(self, event):

        offset = ((self.width() - self._clock.width()) // 2,
                  (self.height() - self._clock.height()) // 2)

        painter = QtGui.QPainter(self)
        self._clock.render(painter, QtCore.QPoint(*offset),
                           self._clock.visibleRegion(),
                           QtWidgets.QWidget.DrawChildren)
        painter.end()


class CountdownMessage(QtWidgets.QFrame):

    def __init__(self, time, action):

        super().__init__()
        self.setObjectName('CountdownMessage')

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
            pix = pix.scaled(self.contentsRect().size(),
                             QtCore.Qt.KeepAspectRatio,
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


class PostprocessMessage(Widgets.TransparentOverlay):

    def __init__(self, parent, tasks, worker, idle_handle,
                 timeout=None, timeout_handle=None):

        if timeout_handle is None:
            timeout_handle = idle_handle

        super().__init__(parent, timeout, timeout_handle)
        self.setObjectName('PostprocessMessage')
        self.initFrame(tasks, idle_handle, worker)

    def initFrame(self, tasks, idle_handle, worker):

        def disableAndCall(button, handle):
            button.setEnabled(False)
            button.update()
            worker.put(handle)

        def createButton(task):
            button = QtWidgets.QPushButton(task.label)
            button.clicked.connect(lambda: disableAndCall(button, task.action))
            return button

        buttons = [createButton(task) for task in tasks]
        buttons.append(QtWidgets.QPushButton(_('Start over')))
        buttons[-1].clicked.connect(idle_handle)

        button_lay = QtWidgets.QGridLayout()
        for i, button in enumerate(buttons):
            pos = divmod(i, 2)
            button_lay.addWidget(button, *pos)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel(_('Happy?')))
        layout.addLayout(button_lay)
        self.setLayout(layout)


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
        layout.addRow(_('Date:'), self._date_widget)
        layout.addRow(_('Time:'), self._time_widget)

        widget = QtWidgets.QGroupBox()
        widget.setTitle(_('Set system date and time:'))
        widget.setLayout(layout)
        return widget

    def createButtons(self):

        layout = QtWidgets.QHBoxLayout()
        layout.addStretch(1)

        btnSave = QtWidgets.QPushButton(_('Save and restart'))
        btnSave.clicked.connect(self.saveAndRestart)
        layout.addWidget(btnSave)

        btnCancel = QtWidgets.QPushButton(_('Cancel'))
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
        layout.addWidget(self.createButtons())
        self.setLayout(layout)

    def createTabs(self):

        tabs = QtWidgets.QTabWidget()
        tabs.addTab(self.createGuiSettings(), _('Interface'))
        tabs.addTab(self.createPhotoboothSettings(), _('Photobooth'))
        tabs.addTab(self.createCameraSettings(), _('Camera'))
        tabs.addTab(self.createPictureSettings(), _('Picture'))
        tabs.addTab(self.createStorageSettings(), _('Storage'))
        tabs.addTab(self.createGpioSettings(), _('GPIO'))
        tabs.addTab(self.createPrinterSettings(), _('Printer'))
        return tabs

    def createButtons(self):

        layout = QtWidgets.QHBoxLayout()
        layout.addStretch(1)

        btnSave = QtWidgets.QPushButton(_('Save and restart'))
        btnSave.clicked.connect(self.storeConfigAndRestart)
        layout.addWidget(btnSave)

        btnCancel = QtWidgets.QPushButton(_('Cancel'))
        btnCancel.clicked.connect(self._cancelAction)
        layout.addWidget(btnCancel)

        btnRestore = QtWidgets.QPushButton(_('Restore defaults'))
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

        # Fix bug in Qt to allow changing the items in a stylesheet
        delegate = QtWidgets.QStyledItemDelegate()
        cb.setItemDelegate(delegate)

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
        layout.addRow(_('Enable fullscreen:'), fullscreen)
        layout.addRow(_('Gui module:'), module)
        layout.addRow(_('Window size [px]:'), lay_size)
        layout.addRow(_('Hide cursor:'), cursor)
        layout.addRow(_('Appearance:'), style)

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

        postproc_time = QtWidgets.QSpinBox()
        postproc_time.setRange(0, 1000)
        postproc_time.setValue(self._cfg.getInt('Photobooth',
                                                'postprocess_time'))
        self.add('Photobooth', 'postprocess_time', postproc_time)

        err_msg = QtWidgets.QLineEdit(
            self._cfg.get('Photobooth', 'overwrite_error_message'))
        self.add('Photobooth', 'overwrite_error_message', err_msg)

        layout = QtWidgets.QFormLayout()
        layout.addRow(_('Show preview during countdown:'), preview)
        layout.addRow(_('Greeter time before countdown [s]:'), greet_time)
        layout.addRow(_('Countdown time [s]:'), count_time)
        layout.addRow(_('Picture display time [s]:'), displ_time)
        layout.addRow(_('Postprocess timeout [s]:'), postproc_time)
        layout.addRow(_('Overwrite displayed error message:'), err_msg)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        return widget

    def createCameraSettings(self):

        self.init('Camera')

        module = self.createModuleComboBox(camera.modules,
                                           self._cfg.get('Camera', 'module'))
        self.add('Camera', 'module', module)

        self.rot_vals_ = (0, 90, 180, 270)
        cur_rot = self._cfg.getInt('Camera', 'rotation')

        rotation = QtWidgets.QComboBox()
        for r in self.rot_vals_:
            rotation.addItem(str(r))

        idx = [x for x, r in enumerate(self.rot_vals_) if r == cur_rot]
        rotation.setCurrentIndex(idx[0] if len(idx) > 0 else -1)

        # Fix bug in Qt to allow changing the items in a stylesheet
        delegate = QtWidgets.QStyledItemDelegate()
        rotation.setItemDelegate(delegate)

        self.add('Camera', 'rotation', rotation)

        layout = QtWidgets.QFormLayout()
        layout.addRow(_('Camera module:'), module)
        layout.addRow(_('Camera rotation:'), rotation)

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

        skip_last = QtWidgets.QCheckBox()
        skip_last.setChecked(self._cfg.getBool('Picture', 'skip_last'))
        self.add('Picture', 'skip_last', skip_last)

        bg = QtWidgets.QLineEdit(self._cfg.get('Picture', 'background'))
        self.add('Picture', 'background', bg)

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
            dialog = QtWidgets.QFileDialog.getOpenFileName
            bg.setText(dialog(self, _('Select file'), os.path.expanduser('~'),
                              'Images (*.jpg *.png)')[0])

        file_button = QtWidgets.QPushButton(_('Select file'))
        file_button.clicked.connect(file_dialog)

        lay_file = QtWidgets.QHBoxLayout()
        lay_file.addWidget(bg)
        lay_file.addWidget(file_button)

        layout = QtWidgets.QFormLayout()
        layout.addRow(_('Number of shots per picture:'), lay_num)
        layout.addRow(_('Size of assembled picture [px]:'), lay_size)
        layout.addRow(_('Min. distance between shots [px]:'), lay_dist)
        layout.addRow(_('Omit last picture:'), skip_last)
        layout.addRow(_('Background image:'), lay_file)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        return widget

    def createStorageSettings(self):

        self.init('Storage')

        basedir = QtWidgets.QLineEdit(self._cfg.get('Storage', 'basedir'))
        basename = QtWidgets.QLineEdit(self._cfg.get('Storage', 'basename'))
        self.add('Storage', 'basedir', basedir)
        self.add('Storage', 'basename', basename)

        keep_pictures = QtWidgets.QCheckBox()
        keep_pictures.setChecked(self._cfg.getBool('Storage', 'keep_pictures'))
        self.add('Storage', 'keep_pictures', keep_pictures)

        def directory_dialog():
            dialog = QtWidgets.QFileDialog.getExistingDirectory
            basedir.setText(dialog(self, _('Select directory'),
                                   os.path.expanduser('~'),
                                   QtWidgets.QFileDialog.ShowDirsOnly))

        dir_button = QtWidgets.QPushButton(_('Select directory'))
        dir_button.clicked.connect(directory_dialog)

        lay_dir = QtWidgets.QHBoxLayout()
        lay_dir.addWidget(basedir)
        lay_dir.addWidget(dir_button)

        layout = QtWidgets.QFormLayout()
        layout.addRow(_('Output directory (strftime possible):'), lay_dir)
        layout.addRow(_('Basename of files (strftime possible):'), basename)
        layout.addRow(_('Keep single shots:'), keep_pictures)

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

        chan_r_pin = QtWidgets.QSpinBox()
        chan_r_pin.setRange(1, 40)
        chan_r_pin.setValue(self._cfg.getInt('Gpio', 'chan_r_pin'))
        self.add('Gpio', 'chan_r_pin', chan_r_pin)

        chan_g_pin = QtWidgets.QSpinBox()
        chan_g_pin.setRange(1, 40)
        chan_g_pin.setValue(self._cfg.getInt('Gpio', 'chan_g_pin'))
        self.add('Gpio', 'chan_g_pin', chan_g_pin)

        chan_b_pin = QtWidgets.QSpinBox()
        chan_b_pin.setRange(1, 40)
        chan_b_pin.setValue(self._cfg.getInt('Gpio', 'chan_b_pin'))
        self.add('Gpio', 'chan_b_pin', chan_b_pin)

        lay_rgb = QtWidgets.QHBoxLayout()
        lay_rgb.addWidget(chan_r_pin)
        lay_rgb.addWidget(chan_g_pin)
        lay_rgb.addWidget(chan_b_pin)

        layout = QtWidgets.QFormLayout()
        layout.addRow(_('Enable GPIO:'), enable)
        layout.addRow(_('Exit button pin (BCM numbering):'), exit_pin)
        layout.addRow(_('Trigger button pin (BCM numbering):'), trig_pin)
        layout.addRow(_('Idle lamp pin (BCM numbering):'), lamp_pin)
        layout.addRow(_('RGB LED pins (BCM numbering):'), lay_rgb)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        return widget

    def createPrinterSettings(self):

        self.init('Printer')

        enable = QtWidgets.QCheckBox()
        enable.setChecked(self._cfg.getBool('Printer', 'enable'))
        self.add('Printer', 'enable', enable)

        pdf = QtWidgets.QCheckBox()
        pdf.setChecked(self._cfg.getBool('Printer', 'pdf'))
        self.add('Printer', 'pdf', pdf)

        confirmation = QtWidgets.QCheckBox()
        confirmation.setChecked(self._cfg.getBool('Printer', 'confirmation'))
        self.add('Printer', 'confirmation', confirmation)

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
        layout.addRow(_('Enable printing:'), enable)
        layout.addRow(_('Module:'), module)
        layout.addRow(_('Print to PDF (for debugging):'), pdf)
        layout.addRow(_('Ask for confirmation before printing:'), confirmation)
        layout.addRow(_('Paper size [mm]:'), lay_size)

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
        self._cfg.set('Photobooth', 'postprocess_time',
                      str(self.get('Photobooth', 'postprocess_time').text()))
        self._cfg.set('Photobooth', 'overwrite_error_message',
                      self.get('Photobooth', 'overwrite_error_message').text())

        self._cfg.set('Camera', 'module',
                      camera.modules[self.get('Camera',
                                              'module').currentIndex()][0])
        self._cfg.set('Camera', 'rotation', str(
            self.rot_vals_[self.get('Camera', 'rotation').currentIndex()]))

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
        self._cfg.set('Picture', 'skip_last',
                      str(self.get('Picture', 'skip_last').isChecked()))
        self._cfg.set('Picture', 'background',
                      self.get('Picture', 'background').text())

        self._cfg.set('Storage', 'basedir',
                      self.get('Storage', 'basedir').text())
        self._cfg.set('Storage', 'basename',
                      self.get('Storage', 'basename').text())
        self._cfg.set('Storage', 'keep_pictures',
                      str(self.get('Storage', 'keep_pictures').isChecked()))

        self._cfg.set('Gpio', 'enable',
                      str(self.get('Gpio', 'enable').isChecked()))
        self._cfg.set('Gpio', 'exit_pin', self.get('Gpio', 'exit_pin').text())
        self._cfg.set('Gpio', 'trigger_pin',
                      self.get('Gpio', 'trigger_pin').text())
        self._cfg.set('Gpio', 'lamp_pin', self.get('Gpio', 'lamp_pin').text())
        self._cfg.set('Gpio', 'chan_r_pin',
                      self.get('Gpio', 'chan_r_pin').text())
        self._cfg.set('Gpio', 'chan_g_pin',
                      self.get('Gpio', 'chan_g_pin').text())
        self._cfg.set('Gpio', 'chan_b_pin',
                      self.get('Gpio', 'chan_b_pin').text())

        self._cfg.set('Printer', 'enable',
                      str(self.get('Printer', 'enable').isChecked()))
        self._cfg.set('Printer', 'pdf',
                      str(self.get('Printer', 'pdf').isChecked()))
        self._cfg.set('Printer', 'confirmation',
                      str(self.get('Printer', 'confirmation').isChecked()))
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
