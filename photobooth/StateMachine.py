#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Photobooth - a flexible photo booth software
# Copyright (C) 2018  Balthasar Reuter <photobooth at re - web dot eu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import logging

from . import util


class Context:

    def __init__(self, communicator, omit_welcome=False):

        super().__init__()
        self._comm = communicator
        self.is_running = False
        if omit_welcome:
            self.state = StartupState()
        else:
            self.state = WelcomeState()

    @property
    def is_running(self):

        return self._is_running

    @is_running.setter
    def is_running(self, running):

        if not isinstance(running, bool):
            raise TypeError('is_running must be a bool')

        self._is_running = running

    @property
    def state(self):

        return self._state

    @state.setter
    def state(self, new_state):

        if not isinstance(new_state, State):
            raise TypeError('state must implement State')

        logging.debug('New state is "{}"'.format(new_state))

        self._state = new_state
        self._comm.bcast(self._state)

    def handleEvent(self, event):

        if not isinstance(event, Event):
            raise TypeError('event must implement Event')

        logging.debug('Handling event "{}"'.format(event))

        if isinstance(event, ErrorEvent):
            self.state = ErrorState(event.origin, event.message, self.state,
                                    self.is_running)
        elif isinstance(event, TeardownEvent):
            self.is_running = False
            self.state = TeardownState(event.target)
            if event.target == TeardownEvent.EXIT:
                self._comm.bcast(None)
                return 0
            elif event.target == TeardownEvent.RESTART:
                self._comm.bcast(None)
                return 123
        else:
            self.state.handleEvent(event, self)


class Event:

    def __init__(self, name):

        super().__init__()
        self.name = name

    def __str__(self):

        return self.name

    @property
    def name(self):

        return self._name

    @name.setter
    def name(self, name):

        if not isinstance(name, str):
            raise TypeError('name must be a str')

        self._name = name


class ErrorEvent(Event):

    def __init__(self, origin, message):

        super().__init__('Error')
        self.origin = origin
        self.message = message

    def __str__(self):

        return self.origin + ': ' + self.message

    @property
    def origin(self):

        return self._origin

    @origin.setter
    def origin(self, origin):

        if not isinstance(origin, str):
            raise TypeError('origin must be a string')

        self._origin = origin

    @property
    def message(self):

        return self._message

    @message.setter
    def message(self, message):

        if not isinstance(message, str):
            raise TypeError('message must be a string')

        self._message = message


class TeardownEvent(Event):

    EXIT = 0
    RESTART = 1
    WELCOME = 2

    def __init__(self, target):

        self._target = target
        super().__init__('Teardown({})'.format(target))

    @property
    def target(self):

        return self._target


class GuiEvent(Event):

    pass


class GpioEvent(Event):

    pass


class CameraEvent(Event):

    def __init__(self, name, picture=None):

        super().__init__(name)
        self._picture = picture

    @property
    def picture(self):

        return self._picture


class WorkerEvent(Event):

    pass


class State:

    def __init__(self):

        super().__init__()
        self.update()

    def __str__(self):

        return type(self).__name__

    def update(self):

        pass

    def handleEvent(self, event, context):

        raise NotImplementedError()


class ErrorState(State):

    def __init__(self, origin, message, old_state, is_running):

        self.origin = origin
        self.message = message
        self.old_state = old_state
        self.is_running = is_running
        super().__init__()

    @property
    def origin(self):

        return self._origin

    @origin.setter
    def origin(self, origin):

        if not isinstance(origin, str):
            raise TypeError('origin must be a string')

        self._origin = origin

    @property
    def message(self):

        return self._message

    @message.setter
    def message(self, message):

        if not isinstance(message, str):
            raise TypeError('message must be a string')

        self._message = message

    @property
    def old_state(self):

        return self._old_state

    @old_state.setter
    def old_state(self, old_state):

        if not isinstance(old_state, State):
            raise TypeError('old_state must be derived from State')

        self._old_state = old_state

    @property
    def is_running(self):

        return self._is_running

    @is_running.setter
    def is_running(self, running):

        if not isinstance(running, bool):
            raise TypeError('is_running must be a bool')

        self._is_running = running

    def handleEvent(self, event, context):

        if isinstance(event, GuiEvent) and event.name == 'retry':
            context.state = self.old_state
            context.state.update()
        elif isinstance(event, GuiEvent) and event.name == 'abort':
            if self.is_running:
                context.state = IdleState()
            else:
                context.state = TeardownState(TeardownEvent.WELCOME)
        else:
            raise TypeError('Unknown Event type "{}"'.format(event))


class TeardownState(State):

    def __init__(self, target):

        super().__init__()
        self._target = target

    @property
    def target(self):

        return self._target

    def handleEvent(self, event, context):

        if self._target == TeardownEvent.WELCOME:
            if isinstance(event, GuiEvent) and event.name == 'welcome':
                context.state = WelcomeState()
            else:
                raise ValueError('Unknown GuiEvent "{}"'.format(event.name))
        else:
            raise TypeError('Unknown Event type "{}"'.format(event))


class WelcomeState(State):

    def __init__(self):

        super().__init__()

    def handleEvent(self, event, context):

        if isinstance(event, GuiEvent):
            if event.name == 'start':
                context.state = StartupState()
            elif event.name == 'exit':
                context.state = TeardownState(TeardownEvent.EXIT)
        else:
            raise TypeError('Unknown Event type "{}"'.format(event))


class StartupState(State):

    def __init__(self):

        super().__init__()

    def handleEvent(self, event, context):

        if isinstance(event, CameraEvent) and event.name == 'ready':
            context.is_running = True
            context.state = IdleState()
        else:
            raise TypeError('Unknown Event type "{}"'.format(event))


class IdleState(State):

    def __init__(self):

        super().__init__()

    def handleEvent(self, event, context):

        if ((isinstance(event, GuiEvent) or isinstance(event, GpioEvent)) and
           event.name == 'trigger'):
            context.state = GreeterState()
        else:
            raise TypeError('Unknown Event type "{}"'.format(event))


class GreeterState(State):

    def __init__(self):

        super().__init__()

    def handleEvent(self, event, context):

        if ((isinstance(event, GuiEvent) or isinstance(event, GpioEvent)) and
           event.name == 'countdown'):
            context.state = CountdownState(1)
        else:
            raise TypeError('Unknown Event type "{}"'.format(event))


class CountdownState(State):

    def __init__(self, num_picture):

        super().__init__()

        self._num_picture = num_picture

    @property
    def num_picture(self):

        return self._num_picture

    def handleEvent(self, event, context):

        if isinstance(event, GuiEvent) and event.name == 'countdown':
            pass
        elif isinstance(event, GuiEvent) and event.name == 'capture':
            context.state = CaptureState(self.num_picture)
        else:
            raise TypeError('Unknown Event type "{}"'.format(event))


class CaptureState(State):

    def __init__(self, num_picture):

        super().__init__()

        self._num_picture = num_picture

    @property
    def num_picture(self):

        return self._num_picture

    def handleEvent(self, event, context):

        if isinstance(event, CameraEvent) and event.name == 'countdown':
            context.state = CountdownState(self.num_picture + 1)
        elif isinstance(event, CameraEvent) and event.name == 'assemble':
            context.state = AssembleState()
        else:
            raise TypeError('Unknown Event type "{}"'.format(event))


class AssembleState(State):

    def __init__(self):

        super().__init__()

    def handleEvent(self, event, context):

        if isinstance(event, CameraEvent) and event.name == 'review':
            context.state = ReviewState(event.picture)
        else:
            raise TypeError('Unknown Event type "{}"'.format(event))


class ReviewState(State):

    def __init__(self, picture):

        super().__init__()
        self._picture = picture

    @property
    def picture(self):

        return self._picture

    def handleEvent(self, event, context):

        if isinstance(event, GuiEvent) and event.name == 'postprocess':
            context.state = PostprocessState()
        else:
            raise TypeError('Unknown Event type "{}"'.format(event))


class PostprocessState(State):

    def __init__(self):

        super().__init__()

    def handleEvent(self, event, context):

        if ((isinstance(event, GuiEvent) or isinstance(event, GpioEvent)) and
           event.name == 'idle'):
            context.state = IdleState()
        else:
            raise TypeError('Unknown Event type "{}"'.format(event))
