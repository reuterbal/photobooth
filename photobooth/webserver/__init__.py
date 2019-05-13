#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Photobooth - a flexible photo booth software
# Copyright (C) 2019  Balthasar Reuter <photobooth at re - web dot eu>
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
import sys
import threading

from .. import StateMachine
from ..util import lookup_and_import
from ..Threading import Workers

# Available webserver modules (config name, module name, class name)
modules = (('SimpleHttpServer', 'SimpleHttpServer', None), )


class Webserver:

    def __init__(self, config, comm):

        self._comm = comm
        self._server = None

        self._initServer(config)

    def _initServer(self, config):

        ServerModule = lookup_and_import(
            modules, config.get('Webserver', 'module'), 'webserver')

        self._server = threading.Thread(target=ServerModule.run, args=[config])

    def run(self):

        self._server.start()

        for state in self._comm.iter(Workers.WEBSERVER):
            self.handle(state)

    def handle(self, state):

        if isinstance(state, StateMachine.TeardownState):
            self.teardown(state)

    def teardown(self, state):

        sys.exit(0)
