#!/usr/bin/env python
# Created by br _at_ re-web _dot_ eu, 2015

try:
    import RPi.GPIO as GPIO
    gpio_enabled = True
except ImportError:
    gpio_enabled = False


class Event:
    def __init__(self, type, value):
        """type  0: quit
                 1: keystroke 
                 2: mouseclick
                 3: gpio
        """
        self.type = type
        self.value = value

class Rpi_GPIO:
    def __init__(self, handle_function, input_channels = [], output_channels = []):
        if gpio_enabled:
            # Display initial information
            print("Your Raspberry Pi is board revision " + str(GPIO.RPI_INFO['P1_REVISION']))
            print("RPi.GPIO version is " + str(GPIO.VERSION))

            # Choose BCM numbering system
            GPIO.setmode(GPIO.BCM)

            # Setup the input channels
            for input_channel in input_channels:
                GPIO.setup(input_channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.add_event_detect(input_channel, GPIO.RISING, callback=handle_function, bouncetime=200)

            # Setup the output channels
            for output_channel in output_channels:
                GPIO.setup(output_channel, GPIO.OUT)
                GPIO.output(output_channel, GPIO.LOW)
        else:
            print("Warning: RPi.GPIO could not be loaded. GPIO disabled.")

    def teardown(self):
        if gpio_enabled:
            GPIO.cleanup()

    def set_output(self, channel, value=0):
        if gpio_enabled:
            GPIO.output(channel, GPIO.HIGH if value==1 else GPIO.LOW)
