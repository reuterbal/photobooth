#!/usr/bin/env python
# Created by br _at_ re-web _dot_ eu, 2016

from gui import GUI_PyGame as GuiModule
from time import sleep

import subprocess

# Screen size
display_size = (1024, 600)

# Button size
button_size = (70, 70)

date_digits = ['D', 'D', 'M', 'M', 'Y', 'Y', 'Y', 'Y'] # DD-MM-YYYY
time_digits = ['H', 'H', 'M', 'M'] # HH-MM

numpad = { 	'1': (100, 100), '2': (200, 100), '3': (300, 100),
			'4': (100, 200), '5': (200, 200), '6': (300, 200),
			'7': (100, 300), '8': (200, 300), '9': (300, 300),
			'0': (200, 400) }

#################
### Functions ###
#################

def check_and_handle_events(display, digit):
    r, e = display.check_for_event()
    while r:
        handle_event(e, digit)
        r, e = display.check_for_event()

def handle_event(event, digit, digits, numpad):
	# mouseclick
	if event.type == 2 and event.value[0] == 1:
		print(event.value[1])
		for num, pos in numpad.items():
			if (event.value[1][0] > pos[0] and
			   	event.value[1][0] < pos[0] + button_size[0] and
			   	event.value[1][1] > pos[1] and
			   	event.value[1][1] < pos[1] + button_size[1]):
				digits[digit] = num
				return True
	return False

def show_numpad(display, numpad, button_size):
	for num, pos in numpad.items():
		display.show_button(num, pos, button_size)

def show_digits(display, digits, button_size):
	for i in range(len(digits)):
		display.show_button(digits[i], (400 + i * (button_size[0] + 5), 200), button_size, outline=(0,0,0))
	
def main():	
	display = GuiModule('set-time', display_size, hide_mouse=False)

	for digit in range(len(date_digits)):
		display.clear()

		show_numpad(display, numpad, button_size)	
		display.show_button('Date:', (400, 100), outline=(0,0,0))
		show_digits(display, date_digits, button_size)	

		display.apply()

		digit_done = False
		while not digit_done:
			r, e = display.check_for_event()
			while r:
				digit_done = handle_event(e, digit, date_digits, numpad)
				r, e = display.check_for_event()

	for digit in range(len(time_digits)):
		display.clear()

		show_numpad(display, numpad, button_size)	
		display.show_button('Time:', (400, 100), outline=(0,0,0))
		show_digits(display, time_digits, button_size)	

		display.apply()

		digit_done = False
		while not digit_done:
			event = display.wait_for_event()
			digit_done = handle_event(event, digit, time_digits, numpad)

	# YYYY-MM-DD HH:mm
	date_str = ( date_digits[4] + date_digits[5] + date_digits[6] + date_digits[7] + '-' +
	             date_digits[2] + date_digits[3] + '-' +
	             date_digits[0] + date_digits[1] + ' ' + 
	             time_digits[0] + time_digits[1] + ':' + time_digits[2] + time_digits[3] )

	subprocess.check_call(['date', '-s', date_str])

	display.teardown()
	return 0

if __name__ == "__main__":
    exit(main())
	