#!/usr/bin/env python
# Created by br@re-web.eu, 2015

from gui import GUI_PyGame as GuiModule

import os
from datetime import datetime
from time import sleep
import subprocess
from threading import Thread

#####################
### Configuration ###
#####################

# Screen size
display_size = (1024, 768)

# Directory name
directory = datetime.now().strftime("%Y-%m-%d")

# Display time for slideshow pictures
display_time = 3

# Waiting time between synchronizations
sync_time = 60

#keep_running = True

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

    def scan(self):
        filelist = []

        if self.recursive:
            # Recursively walk all entries in the directory
            for root, dirnames, filenames in os.walk(self.directory):
                for filename in filenames:
                    filelist.append(os.path.join(root, filename))
        else:
            # Add all entries in the directory
            for item in os.listdir(self.directory):
                filename = os.path.join(self.directory, item)
                if os.path.isfile(filename):
                    filelist.append(filename)

        self.filelist = filelist

    def handle_event(self, event):
        if event.type == 0:
            self.teardown()
        elif event.type == 1:
            self.handle_keypress(event.value)

    def handle_keypress(self, key):
        # Exit the application
        if key == ord('q'):
            self.teardown()

    def run(self):
        while True:
            self.scan()
            for filename in self.filelist:
                self.display.clear()
                self.display.show_picture(filename)
                self.display.apply()
                sleep(self.display_time)
                r, e = self.display.check_for_event()
                if r:
                    self.handle_event(e)

    def teardown(self):
        self.display.teardown()
        #keep_running = False
        exit(0)


#################
### Functions ###
#################

def routine_command(cmd, interval):
    while True:
        print("Running routine")
        #output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        #print("Output is " + output)
        sleep(interval)

def main():
    show = Slideshow(display_size, display_time, directory, True)
    sync = Thread(target=routine_command, args=("/bin/echo 'Routine executed'", 5) )
    
    #sync.run()
    show.run()

    sync.join()
    return 0

if __name__ == "__main__":
    exit(main())