#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Available printer modules as tuples of (config name, module name, class name)
modules = (
    ('PyQt5', 'PrinterPyQt5', 'PrinterPyQt5'), )


class Printer:

    def __init__(self, page_size):

        self.pageSize = page_size

    @property
    def pageSize(self):

        return self._page_size

    @pageSize.setter
    def pageSize(self, page_size):

        if not isinstance(page_size, (list, tuple)) or len(page_size) != 2:
            raise ValueError('page_size must be a list/tuple of length 2')

        self._page_size = page_size

    def print(self, picture):

        raise NotImplementedError('print function not implemented!')
