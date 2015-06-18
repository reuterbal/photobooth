#!/usr/bin/env python
# Created by br@re-web.eu, 2015

import os
from time import sleep

from gui import GUI_PyGame as GuiModule

#####################
### Configuration ###
#####################

# Screen size
display_size = (1024, 600)

# Directory name
directory = "2015-06-18"

# Display time for slideshow pictures
display_time = 3

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

	def run(self):
		while True:
			for filename in self.filelist:
				self.display.clear()
				self.display.show_picture(filename)
				self.display.apply()
				sleep(self.display_time)



#################
### Functions ###
#################

def main():
    slideshow = Slideshow(display_size, display_time, directory, False)
    slideshow.scan()
    slideshow.run()
    return 0

if __name__ == "__main__":
    exit(main())