#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import multiprocessing as mp
import queue
import logging
from os.path import expanduser

from PIL import ImageQt

from PyQt5 import QtGui, QtCore, QtWidgets

import math

from .PyQt5GuiHelpers import QRoundProgressBar

from . import *
from .. import camera, printer


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
            self._p.setCentralWidget(PyQt5WaitMessage('Processing picture...'))

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
        self._p.setCentralWidget(PyQt5Start(self))
        if QtWidgets.QApplication.overrideCursor() != 0:
            QtWidgets.QApplication.restoreOverrideCursor()


    def showSettings(self):

        self._p.handleKeypressEvent = lambda event : None
        self._lastState = self.showSettings
        self._p.setCentralWidget(PyQt5Settings(self))


    def showStartPhotobooth(self):

        self._lastState = self.showStartPhotobooth
        self._conn.send('start')
        self._p.setCentralWidget(PyQt5WaitMessage('Starting the photobooth...'))
        if cfg.getBool('Gui', 'hide_cursor'):
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.BlankCursor)


    def showIdle(self):

        self._p.handleKeypressEvent = self.handleKeypressEvent
        self._lastState = self.showIdle
        self._p.setCentralWidget(PyQt5IdleMessage())


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




class PyQt5Start(QtWidgets.QFrame):

    def __init__(self, gui):
        
        super().__init__()

        self.initFrame(gui)


    def initFrame(self, gui):

        grid = QtWidgets.QGridLayout()
        grid.setSpacing(100)
        self.setLayout(grid)

        btnStart = QtWidgets.QPushButton('Start Photobooth')
        btnStart.resize(btnStart.sizeHint())
        btnStart.clicked.connect(gui.showStartPhotobooth)
        grid.addWidget(btnStart, 0, 0)

        btnSettings = QtWidgets.QPushButton('Settings')
        btnSettings.resize(btnSettings.sizeHint())
        btnSettings.clicked.connect(gui.showSettings)
        grid.addWidget(btnSettings, 0, 1)

        btnQuit = QtWidgets.QPushButton('Quit')
        btnQuit.resize(btnQuit.sizeHint())
        btnQuit.clicked.connect(gui.close)
        grid.addWidget(btnQuit, 0, 2)



class PyQt5Settings(QtWidgets.QFrame):

    def __init__(self, gui):
        
        super().__init__()

        self._gui = gui

        self.initFrame()


    def initFrame(self):

        self._value_widgets = {}

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
        btnSave.resize(btnSave.sizeHint())
        btnSave.clicked.connect(self.storeConfigAndRestart)
        layout.addWidget(btnSave)

        btnCancel = QtWidgets.QPushButton('Cancel')
        btnCancel.resize(btnCancel.sizeHint())
        btnCancel.clicked.connect(self._gui.showStart)
        layout.addWidget(btnCancel)

        btnRestore = QtWidgets.QPushButton('Restore defaults')
        btnRestore.resize(btnRestore.sizeHint())
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

        global cfg

        self._value_widgets['Gui'] = {}
        self._value_widgets['Gui']['fullscreen'] = QtWidgets.QCheckBox('Enable fullscreen')
        if cfg.getBool('Gui', 'fullscreen'):
            self._value_widgets['Gui']['fullscreen'].toggle()
        self._value_widgets['Gui']['module'] = self.createModuleComboBox(modules, cfg.get('Gui', 'module'))
        self._value_widgets['Gui']['width'] = QtWidgets.QLineEdit(cfg.get('Gui', 'width'))
        self._value_widgets['Gui']['height'] = QtWidgets.QLineEdit(cfg.get('Gui', 'height'))
        self._value_widgets['Gui']['hide_cursor'] = QtWidgets.QCheckBox('Hide cursor')
        if cfg.getBool('Gui', 'hide_cursor'):
            self._value_widgets['Gui']['hide_cursor'].toggle()

        layout = QtWidgets.QFormLayout()
        layout.addRow(self._value_widgets['Gui']['fullscreen'])
        layout.addRow(QtWidgets.QLabel('Gui module:'), self._value_widgets['Gui']['module'])

        sublayout_size = QtWidgets.QHBoxLayout()
        sublayout_size.addWidget(QtWidgets.QLabel('Window size [px]:'))
        sublayout_size.addWidget(self._value_widgets['Gui']['width'])
        sublayout_size.addWidget(QtWidgets.QLabel('x'))
        sublayout_size.addWidget(self._value_widgets['Gui']['height'])
        layout.addRow(sublayout_size)

        layout.addRow(self._value_widgets['Gui']['hide_cursor'])

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        return widget


    def createGpioSettings(self):

        global cfg

        self._value_widgets['Gpio'] = {}
        self._value_widgets['Gpio']['enable'] = QtWidgets.QCheckBox('Enable GPIO')
        if cfg.getBool('Gpio', 'enable'):
            self._value_widgets['Gpio']['enable'].toggle()
        self._value_widgets['Gpio']['exit_pin'] = QtWidgets.QLineEdit(cfg.get('Gpio', 'exit_pin'))
        self._value_widgets['Gpio']['trigger_pin'] = QtWidgets.QLineEdit(cfg.get('Gpio', 'trigger_pin'))
        self._value_widgets['Gpio']['lamp_pin'] = QtWidgets.QLineEdit(cfg.get('Gpio', 'lamp_pin'))

        layout = QtWidgets.QFormLayout()
        layout.addRow(self._value_widgets['Gpio']['enable'])
        layout.addRow(QtWidgets.QLabel('Exit pin (BCM numbering):'), self._value_widgets['Gpio']['exit_pin'])
        layout.addRow(QtWidgets.QLabel('Trigger pin (BCM numbering):'), self._value_widgets['Gpio']['trigger_pin'])
        layout.addRow(QtWidgets.QLabel('Lamp pin (BCM numbering):'), self._value_widgets['Gpio']['lamp_pin'])

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        return widget


    def createPrinterSettings(self):

        global cfg

        self._value_widgets['Printer'] = {}
        self._value_widgets['Printer']['enable'] = QtWidgets.QCheckBox('Enable Printing')
        if cfg.getBool('Printer', 'enable'):
            self._value_widgets['Printer']['enable'].toggle()
        self._value_widgets['Printer']['module'] = self.createModuleComboBox(printer.modules, cfg.get('Printer', 'module'))
        self._value_widgets['Printer']['width'] = QtWidgets.QLineEdit(cfg.get('Printer', 'width'))
        self._value_widgets['Printer']['height'] = QtWidgets.QLineEdit(cfg.get('Printer', 'height'))

        layout = QtWidgets.QFormLayout()
        layout.addRow(self._value_widgets['Printer']['enable'])
        layout.addRow(QtWidgets.QLabel('Printer module:'), self._value_widgets['Printer']['module'])
        
        sublayout_size = QtWidgets.QHBoxLayout()
        sublayout_size.addWidget(QtWidgets.QLabel('Paper size [mm]:'))
        sublayout_size.addWidget(self._value_widgets['Printer']['width'])
        sublayout_size.addWidget(QtWidgets.QLabel('x'))
        sublayout_size.addWidget(self._value_widgets['Printer']['height'])
        layout.addRow(sublayout_size)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        return widget


    def createCameraSettings(self):

        global cfg

        self._value_widgets['Camera'] = {}
        self._value_widgets['Camera']['module'] = self.createModuleComboBox(camera.modules, cfg.get('Camera', 'module'))

        layout = QtWidgets.QFormLayout()
        layout.addRow(QtWidgets.QLabel('Camera module:'), self._value_widgets['Camera']['module'])

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        return widget


    def createPhotoboothSettings(self):

        global cfg

        self._value_widgets['Photobooth'] = {}
        self._value_widgets['Photobooth']['show_preview'] = QtWidgets.QCheckBox('Show preview while countdown')
        if cfg.getBool('Photobooth', 'show_preview'):
            self._value_widgets['Photobooth']['show_preview'].toggle()
        self._value_widgets['Photobooth']['greeter_time'] = QtWidgets.QLineEdit(cfg.get('Photobooth', 'greeter_time'))
        self._value_widgets['Photobooth']['countdown_time'] = QtWidgets.QLineEdit(cfg.get('Photobooth', 'countdown_time'))
        self._value_widgets['Photobooth']['display_time'] = QtWidgets.QLineEdit(cfg.get('Photobooth', 'display_time'))

        layout = QtWidgets.QFormLayout()
        layout.addRow(self._value_widgets['Photobooth']['show_preview'])
        layout.addRow(QtWidgets.QLabel('Greeter time [s]:'), self._value_widgets['Photobooth']['greeter_time'])
        layout.addRow(QtWidgets.QLabel('Countdown time [s]:'), self._value_widgets['Photobooth']['countdown_time'])
        layout.addRow(QtWidgets.QLabel('Display time [s]:'), self._value_widgets['Photobooth']['display_time'])

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        return widget


    def createPictureSettings(self):

        global cfg

        self._value_widgets['Picture'] = {}
        self._value_widgets['Picture']['num_x'] = QtWidgets.QLineEdit(cfg.get('Picture', 'num_x'))
        self._value_widgets['Picture']['num_y'] = QtWidgets.QLineEdit(cfg.get('Picture', 'num_y'))
        self._value_widgets['Picture']['size_x'] = QtWidgets.QLineEdit(cfg.get('Picture', 'size_x'))
        self._value_widgets['Picture']['size_y'] = QtWidgets.QLineEdit(cfg.get('Picture', 'size_y'))
        self._value_widgets['Picture']['min_dist_x'] = QtWidgets.QLineEdit(cfg.get('Picture', 'min_dist_x'))
        self._value_widgets['Picture']['min_dist_y'] = QtWidgets.QLineEdit(cfg.get('Picture', 'min_dist_y'))
        self._value_widgets['Picture']['basedir'] = QtWidgets.QLineEdit(cfg.get('Picture', 'basedir'))
        self._value_widgets['Picture']['basename'] = QtWidgets.QLineEdit(cfg.get('Picture', 'basename'))

        layout = QtWidgets.QFormLayout()

        sublayout_num = QtWidgets.QHBoxLayout()
        sublayout_num.addWidget(QtWidgets.QLabel('Number of shots per picture:'))
        sublayout_num.addWidget(self._value_widgets['Picture']['num_x'])
        sublayout_num.addWidget(QtWidgets.QLabel('x'))
        sublayout_num.addWidget(self._value_widgets['Picture']['num_y'])
        layout.addRow(sublayout_num)

        sublayout_size = QtWidgets.QHBoxLayout()
        sublayout_size.addWidget(QtWidgets.QLabel('Size of assembled picture:'))
        sublayout_size.addWidget(self._value_widgets['Picture']['size_x'])
        sublayout_size.addWidget(QtWidgets.QLabel('x'))
        sublayout_size.addWidget(self._value_widgets['Picture']['size_y'])
        layout.addRow(sublayout_size)

        sublayout_dist = QtWidgets.QHBoxLayout()
        sublayout_dist.addWidget(QtWidgets.QLabel('Min. distance between shots in picture:'))
        sublayout_dist.addWidget(self._value_widgets['Picture']['min_dist_x'])
        sublayout_dist.addWidget(QtWidgets.QLabel('x'))
        sublayout_dist.addWidget(self._value_widgets['Picture']['min_dist_y'])
        layout.addRow(sublayout_dist)

        file_dialog = lambda : self._value_widgets['Picture']['basedir'].setText(
            QtWidgets.QFileDialog.getExistingDirectory(self, 'Select directory', 
                expanduser('~'), QtWidgets.QFileDialog.ShowDirsOnly))
        file_button = QtWidgets.QPushButton('Select directory')
        file_button.resize(file_button.sizeHint())
        file_button.clicked.connect(file_dialog)

        sublayout_path = QtWidgets.QHBoxLayout()
        sublayout_path.addWidget(QtWidgets.QLabel('Basename of output files:'))
        sublayout_path.addWidget(self._value_widgets['Picture']['basedir'])
        sublayout_path.addWidget(QtWidgets.QLabel('/'))
        sublayout_path.addWidget(self._value_widgets['Picture']['basename'])
        sublayout_path.addWidget(file_button)
        layout.addRow(sublayout_path)

        widget = QtWidgets.QWidget()
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
        cfg.set('Picture', 'basedir', self._value_widgets['Picture']['basedir'].text())
        cfg.set('Picture', 'basename', self._value_widgets['Picture']['basename'].text())

        cfg.set('Camera', 'module', camera.modules[self._value_widgets['Camera']['module'].currentIndex()][0])

        cfg.write()
        self._gui.restart()


    def restoreDefaults(self):

        global cfg

        cfg.defaults()
        self._gui.showSettings()




class PyQt5WaitMessage(QtWidgets.QFrame):
    # With spinning wait clock, inspired by 
    # https://wiki.python.org/moin/PyQt/A%20full%20widget%20waiting%20indicator

    def __init__(self, message):
        
        super().__init__()

        self._message = message

        self.initFrame()


    def initFrame(self):

        self.setStyleSheet('background-color: black; color: white;')


    def paintEvent(self, event):

        painter = QtGui.QPainter(self)

        f = self.font()
        f.setPixelSize(self.height() / 8)
        painter.setFont(f)

        rect = QtCore.QRect(0, self.height() * 3 / 5, self.width(), self.height() * 3 / 10)
        painter.drawText(rect, QtCore.Qt.AlignCenter, self._message)

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

        painter.end()


    def showEvent(self, event):
    
        self._counter = 0
        self.startTimer(100)
        
    
    def timerEvent(self, event):
    
        self._counter += 1
        self.update()



class PyQt5IdleMessage(QtWidgets.QFrame):

    def __init__(self):

        super().__init__()

        self.initFrame()


    def initFrame(self):

        self.setStyleSheet('background-color: black; color: white;')


    def paintEvent(self, event):

        painter = QtGui.QPainter(self)

        f = self.font()
        f.setPixelSize(self.height() / 5)
        painter.setFont(f)

        painter.drawText(event.rect(), QtCore.Qt.AlignCenter, 'Hit the button!')

        painter.end()



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

