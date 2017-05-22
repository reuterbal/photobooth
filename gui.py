#!/usr/bin/env python
# Created by br _at_ re-web _dot_ eu, 2015

from __future__ import division

import pygame

try:
    import pygame.fastevent as EventModule
except ImportError:
    import pygame.event as EventModule

from events import Event

class GuiException(Exception):
    """Custom exception class to handle GUI class errors"""

class GUI_PyGame:
    """A GUI class using PyGame"""

    def __init__(self, name, size, hide_mouse=True,
                 display_rotate=False):
        # Call init routines
        pygame.init()
        if hasattr(EventModule, 'init'):
            EventModule.init()

        # Window name
        pygame.display.set_caption(name)

        # Hide mouse cursor
        if hide_mouse:
            pygame.mouse.set_cursor(*pygame.cursors.load_xbm('transparent.xbm','transparent.msk'))

        # Store screen and size
        self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        
        # Always find the real resolution (e.g., if size==(0,0))
        i = pygame.display.Info()
        self.size = (i.current_w, i.current_h)

        # Should text be rotated 90 degrees counterclockwise?
        self.display_rotate = display_rotate

        # Clear screen
        self.clear()
        self.apply()

    def toggle_fullscreen(self):
        pygame.display.toggle_fullscreen()

    def set_rotate(self, display_rotate):
        self.display_rotate=display_rotate

    def get_rotate(self):
        return self.display_rotate

    def clear(self, color=(0,0,0)):
        self.screen.fill(color)
        self.surface_list = []

    def apply(self):
        for surface in self.surface_list:
            self.screen.blit(surface[0], surface[1])
        pygame.display.update()

    def blit_array(self, f):
        """Given a 2-D array (Numpy style), blit it directly to the screen
        using pygame.surfarray, which is significantly faster than
        creating a new Surface and then blitting that.

        Note that 2-D arrays cannot be scaled easily, so this has the
        downside that the image may be smaller than the screen. This code
        will compensate by centering the image.
        
        Also note, if you pass in an array that's *larger* than the
        screen, then this will arbitrarily decimate the array for you
        using nearest neighbor.
        """

        # Find size of image array and of screen
        (    w,     h) = (len(f), len(f[0]))
        (max_w, max_h) = self.get_size()                            

        # Decimate size if image is too large.
        if w>max_w or h>max_h:
            w_factor = (w/max_w) + (1 if (w%max_w) else 0)
            h_factor = (h/max_h) + (1 if (h%max_h) else 0)
            scaling_factor = int(max( (w_factor, h_factor) ))
            f=f[::scaling_factor, ::scaling_factor]
            (w, h) = (len(f), len(f[0]))

        # Center the preview on the screen
        x=(max_w-w)/2
        y=(max_h-h)/2

        subsurface=pygame.Surface.subsurface(self.screen, ( (x,y), (w, h) ))
        pygame.surfarray.blit_array(subsurface, f)

    def get_size(self):
        return self.size

    def trigger_event(self, event_channel):
        EventModule.post(EventModule.Event(pygame.USEREVENT, channel=event_channel))

    def show_picture(self, filename, size=(0,0), offset=(0,0), flip=False):
        # Use window size if none given
        if size == (0,0):
            size = self.size
        try:
            # Load image from file
            image = pygame.image.load(filename)
        except pygame.error as e:
            raise GuiException("ERROR: Can't open image '" + filename + "': " + e.message)
        # If the display is rotated CW, rotate the image CCW to compensate.
        if self.get_rotate():
            pygame.transform.rotate(image, 90)

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
        if flip:
            surface = pygame.transform.flip(surface, True, False)
        self.surface_list.append((surface, offset))


    def show_message(self, msg, color=(0,0,0), bg=(230,230,230), transparency=True, outline=(245,245,245)):
        # Check if we've done this before
        s=self.get_message_cache(msg, color, bg, transparency, outline,
                                 self.display_rotate)
        if s:
            self.surface_list.append((s, (0,0)))
            return

        # Choose font
        font = pygame.font.Font(None, 144)
        # If monitor is on its side, rotate text CCW 90 degrees
        if not self.display_rotate:
            maybe_rotated_size=self.size
        else:
            maybe_rotated_size=(self.size[1], self.size[0])
        # Wrap and render text
        wrapped_text, text_height = self.wrap_text(msg, font, maybe_rotated_size)
        rendered_text = self.render_text(wrapped_text, text_height, 1, 1, font, color, bg, transparency, outline)

        if self.display_rotate:
            rendered_text = pygame.transform.rotate(rendered_text, 90)

        # Queue it for rendering during next apply()
        self.surface_list.append((rendered_text, (0,0)))

        # Save this rendering for later since this routine is so slow.
        self.set_message_cache(msg, color, bg, transparency, outline,
                               self.display_rotate, rendered_text)

    def msg(self, text):
        "Just a convenience wrapper to splat text to a blank screen"
        self.clear()
        self.show_message(text)
        self.apply()
        
    static_message_cache = {}
    def set_message_cache(self, msg, color, bg, transparency, outline, rotate, rendered_text):
        """Speed up for show_message which is called repeatedly during
            photobooth.py's show_counter() and doesn't need to be.
        """
        index=(msg, color, bg, transparency, outline, rotate)
        self.static_message_cache[index] = rendered_text

    def get_message_cache(self, msg, color, bg, transparency, outline, rotate):
        index=(msg, color, bg, transparency, outline, rotate)
        if index in self.static_message_cache:
            return self.static_message_cache[index]
        else:
            return None

    def show_button(self, text, pos, size=(0,0), color=(230,230,230), bg=(0,0,0), transparency=True, outline=(230,230,230)):
        # Choose font
        font = pygame.font.Font(None, 72)
        text_size = font.size(text)
        if size == (0,0):
            size = (text_size[0] + 4, text_size[1] + 4)
        offset = ( (size[0] - text_size[0]) // 2, (size[1] - text_size[1]) // 2 )

        # Create Surface object and fill it with the given background
        surface = pygame.Surface(self.size) 
        surface.fill(bg) 

        # Render text
        rendered_text = font.render(text, 1, color)
        surface.blit(rendered_text, pos)

        # Render outline
        pygame.draw.rect(surface, outline, (pos[0]-offset[0], pos[1]-offset[0], size[0], size[1]), 1)

        # Make background color transparent
        if transparency:
            surface.set_colorkey(bg)

        self.surface_list.append((surface, (0,0)))

    def wrap_text(self, msg, font, size):
        final_lines = []                   # resulting wrapped text
        requested_lines = msg.splitlines() # wrap input along line breaks
        accumulated_height = 0             # accumulated height

        # Form a series of lines
        for requested_line in requested_lines:
            # Handle too long lines
            if font.size(requested_line)[0] > size[0]:
                # Split at white spaces
                words = requested_line.split(' ')
                # if any of our words are too long to fit, trim them
                for word in words:
                    while font.size(word)[0] >= size[0]:
                        word = word[:-1]
                # Start a new line
                accumulated_line = ""
                # Put words on the line as long as they fit
                for word in words:
                    test_line = accumulated_line + word + " "
                    # Build the line while the words fit.   
                    if font.size(test_line)[0] < size[0]:
                        accumulated_line = test_line 
                    else:
                        # Start a new line
                        line_height = font.size(accumulated_line)[1]
                        if accumulated_height + line_height > size[1]:
                            break
                        else:
                            accumulated_height += line_height
                            final_lines.append(accumulated_line)
                            accumulated_line = word + " " 
                # Finish requested_line
                line_height = font.size(accumulated_line)[1]
                if accumulated_height + line_height > size[1]:
                    break
                else:
                    accumulated_height += line_height
                    final_lines.append(accumulated_line)
            # Line fits as it is
            else:
                accumulated_height += font.size(requested_line)[1] 
                final_lines.append(requested_line)

        # Check height of wrapped text
        if accumulated_height >= size[1]:
            raise GuiException("Wrapped text is too high to fit.")

        return final_lines, accumulated_height

    def render_text(self, text, text_height, valign, halign, font, color, bg, transparency, outline):
        if not self.display_rotate:
            maybe_rotated_size=self.size
        else:
            maybe_rotated_size=(self.size[1], self.size[0])
        # Determine vertical position
        if valign == 0:     # top aligned
            voffset = 0
        elif valign == 1:   # centered
            
            voffset = int((maybe_rotated_size[1] - text_height) / 2)
        elif valign == 2:   # bottom aligned
            voffset = maybe_rotated_size[1] - text_height
        else:
            raise GuiException("Invalid valign argument: " + str(valign))

        # Create Surface object and fill it with the given background
        surface = pygame.Surface(maybe_rotated_size) 
        surface.fill(bg) 

        # Blit one line after another
        accumulated_height = 0 
        for line in text: 
            maintext = font.render(line, 1, color)
            shadow = font.render(line, 1, outline)
            if halign == 0:     # left aligned
                hoffset = 0
            elif halign == 1:   # centered
                hoffset = (maybe_rotated_size[0] - maintext.get_width()) / 2
            elif halign == 2:   # right aligned
                hoffset = rect.width - maintext.get_width()
            else:
                raise GuiException("Invalid halign argument: " + str(justification))
            pos = (hoffset, voffset + accumulated_height)
            # Outline
            surface.blit(shadow, (pos[0]-1,pos[1]-1))
            surface.blit(shadow, (pos[0]-1,pos[1]+1))
            surface.blit(shadow, (pos[0]+1,pos[1]-1))
            surface.blit(shadow, (pos[0]+1,pos[1]+1))
            # Text
            surface.blit(maintext, pos)
            accumulated_height += font.size(line)[1]

        # Make background color transparent
        if transparency:
            surface.set_colorkey(bg)

        # Return the rendered surface
        return surface

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

    def teardown(self):
        pygame.quit()
