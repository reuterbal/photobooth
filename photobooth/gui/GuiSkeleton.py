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

from .. import StateMachine


class GuiSkeleton:

    def __init__(self, communicator):

        super().__init__()
        self._comm = communicator

    def showError(self, state):

        raise NotImplementedError()

    def showWelcome(self, state):

        raise NotImplementedError()

    def showStartup(self, state):

        raise NotImplementedError()

    def showSettings(self, state):

        raise NotImplementedError()

    def showIdle(self, state):

        raise NotImplementedError()

    def showGreeter(self, state):

        raise NotImplementedError()

    def showCountdown(self, state):

        raise NotImplementedError()

    def showCapture(self, state):

        raise NotImplementedError()

    def showAssemble(self, state):

        raise NotImplementedError()

    def showReview(self, state):

        raise NotImplementedError()

    def showPostprocess(self, state):

        raise NotImplementedError()

    def teardown(self, state):

        raise NotImplementedError()

    def handleState(self, state):

        if isinstance(state, StateMachine.CameraEvent):
            self.updateCountdown(state)
        elif isinstance(state, StateMachine.ErrorState):
            self.showError(state)
        elif isinstance(state, StateMachine.WelcomeState):
            self.showWelcome(state)
        elif isinstance(state, StateMachine.StartupState):
            self.showStartup(state)
        elif isinstance(state, StateMachine.IdleState):
            self.showIdle(state)
        elif isinstance(state, StateMachine.GreeterState):
            self.showGreeter(state)
        elif isinstance(state, StateMachine.CountdownState):
            self.showCountdown(state)
        elif isinstance(state, StateMachine.CaptureState):
            self.showCapture(state)
        elif isinstance(state, StateMachine.AssembleState):
            self.showAssemble(state)
        elif isinstance(state, StateMachine.ReviewState):
            self.showReview(state)
        elif isinstance(state, StateMachine.PostprocessState):
            self.showPostprocess(state)
        elif isinstance(state, StateMachine.TeardownState):
            self.teardown(state)
