#!/usr/bin/env python
# Created by br@re-web.eu, 2015

# TODO: 
# - base everything on surfaces to allow stacking
# - incorporate render_textrect
# - restructure mainloop

from __future__ import division

import pygame  

try:
    import pygame.fastevent as EventModule
except ImportError:
    import pygame.event as EventModule

from events import Event


class TextRectException:
    def __init__(self, message = None):
        self.message = message
    def __str__(self):
        return self.message

def render_textrect(string, font, rect, text_color, background_color, justification=0, valign=0):
    """Returns a surface containing the passed text string, reformatted
    to fit within the given rect, word-wrapping as necessary. The text
    will be anti-aliased.

    Source: http://www.pygame.org/pcr/text_rect/index.php

    Takes the following arguments:

    string - the text you wish to render. \n begins a new line.
    font - a Font object
    rect - a rectstyle giving the size of the surface requested.
    text_color - a three-byte tuple of the rgb value of the
                 text color. ex (0, 0, 0) = BLACK
    background_color - a three-byte tuple of the rgb value of the surface.
    justification - 0 (default) left-justified
                    1 horizontally centered
                    2 right-justified
    valign - 0 (default) top aligned
             1 vertically centered
             2 bottom aligned

    Returns the following values:

    Success - a surface object with the text rendered onto it.
    Failure - raises a TextRectException if the text won't fit onto the surface.
    """

    final_lines = []

    requested_lines = string.splitlines()

    # Create a series of lines that will fit on the provided
    # rectangle.

    accumulated_height = 0
    for requested_line in requested_lines:
        if font.size(requested_line)[0] > rect.width:
            words = requested_line.split(' ')
            # if any of our words are too long to fit, return.
            for word in words:
                if font.size(word)[0] >= rect.width:
                    raise TextRectException, "The word " + word + " is too long to fit in the rect passed."
            # Start a new line
            accumulated_line = ""
            for word in words:
                test_line = accumulated_line + word + " "
                # Build the line while the words fit.    
                if font.size(test_line)[0] < rect.width:
                    accumulated_line = test_line 
                else: 
                    accumulated_height += font.size(test_line)[1]
                    final_lines.append(accumulated_line) 
                    accumulated_line = word + " " 
            accumulated_height += font.size(accumulated_line)[1]
            final_lines.append(accumulated_line)
        else:
            accumulated_height += font.size(requested_line)[1] 
            final_lines.append(requested_line) 

    # Check height of the text and align vertically

    if accumulated_height >= rect.height:
        raise TextRectException, "Once word-wrapped, the text string was too tall to fit in the rect."

    if valign == 0:
        voffset = 0
    elif valign == 1:
        voffset = int((rect.height - accumulated_height) / 2)
    elif valign == 2:
        voffset = rect.height - accumulated_height
    else:
        raise TextRectException, "Invalid valign argument: " + str(valign)

    # Let's try to write the text out on the surface.

    surface = pygame.Surface(rect.size) 
    surface.fill(background_color) 

    accumulated_height = 0 
    for line in final_lines: 
        if line != "":
            tempsurface = font.render(line, 1, text_color)
            if justification == 0:
                surface.blit(tempsurface, (0, voffset + accumulated_height))
            elif justification == 1:
                surface.blit(tempsurface, ((rect.width - tempsurface.get_width()) / 2, voffset + accumulated_height))
            elif justification == 2:
                surface.blit(tempsurface, (rect.width - tempsurface.get_width(), voffset + accumulated_height))
            else:
                raise TextRectException, "Invalid justification argument: " + str(justification)
        accumulated_height += font.size(line)[1]

    return surface


class GUI_PyGame:
    """A GUI class using PyGame"""

    def __init__(self, name, size):
        # Call init routines
        pygame.init()
        if hasattr(EventModule, 'init'):
            EventModule.init()

        # Window name
        pygame.display.set_caption(name)

        # Hide mouse cursor
        pygame.mouse.set_cursor(*pygame.cursors.load_xbm('transparent.xbm','transparent.msk'))

        # Store screen and size
        self.size = size
        self.screen = pygame.display.set_mode(size) #, pygame.FULLSCREEN)

        # Clear screen
        self.clear()

    def clear(self, color=(0,0,0)):
        self.screen.fill(color)
        self.surface_list = []

    def apply(self):
        for surface in self.surface_list:
            self.screen.blit(surface[0], surface[1])
        pygame.display.update()

    def get_size(self):
        return self.size

    def trigger_event(self, event_channel):
        EventModule.post(EventModule.Event(pygame.USEREVENT, channel=event_channel))

    def show_picture(self, filename, size=(0,0), offset=(0,0)):
        # Use window size if none given
        if size == (0,0):
            size = self.size
        # Load image from file
        image = pygame.image.load(filename)
        # Extract image size and determine scaling
        image_size = image.get_rect().size
        image_scale = min([min(a,b)/b for a,b in zip(size, image_size)])
        # New image size
        new_size = [int(a*image_scale) for a in image_size]
        # Update offset
        offset = tuple(a+int((b-c)/2) for a,b,c in zip(offset, size, new_size))
        # Apply scaling and display picture
        image = pygame.transform.scale(image, new_size).convert()
        # Create surface and blit the image to it
        surface = pygame.Surface(new_size)
        surface.blit(image, (0,0))
        self.surface_list.append((surface, offset))

    def show_message(self, msg, color=(245,245,245), bg=(0,0,0), transparency=True):
        # Choose font
        font = pygame.font.Font(None, 144)
        # Create rectangle for text
        rect = pygame.Rect((0, 0, self.size[0], self.size[1]))
        # Render text
        text = render_textrect(msg, font, rect, color, bg, 1, 1)
        if transparency:
            text.set_colorkey(bg)
        self.surface_list.append((text, rect.topleft))

    def convert_event(self, event):
        if event.type == pygame.QUIT: 
            return True, Event(0, 0)
        elif event.type == pygame.KEYDOWN: 
            return True, Event(1, event.key)
        elif event.type == pygame.MOUSEBUTTONUP: 
            return True, Event(2, (event.button, event.pos))
        elif event.type >= pygame.USEREVENT: 
            return True, Event(3, event.channel)
        else:
            return False, ''

    def check_for_event(self):
        for event in EventModule.get():
            r, e = self.convert_event(event)
            if r:
                return r, e
        return False, ''

    def wait_for_event(self):
        # Repeat until a relevant event happened
        while True:
            # Discard all input that happened before entering the loop
            EventModule.get()

            # Wait for event
            event = EventModule.wait()

            # Return Event-Object
            r, e = self.convert_event(event)
            if r:
                return e


    def mainloop(self, filename, handle_keypress, handle_mousebutton, handle_gpio_event):
        while True:
            # Ignore all input that happened before entering the loop
            EventModule.get()
            # Clear display
            self.clear()
            # Show idle-picture and message
            if filename != None:
                self.show_picture(filename)
            self.show_message("Hit the button!")
            # Render everything
            self.apply()
            # Wait for event
            event = EventModule.wait()
            # Handle the event
            if event.type == pygame.QUIT: return
            elif event.type == pygame.KEYDOWN: handle_keypress(event.key)
            elif event.type == pygame.MOUSEBUTTONUP: handle_mousebutton(event.button, event.pos)
            elif event.type == gpio_pygame_event: handle_gpio_event(event.channel)

    def teardown(self):
        pygame.quit()
