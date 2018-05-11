#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from time import localtime, strftime

from .PictureList import PictureList


class WorkerTask:

    def __init__(self, **kwargs):

        assert not kwargs


    def do(self, picture):

        raise NotImplementedError()



class PictureSaver(WorkerTask):

    def __init__(self, config):

        super().__init__()

        picture_basename = strftime(config.get('Picture', 'basename'), localtime())
        self._pic_list = PictureList(picture_basename)
        self._get_next_filename = self._pic_list.getNext


    @property
    def getNextFilename(self):

        return self._get_next_filename


    def do(self, picture):

        print('saving picture')
        picture.save(self.getNextFilename(), 'JPEG')



class Worker:

    def __init__(self, config, queue):

        self._queue = queue


    def run(self):

        for func, args in iter(self._queue.get, ('teardown', None)):
            func(*args)

        return 0
