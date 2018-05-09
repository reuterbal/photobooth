1. Install Raspbian Desktop (Lite might lack some packages for the GUI)

https://www.raspberrypi.org/documentation/installation/installing-images/

2. Configure and Update
```bash
sudo rpi-config
sudo rpi-update
sudo apt update
sudo apt dist-upgrade
```

3. Install required packages
```bash
sudo apt install gphoto2 libgphoto2-dev python3-dev python3-pip virtualenv  
sudo apt install qt5-default pyqt5-dev pyqt5-dev-tools # for PyQt5-GUI
sudo apt install libffi6 libffi-dev # for gphoto2-cffi bindings
```

4. Remove some files to get gphoto2 working
Note: This breaks file manager access etc. for some camera models
```bash
sudo rm /usr/share/dbus-1/services/org.gtk.vfs.GPhoto2VolumeMonitor.service
sudo rm /usr/share/gvfs/mounts/gphoto2.mount
sudo rm /usr/share/gvfs/remote-volume-monitors/gphoto2.mount
sudo rm /usr/lib/gvfs/gvfs-gphoto2-volume-monitor
sudo rm /usr/lib/gvfs/gvfsd-gphoto2
```

4. Reboot

5. Clone the Photobooth repository
```bash
git clone -b development https://github.com/reuterbal/photobooth
```

6. Initialize virtualenv
```bash
cd photobooth
virtualenv -p python3 --system-site-packages .venv
source .venv/bin/activate
```

7. Install Photobooth
```bash
pip install -e .
```

8. Run Photobooth
```bash
python3 photobooth
```


pip install pyqt5
pip install opencv-python
pip install Pillow
pip install gpiozero
apt install gphoto2 libgphoto2-dev

pip install gphoto2
-or-
pip install gphoto2-cffi


apt install xinput-calibrator xserver-xorg-input-evdev

/usr/share/X11/xorg.conf.d/99-eGalax.conf:
```
Section "InputClass"
    Identifier "evdev tablet catchall"
    MatchIsTablet "on"
    MatchDevicePath "/dev/input/event*"
    Driver "evdev"
EndSection

Section "InputClass"
    Identifier      "calibration"
    MatchProduct    "eGalax Inc. Touch"
    Option  "Calibration"   "19 1988 96 1965"
    Option  "SwapAxes"      "0"
EndSection
```