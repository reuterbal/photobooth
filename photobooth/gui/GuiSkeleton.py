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

from . import GuiState

from .. import StateMachine


class GuiSkeleton:

    def __init__(self, communicator):

        super().__init__()
        self._comm = communicator

    @property
    def idle(self):

        return self._idle

    @idle.setter
    def idle(self, handle):

        if not callable(handle):
            raise ValueError('Function handle for "idle" must be callable')

        self._idle = handle

    @property
    def trigger(self):

        return self._trigger

    @trigger.setter
    def trigger(self, handle):

        if not callable(handle):
            raise ValueError('Function handle for "trigger" must be callable')

        self._trigger = handle

    @property
    def greeter(self):

        return self._greeter

    @greeter.setter
    def greeter(self, handle):

        if not callable(handle):
            raise ValueError('Function handle for "greeter" must be callable')

        self._greeter = handle

    @property
    def countdown(self):

        return self._countdown

    @countdown.setter
    def countdown(self, handle):

        if not callable(handle):
            raise ValueError(('Function handle for "countdown" must be '
                              'callable'))

        self._countdown = handle

    @property
    def preview(self):

        return self._preview

    @preview.setter
    def preview(self, handle):

        if not callable(handle):
            raise ValueError('Function handle for "preview" must be callable')

        self._preview = handle

    @property
    def pose(self):

        return self._pose

    @pose.setter
    def pose(self, handle):

        if not callable(handle):
            raise ValueError('Function handle for "pose" must be callable')

        self._pose = handle

    @property
    def assemble(self):

        return self._assemble

    @assemble.setter
    def assemble(self, handle):

        if not callable(handle):
            raise ValueError('Function handle for "assemble" must be callable')

        self._assemble = handle

    @property
    def review(self):

        return self._review

    @review.setter
    def review(self, handle):

        if not callable(handle):
            raise ValueError('Function handle for "review" must be callable')

        self._review = handle

    @property
    def teardown(self):

        return self._teardown

    @teardown.setter
    def teardown(self, handle):

        if not callable(handle):
            raise ValueError('Function handle for "teardown" must be callable')

        self._teardown = handle

    @property
    def error(self):

        return self._error

    @error.setter
    def error(self, handle):

        if not callable(handle):
            raise ValueError('Function handle for "error" must be callable')

        self._error = handle

    def handleState(self, state):

        if not isinstance(state, GuiState.GuiState):
            raise ValueError('Not a GuiState object received')

        if isinstance(state, GuiState.IdleState):
            self.idle(state)
        elif isinstance(state, GuiState.TriggerState):
            self.trigger(state)
        elif isinstance(state, GuiState.GreeterState):
            self.greeter(state)
        elif isinstance(state, GuiState.CountdownState):
            self.countdown(state)
        elif isinstance(state, GuiState.PreviewState):
            self.preview(state)
        elif isinstance(state, GuiState.PoseState):
            self.pose(state)
        elif isinstance(state, GuiState.AssembleState):
            self.assemble(state)
        elif isinstance(state, GuiState.ReviewState):
            self.review(state)
        elif isinstance(state, GuiState.TeardownState):
            self.teardown(state)
        elif isinstance(state, GuiState.ErrorState):
            self.error(state)
        else:
            raise ValueError('Unknown state received')
