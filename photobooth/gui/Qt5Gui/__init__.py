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

# Available style sheets as tuples of (style name, style file)
styles = (('default', 'stylesheets/default.qss'),
          ('dark (1024 x 600 px)', 'stylesheets/dark-1024x600.qss'),
          ('dark (800 x 600 px)', 'stylesheets/dark-800x600.qss'),
          ('pastel (1024 x 600 px)', 'stylesheets/pastel-1024x600.qss'),
          ('pastel (800 x 600 px)', 'stylesheets/pastel-800x600.qss'))

from .PyQt5Gui import PyQt5Gui  # noqa
