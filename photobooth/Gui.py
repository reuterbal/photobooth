#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class Gui:

    def __init__(self):

        pass


    def run(self, send, recv):

        raise NotImplementedError()



class GuiState:

    def __init__(self, **kwargs):

        assert not kwargs


class IdleState(GuiState):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)



class PictureState(GuiState):

    def __init__(self, picture, **kwargs):

        super().__init__(**kwargs)

        self._pic = picture


    @property
    def picture(self):

        return self._pic


    @picture.setter
    def picture(self, picture):

        self._pic = picture


class MessageState(GuiState):

    def __init__(self, message, **kwargs):

        super().__init__(**kwargs)

        self._msg = message


    @property
    def message(self):

        return self._msg


    @message.setter
    def message(self, message):

        if not isinstance(message, str):
            raise ValueError('Message must be a string')

        self._msg = message



class PoseState(GuiState):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class PreviewState(MessageState, PictureState):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)
