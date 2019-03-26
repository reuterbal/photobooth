#sudo apt-get install libcups2-dev
#pip3 install pycups

try:
    import cups
except ImportError:
    cups = None  # CUPS is optional

import logging
from . import Printer
from io import BytesIO
from PIL import ImageQt, Image
import base64
import time
from .. import StateMachine
from ..Threading import Workers


class PrinterPyCups(Printer):
	def __init__(self, page_size, print_pdf=False, config=None, comm=None):
		
		self._comm = comm
		self._conn = cups.Connection() if cups else None
		self._printers = self._conn.getPrinters()
		self._config = config
		self._printer_found_in_cups = False
		self._printer_name = ""
		
		if not cups:
			logging.error("Is CUPS and PYCUPS installed?")

		if self._config is not None:
			self._printer_name = config.get('Printer', 'cups_printer_name')
		
		if len(self._printers) == 0:
			logging.error("Please add a printer in Cups")
		else:
			logging.debug("The printers we've found configured in Cups:")
			for printer in self._printers:
				if printer in self._printer_name:
					logging.debug(printer)
					self._printer_found_in_cups = True
					logging.debug("Printer '%s' was found..." %self._printer_name)
		
		if not self._printer_found_in_cups:
			logging.error("The printer '%s' was not found in CUPS" %self._printer_name)

	def print(self, picture):
		
		self.show_print_progress_screen = self._config.getBool('Printer', 'show_print_screen_progress')
		if self.show_print_progress_screen:
			self._comm.send(Workers.GUI, StateMachine.ShowPrintProcess())
			
		if isinstance(picture, ImageQt.ImageQt):
			pil_im = ImageQt.fromqimage(picture)
		else:
			pil_im = Image.open(picture)
				
		pil_im.save("temp.jpg", format="JPEG")

		if not self._printer_name == "":
			logging.debug("Printing picture to %s" %self._printer_name)
			printid = self._conn.printFile(self._printer_name, "temp.jpg", 'test', {})
			while self._conn.getJobs().get(printid, None) is not None:
				time.sleep(1)
		else:
			logging.error("No printer defined...")
			
		time.sleep(14)
		self._comm.send(
			Workers.GUI, StateMachine.IdleState())
			
		
