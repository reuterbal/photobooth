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

import importlib

from PIL import Image


def lookup_and_import(module_list, name, package=None):

    result = next(((mod_name, class_name)
                   for config_name, mod_name, class_name in module_list
                   if name == config_name), None)

    if package is None:
        import_module = importlib.import_module('photobooth.' + result[0])
    else:
        import_module = importlib.import_module(
            'photobooth.' + package + '.' + result[0])

    if result[1] is None:
        return import_module
    else:
        return getattr(import_module, result[1])


def pickle_image(image):

    if image is None:
        return None
    else:
        image_data = (image.mode, image.size, image.tobytes())
        return image_data


def unpickle_image(image_data):

    if image_data is None:
        return None
    else:
        image = Image.frombytes(*image_data)
        return image
