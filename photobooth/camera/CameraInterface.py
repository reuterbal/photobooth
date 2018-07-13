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


class CameraInterface:

    def __init__(self):

        self.hasPreview = False
        self.hasIdle = False

    def __enter__(self):

        return self

    def __exit__(self, exc_type, exc_value, traceback):

        self.cleanup()

    def cleanup(self):

        pass

    @property
    def hasPreview(self):

        return self._has_preview

    @hasPreview.setter
    def hasPreview(self, value):

        if not isinstance(value, bool):
            raise ValueError('Expected bool')

        self._has_preview = value

    @property
    def hasIdle(self):

        return self._has_idle

    @hasIdle.setter
    def hasIdle(self, value):

        if not isinstance(value, bool):
            raise ValueError('Expected bool')

        self._has_idle = value

    def setActive(self):

        if not self.hasIdle:
            pass
        else:
            raise NotImplementedError()

    def setIdle(self):

        if not self.hasIdle:
            raise RuntimeError('Camera does not have idle functionality')

        raise NotImplementedError()

    def getPreview(self):

        if not self.hasPreview:
            raise RuntimeError('Camera does not have preview functionality')

        raise NotImplementedError()

    def getPicture(self):

        raise NotImplementedError()
