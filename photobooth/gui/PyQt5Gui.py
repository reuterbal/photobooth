#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import multiprocessing as mp

from PIL import ImageQt

from PyQt5.QtCore import Qt, QObject, QPoint, QThread, QTimer, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLayout, QLineEdit, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget)
from PyQt5.QtGui import QImage, QPainter, QPixmap

import math
from PyQt5.QtGui import QBrush, QPen, QColor
from PyQt5.QtCore import QRect

from .PyQt5GuiHelpers import QRoundProgressBar

from . import *
from .. import camera, printer

from ..printer.PrinterPyQt5 import PrinterPyQt5 as Printer


class PyQt5Gui(Gui):

    def __init__(self, argv, config):

        super().__init__()

        global cfg
        cfg = config

        self._app = QApplication(argv)
        self._p = PyQt5MainWindow()
        self._lastState = self.showStart
        self._printer = Printer((cfg.getInt('Printer', 'width'), 
                                 cfg.getInt('Printer', 'height')), True)


    def run(self, camera_conn):

        receiver = PyQt5Receiver([camera_conn])
        receiver.notify.connect(self.handleState)
        receiver.start()

        self._conn = camera_conn

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

        if event.key() == Qt.Key_Escape:
            self.handleState(TeardownState())
        elif event.key() == Qt.Key_Space:
            self.handleState(TriggerState())


    def handleKeypressEventNoTrigger(self, event):

        if event.key() == Qt.Key_Escape:
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
            num_pictures = ( 
                cfg.getInt('Picture', 'num_x') * 
                cfg.getInt('Picture', 'num_y') )
            self._p.setCentralWidget(
                PyQt5PictureMessage('Will capture {} pictures!'.format(num_pictures)))
            QTimer.singleShot(cfg.getInt('Photobooth', 'greeter_time') * 1000, self.sendAck)

        elif isinstance(state, CountdownState):
            self._p.setCentralWidget(PyQt5CountdownMessage(cfg.getInt('Photobooth', 'countdown_time'), self.sendAck))

        elif isinstance(state, PreviewState):
            self._p.centralWidget().picture = ImageQt.ImageQt(state.picture)
            self._p.centralWidget().update()
            
        elif isinstance(state, PoseState):
            self._p.setCentralWidget(PyQt5PictureMessage('Pose!'))

        elif isinstance(state, AssembleState):
            self._p.setCentralWidget(PyQt5WaitMessage('Processing picture...'))

        elif isinstance(state, PictureState):
            img = ImageQt.ImageQt(state.picture)
            self._p.setCentralWidget(PyQt5PictureMessage('', img))
            QTimer.singleShot(cfg.getInt('Photobooth', 'display_time') * 1000, lambda : self.sendAck())

            self._printer.print(state.picture)

        elif isinstance(state, TeardownState):
            self._conn.send('teardown')
            self.showStart()

        elif isinstance(state, ErrorState):
            self.showError(state.title, state.message)

        else:
            raise ValueError('Unknown state')


    def showStart(self):

        self._p.handleKeypressEvent = lambda event : None
        self._lastState = self.showStart
        self._p.setCentralWidget(PyQt5Start(self))
        if QApplication.overrideCursor() != 0:
            QApplication.restoreOverrideCursor()


    def showSettings(self):

        self._p.handleKeypressEvent = lambda event : None
        self._lastState = self.showSettings
        self._p.setCentralWidget(PyQt5Settings(self))


    def showStartPhotobooth(self):

        self._lastState = self.showStartPhotobooth
        self._conn.send('start')
        self._p.setCentralWidget(PyQt5WaitMessage('Starting the photobooth...'))
        if cfg.getBool('Gui', 'hide_cursor'):
            QApplication.setOverrideCursor(Qt.BlankCursor)


    def showIdle(self):

        self._p.handleKeypressEvent = self.handleKeypressEvent
        self._lastState = self.showIdle
        self._p.setCentralWidget(PyQt5PictureMessage('Hit the button!'))


    def showError(self, title, message):

        print('ERROR: ' + title + ': ' + message)
        reply = QMessageBox.warning(self._p, title, message, QMessageBox.Close | QMessageBox.Retry, 
            QMessageBox.Retry) 
        if reply == QMessageBox.Retry:
            self.sendAck()
            self._lastState()
        else:
            self.sendCancel()
            self.showStart()


class PyQt5Receiver(QThread):

    notify = pyqtSignal(object)

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



class PyQt5MainWindow(QMainWindow):

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

        reply = QMessageBox.question(self, 'Confirmation', "Quit Photobooth?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
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
        btnStart.clicked.connect(gui.showStartPhotobooth)
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
        grid.addWidget(self.createPrinterSettings(), 2, 0)
        grid.addWidget(self.createCameraSettings(), 0, 1)
        grid.addWidget(self.createPhotoboothSettings(), 1, 1)
        grid.addWidget(self.createPictureSettings(), 2, 1)

        layout = QVBoxLayout()
        layout.addLayout(grid)
        layout.addStretch(1)
        layout.addWidget(self.createButtons())
        self.setLayout(layout)


    def createModuleComboBox(self, module_list, current_module):

        cb = QComboBox()
        for m in module_list:
            cb.addItem(m[0])

        idx = [x for x, m in enumerate(module_list) if m[0] == current_module]
        cb.setCurrentIndex(idx[0] if len(idx) > 0 else -1)

        return cb


    def createGuiSettings(self):

        global cfg

        self._value_widgets['Gui'] = {}
        self._value_widgets['Gui']['fullscreen'] = QCheckBox('Enable fullscreen')
        if cfg.getBool('Gui', 'fullscreen'):
            self._value_widgets['Gui']['fullscreen'].toggle()
        self._value_widgets['Gui']['module'] = self.createModuleComboBox(modules, cfg.get('Gui', 'module'))
        self._value_widgets['Gui']['width'] = QLineEdit(cfg.get('Gui', 'width'))
        self._value_widgets['Gui']['height'] = QLineEdit(cfg.get('Gui', 'height'))
        self._value_widgets['Gui']['hide_cursor'] = QCheckBox('Hide cursor')
        if cfg.getBool('Gui', 'hide_cursor'):
            self._value_widgets['Gui']['hide_cursor'].toggle()

        layout = QFormLayout()
        layout.addRow(self._value_widgets['Gui']['fullscreen'])
        layout.addRow(QLabel('Gui module:'), self._value_widgets['Gui']['module'])

        sublayout_size = QHBoxLayout()
        sublayout_size.addWidget(QLabel('Window size [px]:'))
        sublayout_size.addWidget(self._value_widgets['Gui']['width'])
        sublayout_size.addWidget(QLabel('x'))
        sublayout_size.addWidget(self._value_widgets['Gui']['height'])
        layout.addRow(sublayout_size)

        layout.addRow(self._value_widgets['Gui']['hide_cursor'])

        widget = QGroupBox('Interface settings')
        widget.setLayout(layout)
        return widget


    def createGpioSettings(self):

        global cfg

        self._value_widgets['Gpio'] = {}
        self._value_widgets['Gpio']['enable'] = QCheckBox('Enable GPIO')
        if cfg.getBool('Gpio', 'enable'):
            self._value_widgets['Gpio']['enable'].toggle()
        self._value_widgets['Gpio']['exit_pin'] = QLineEdit(cfg.get('Gpio', 'exit_pin'))
        self._value_widgets['Gpio']['trigger_pin'] = QLineEdit(cfg.get('Gpio', 'trigger_pin'))
        self._value_widgets['Gpio']['lamp_pin'] = QLineEdit(cfg.get('Gpio', 'lamp_pin'))

        layout = QFormLayout()
        layout.addRow(self._value_widgets['Gpio']['enable'])
        layout.addRow(QLabel('Exit pin (BCM numbering):'), self._value_widgets['Gpio']['exit_pin'])
        layout.addRow(QLabel('Trigger pin (BCM numbering):'), self._value_widgets['Gpio']['trigger_pin'])
        layout.addRow(QLabel('Lamp pin (BCM numbering):'), self._value_widgets['Gpio']['lamp_pin'])

        widget = QGroupBox('GPIO settings')
        widget.setLayout(layout)
        return widget


    def createPrinterSettings(self):

        global cfg

        self._value_widgets['Printer'] = {}
        self._value_widgets['Printer']['enable'] = QCheckBox('Enable Printing')
        if cfg.getBool('Printer', 'enable'):
            self._value_widgets['Printer']['enable'].toggle()
        self._value_widgets['Printer']['module'] = self.createModuleComboBox(printer.modules, cfg.get('Printer', 'module'))
        self._value_widgets['Printer']['width'] = QLineEdit(cfg.get('Printer', 'width'))
        self._value_widgets['Printer']['height'] = QLineEdit(cfg.get('Printer', 'height'))

        layout = QFormLayout()
        layout.addRow(self._value_widgets['Printer']['enable'])
        layout.addRow(QLabel('Printer module:'), self._value_widgets['Printer']['module'])
        
        sublayout_size = QHBoxLayout()
        sublayout_size.addWidget(QLabel('Paper size [mm]:'))
        sublayout_size.addWidget(self._value_widgets['Printer']['width'])
        sublayout_size.addWidget(QLabel('x'))
        sublayout_size.addWidget(self._value_widgets['Printer']['height'])
        layout.addRow(sublayout_size)

        widget = QGroupBox('Printer settings')
        widget.setLayout(layout)
        return widget


    def createCameraSettings(self):

        global cfg

        self._value_widgets['Camera'] = {}
        self._value_widgets['Camera']['module'] = self.createModuleComboBox(camera.modules, cfg.get('Camera', 'module'))

        layout = QFormLayout()
        layout.addRow(QLabel('Camera module:'), self._value_widgets['Camera']['module'])

        widget = QGroupBox('Camera settings')
        widget.setLayout(layout)
        return widget


    def createPhotoboothSettings(self):

        global cfg

        self._value_widgets['Photobooth'] = {}
        self._value_widgets['Photobooth']['show_preview'] = QCheckBox('Show preview while countdown')
        if cfg.getBool('Photobooth', 'show_preview'):
            self._value_widgets['Photobooth']['show_preview'].toggle()
        self._value_widgets['Photobooth']['greeter_time'] = QLineEdit(cfg.get('Photobooth', 'greeter_time'))
        self._value_widgets['Photobooth']['countdown_time'] = QLineEdit(cfg.get('Photobooth', 'countdown_time'))
        self._value_widgets['Photobooth']['display_time'] = QLineEdit(cfg.get('Photobooth', 'display_time'))

        layout = QFormLayout()
        layout.addRow(self._value_widgets['Photobooth']['show_preview'])
        layout.addRow(QLabel('Pose time [s]:'), self._value_widgets['Photobooth']['greeter_time'])
        layout.addRow(QLabel('Countdown time [s]:'), self._value_widgets['Photobooth']['countdown_time'])
        layout.addRow(QLabel('Display time [s]:'), self._value_widgets['Photobooth']['display_time'])

        widget = QGroupBox('Photobooth settings')
        widget.setLayout(layout)
        return widget


    def createPictureSettings(self):

        global cfg

        self._value_widgets['Picture'] = {}
        self._value_widgets['Picture']['num_x'] = QLineEdit(cfg.get('Picture', 'num_x'))
        self._value_widgets['Picture']['num_y'] = QLineEdit(cfg.get('Picture', 'num_y'))
        self._value_widgets['Picture']['size_x'] = QLineEdit(cfg.get('Picture', 'size_x'))
        self._value_widgets['Picture']['size_y'] = QLineEdit(cfg.get('Picture', 'size_y'))
        self._value_widgets['Picture']['min_dist_x'] = QLineEdit(cfg.get('Picture', 'min_dist_x'))
        self._value_widgets['Picture']['min_dist_y'] = QLineEdit(cfg.get('Picture', 'min_dist_y'))
        self._value_widgets['Picture']['basename'] = QLineEdit(cfg.get('Picture', 'basename'))

        layout = QFormLayout()

        sublayout_num = QHBoxLayout()
        sublayout_num.addWidget(QLabel('Number of shots per picture:'))
        sublayout_num.addWidget(self._value_widgets['Picture']['num_x'])
        sublayout_num.addWidget(QLabel('x'))
        sublayout_num.addWidget(self._value_widgets['Picture']['num_y'])
        layout.addRow(sublayout_num)

        sublayout_size = QHBoxLayout()
        sublayout_size.addWidget(QLabel('Size of assembled picture:'))
        sublayout_size.addWidget(self._value_widgets['Picture']['size_x'])
        sublayout_size.addWidget(QLabel('x'))
        sublayout_size.addWidget(self._value_widgets['Picture']['size_y'])
        layout.addRow(sublayout_size)

        sublayout_dist = QHBoxLayout()
        sublayout_dist.addWidget(QLabel('Min. distance between shots in picture:'))
        sublayout_dist.addWidget(self._value_widgets['Picture']['min_dist_x'])
        sublayout_dist.addWidget(QLabel('x'))
        sublayout_dist.addWidget(self._value_widgets['Picture']['min_dist_y'])
        layout.addRow(sublayout_dist)

        layout.addRow(QLabel('Basename of output files:'), self._value_widgets['Picture']['basename'])

        widget = QGroupBox('Picture settings')
        widget.setLayout(layout)
        return widget


    def createButtons(self):

        layout = QHBoxLayout()
        layout.addStretch(1)

        btnSave = QPushButton('Save')
        btnSave.resize(btnSave.sizeHint())
        btnSave.clicked.connect(self.storeConfigAndRestart)
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


    def storeConfigAndRestart(self):

        global cfg

        cfg.set('Gui', 'fullscreen', str(self._value_widgets['Gui']['fullscreen'].isChecked()))
        cfg.set('Gui', 'module', modules[self._value_widgets['Gui']['module'].currentIndex()][0])
        cfg.set('Gui', 'width', self._value_widgets['Gui']['width'].text())
        cfg.set('Gui', 'height', self._value_widgets['Gui']['height'].text())
        cfg.set('Gui', 'hide_cursor', str(self._value_widgets['Gui']['hide_cursor'].isChecked()))


        cfg.set('Gpio', 'enable', str(self._value_widgets['Gpio']['enable'].isChecked()))
        cfg.set('Gpio', 'exit_pin', self._value_widgets['Gpio']['exit_pin'].text())
        cfg.set('Gpio', 'trigger_pin', self._value_widgets['Gpio']['trigger_pin'].text())
        cfg.set('Gpio', 'lamp_pin', self._value_widgets['Gpio']['lamp_pin'].text())

        cfg.set('Printer', 'enable', str(self._value_widgets['Printer']['enable'].isChecked()))
        cfg.set('Printer', 'module', modules[self._value_widgets['Printer']['module'].currentIndex()][0])
        cfg.set('Printer', 'width', self._value_widgets['Printer']['width'].text())
        cfg.set('Printer', 'height', self._value_widgets['Printer']['height'].text())

        cfg.set('Photobooth', 'show_preview', str(self._value_widgets['Photobooth']['show_preview'].isChecked()))
        cfg.set('Photobooth', 'greeter_time', str(self._value_widgets['Photobooth']['greeter_time'].text()))
        cfg.set('Photobooth', 'countdown_time', str(self._value_widgets['Photobooth']['countdown_time'].text()))
        cfg.set('Photobooth', 'display_time', str(self._value_widgets['Photobooth']['display_time'].text()))

        cfg.set('Picture', 'num_x', self._value_widgets['Picture']['num_x'].text())
        cfg.set('Picture', 'num_y', self._value_widgets['Picture']['num_y'].text())
        cfg.set('Picture', 'size_x', self._value_widgets['Picture']['size_x'].text())
        cfg.set('Picture', 'size_y', self._value_widgets['Picture']['size_y'].text())
        cfg.set('Picture', 'min_dist_x', self._value_widgets['Picture']['min_dist_x'].text())
        cfg.set('Picture', 'min_dist_y', self._value_widgets['Picture']['min_dist_y'].text())
        cfg.set('Picture', 'basename', self._value_widgets['Picture']['basename'].text())

        cfg.set('Camera', 'module', camera.modules[self._value_widgets['Camera']['module'].currentIndex()][0])

        cfg.write()
        self._gui.restart()


    def restoreDefaults(self):

        global cfg

        cfg.defaults()
        self._gui.showSettings()




class PyQt5WaitMessage(QFrame):
    # With spinning wait clock, inspired by 
    # https://wiki.python.org/moin/PyQt/A%20full%20widget%20waiting%20indicator

    def __init__(self, message):
        
        super().__init__()

        self._message = message

        self.initFrame()


    def initFrame(self):

        self.setStyleSheet('background-color: white;')


    def paintEvent(self, event):

        painter = QPainter(self)

        rect = QRect(0, self.height() * 3 / 5, self.width(), self.height() * 3 / 10)
        painter.drawText(rect, Qt.AlignCenter, self._message)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(Qt.NoPen))

        center = (self.width() / 2, self.height() / 2)

        dots = 8
        pos = self._counter % dots

        for i in range(dots):

            distance = (pos - i) % dots
            color = (distance + 1) / (dots + 1) * 255
            painter.setBrush(QBrush(QColor(color, color, color)))

            painter.drawEllipse(
                center[0] + 180 / dots * math.cos(2 * math.pi * i / dots) - 20,
                center[1] + 180 / dots * math.sin(2 * math.pi * i / dots) - 20,
                15, 15)

        painter.end()


    def showEvent(self, event):
    
        self._counter = 0
        self.startTimer(100)
        
    

    def timerEvent(self, event):
    
        self._counter += 1
        self.update()



class PyQt5CountdownMessage(QFrame):

    def __init__(self, time, action):
        
        super().__init__()

        self._step_size = 100
        self._counter = time * (1000 // self._step_size)
        self._action = action
        self._picture = None

        self.initFrame()
        self.initProgressBar(time)


    def initFrame(self):

        self.setStyleSheet('background-color: white;')


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

        if not isinstance(pic, QImage):
            raise ValueError('picture must be a QImage')

        self._picture = pic


    def paintEvent(self, event):

        painter = QPainter(self)

        if self._picture != None:
            pix = QPixmap.fromImage(self._picture)
            pix = pix.scaled(self.size(), Qt.KeepAspectRatio, Qt.FastTransformation)
            origin = ( (self.width() - pix.width()) // 2,
                       (self.height() - pix.height()) // 2 )
            painter.drawPixmap(QPoint(*origin), pix)

        # painter.drawText(event.rect(), Qt.AlignCenter, str(self.counter))
        painter.end()

        offset = ( (self.width() - self._bar.width()) // 2, 
                   (self.height() - self._bar.height()) // 2 )
        self._bar.render(self, QPoint(*offset), self._bar.visibleRegion(), QWidget.DrawChildren)


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


class PyQt5PictureMessage(QFrame):

    def __init__(self, message, picture=None):
        
        super().__init__()

        self._message = message
        self._picture = picture

        self.initFrame()


    def initFrame(self):

        self.setStyleSheet('background-color: white;')


    def paintEvent(self, event):

        painter = QPainter(self)

        if self._picture != None:
            if isinstance(self._picture, QImage):
                pix = QPixmap.fromImage(self._picture)
            else:
                pix = QPixmap(self._picture)
            pix = pix.scaled(self.rect().size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

            origin = ( (self.rect().width() - pix.width()) // 2,
                       (self.rect().height() - pix.height()) // 2 )
            painter.drawPixmap(QPoint(*origin), pix)

        painter.drawText(event.rect(), Qt.AlignCenter, self._message)
        painter.end()
