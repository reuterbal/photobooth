#!/usr/bin/env python
# Created by br@re-web.eu, 2015

from gui import GUI_PyGame as GuiModule

import os
from datetime import datetime
import subprocess
import thread
from time import sleep

#####################
### Configuration ###
#####################

# Screen size
display_size = (1024, 768)

# Directory for slideshow pictures
slideshow_directory = "slideshow/"

# Source directory, can also be remote.
# Leave empty to disable sync
source_directory = "pi@photobooth:photobooth/" + datetime.now().strftime("%Y-%m-%d")

# Display time (in seconds) for slideshow pictures
display_time = 3

# Waiting time (in seconds) between synchronizations
sync_time = 60

###############
### Classes ###
###############

class Slideshow:
    def __init__(self, display_size, display_time, directory, recursive=True):
        self.directory    = directory
        self.recursive    = recursive
        self.filelist     = []
        self.display      = GuiModule("Slideshow", display_size)
        self.display_time = display_time
        self.next         = 0

    def scan(self):
        filelist = []

        if self.recursive:
            # Recursively walk all entries in the directory
            for root, dirnames, filenames in os.walk(self.directory, followlinks=True):
                for filename in filenames:
                    filelist.append(os.path.join(root, filename))
        else:
            # Add all entries in the directory
            for item in os.listdir(self.directory):
                filename = os.path.join(self.directory, item)
                if os.path.isfile(filename):
                    filelist.append(filename)

        self.filelist = filelist
        self.next = 0

    def handle_event(self, event):
        if event.type == 0:
            self.teardown()
        elif event.type == 1:
            self.handle_keypress(event.value)

    def handle_keypress(self, key):
        # Exit the application
        if key == ord('q'):
            self.teardown()

    def display_next(self, text=""):
        if self.next >= len(self.filelist):
            self.scan()
        if not self.filelist:
            self.display.clear()
            if text:
                self.display.show_message(text)
            else:
                self.display.show_message("No pictures available!")
            self.display.apply()
        else:
            filename = self.filelist[self.next]
            self.next += 1
            self.display.clear()
            self.display.show_picture(filename)
            if text:
                self.display.show_message(text)
            self.display.apply()

    def run(self):
        while True:
            self.display_next()
            sleep(self.display_time)
            r, e = self.display.check_for_event()
            if r:
                self.handle_event(e)

    def teardown(self):
        self.display.teardown()
        exit(0)


#################
### Functions ###
#################

def sync_folders(source_directory, target_directory, wait_time):
    sleep(5)
    while True:
        print("[" + datetime.now().strftime("%H:%M:%S") + "] Sync " 
                + source_directory + " --> " + target_directory)
        try:
            cmd = "rsync -rtu " + source_directory + " " + target_directory
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print("ERROR executing '" + e.cmd + "':\n" + e.output)
        sleep(wait_time)

def main():
    # Start a thread for syncing files
    if len(source_directory) > 0:
        thread.start_new_thread(sync_folders, (source_directory, slideshow_directory, sync_time) )
    
    # Start the slideshow
    slideshow = Slideshow(display_size, display_time, slideshow_directory, True)
    slideshow.run()

    return 0

if __name__ == "__main__":
    exit(main())