#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Photobooth USB-Wrapper

import dbus
import time
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import subprocess
import os
import configparser

ignorelist = ['/dev/mmcblk0p1', '/dev/mmcblk0p2']

def get_usb():
    devices = []
    bus = dbus.SystemBus()
    ud_manager_obj = bus.get_object('org.freedesktop.UDisks2', '/org/freedesktop/UDisks2')
    om = dbus.Interface(ud_manager_obj, 'org.freedesktop.DBus.ObjectManager')
    try:
        for k, v in om.GetManagedObjects().items():
            drive_info = v.get('org.freedesktop.UDisks2.Block', {})
            if drive_info.get('IdUsage') == "filesystem" and not drive_info.get('HintSystem') and not drive_info.get('ReadOnly'):
                device = drive_info.get('Device')
                device = bytearray(device).replace(b'\x00', b'').decode('utf-8')
                if not device in ignorelist:
                    devices.append(device)
    except:
        print("No device found...")
    return devices

def get_mountpath(device):
    bus = dbus.SystemBus()
    bd = bus.get_object('org.freedesktop.UDisks2', '/org/freedesktop/UDisks2/block_devices%s'%device[4:])
    mountpoints = []
    try:
        mp = bd.Get('org.freedesktop.UDisks2.Filesystem', 'MountPoints',  dbus_interface='org.freedesktop.DBus.Properties')
        for path in mp:
            mountpoints.append(bytearray(path).replace(b'\x00', b'').decode('utf-8'))
    except:
        print("Error detecting USB details...")
    return mountpoints
    
def mount_drive(device):
    bus = dbus.SystemBus()
    path = ''
    bd = bus.get_object('org.freedesktop.UDisks2', '/org/freedesktop/UDisks2/block_devices%s'%device[4:])
    try:
        path = bd.get_dbus_method('Mount',  dbus_interface='org.freedesktop.UDisks2.Filesystem')([])
    except:
        print('Unable to mount USB device...')
    return path

def find_and_ensure_mounted():
    devices = False
    storage_path = False
    
    usb_devices = get_usb()
    if usb_devices:
        devices = True

    for device in usb_devices:
        mount_paths = get_mountpath(device)
        if mount_paths:
            storage_path = mount_paths[0]
            break
    
    if storage_path:
        print('Found storage path: ' + storage_path)
    elif devices:
        print('Could not find mounted drive,  attempting to mount drive: ' + usb_devices[0])
        storage_path = mount_drive(usb_devices[0])
        if storage_path:
            print('USB device mounted at ' + storage_path)
    else:
        print('No USB device found.')
    
    return storage_path

if __name__ == "__main__":
    pb = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..'))
    cfg = os.path.abspath(os.path.join(pb, 'photobooth.cfg'))
    cfgr = cfg
    if not os.path.exists(cfg):
        cfgr = os.path.abspath(os.path.join(pb, 'photobooth', 'defaults.cfg'))
    config = configparser.ConfigParser(interpolation=None)
    config.read(cfgr)
    
    width = config.getint('Gui','width')
    height = config.getint('Gui','height')
    fs = config.getboolean('Gui', 'fullscreen')
    
    app = QApplication(sys.argv)
    
    #splash_pix = QPixmap('loading.gif')
    splash_pix = QPixmap(width, height)
    splash_pix.fill(Qt.white)
    splash = QSplashScreen(splash_pix) #, Qt.WindowStaysOnTopHint)
    splash.setEnabled(False)
    if fs:
        splash.showFullScreen()
    else:
        splash.setFixedWidth(width)
        splash.setFixedHeight(height)
        splash.show()
    splash.showMessage("<h1>Loading...</h1>", Qt.AlignTop | Qt.AlignCenter, Qt.black)


    storage_path = find_and_ensure_mounted()
    while not storage_path:
        splash.showMessage("<h1>USB Drive not found. Please connect it to start the Photobooth</h1>", Qt.AlignTop | Qt.AlignCenter, Qt.black)
        t = time.time()
        while time.time() < t + 1:
            app.processEvents()
            time.sleep(0.01)
        storage_path = find_and_ensure_mounted()
    splash.showMessage("<h1>USB Drive found.<br>Loading...</h1>", Qt.AlignTop | Qt.AlignCenter, Qt.black)
    print('Found storage path: ' + storage_path)
    
    print(os.path.abspath(os.path.join(storage_path, 'photobooth.cfg')))
    
    if os.path.exists(os.path.abspath(os.path.join(storage_path, 'photobooth.cfg'))):
        mergeconfig = configparser.ConfigParser(interpolation=None)
        mergeconfig.read(os.path.abspath(os.path.join(storage_path, 'photobooth.cfg')))
        print(mergeconfig.sections())
        for section in mergeconfig:
            for key in mergeconfig[section]:
                config[section][key] = mergeconfig[section][key]
                
    if os.path.exists(os.path.abspath(os.path.join(storage_path, 'background.jpg'))):
        config['Picture']['background'] = os.path.abspath(os.path.join(storage_path, 'background.jpg'))
    
    storage_path = os.path.abspath(os.path.join(storage_path, '%Y-%m-%d'))
    
    config['Storage']['basedir'] = storage_path

    with open(cfg, 'w') as configfile:
        config.write(configfile)
    subprocess.run(["./autostart.sh"], cwd=pb)
