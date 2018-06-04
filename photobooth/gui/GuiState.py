#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class GuiState:

    def __init__(self, **kwargs):

        assert not kwargs


class ErrorState(GuiState):

    def __init__(self, title, message, **kwargs):

        super().__init__(**kwargs)

        self.title = title
        self.message = message

    @property
    def title(self):

        return self._title

    @title.setter
    def title(self, title):

        self._title = title

    @property
    def message(self):

        return self._message

    @message.setter
    def message(self, message):

        self._message = message


class IdleState(GuiState):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class PictureState(GuiState):

    def __init__(self, picture, **kwargs):

        super().__init__(**kwargs)

        self.picture = picture

    @property
    def picture(self):

        return self._pic

    @picture.setter
    def picture(self, picture):

        self._pic = picture


class MessageState(GuiState):

    def __init__(self, message, **kwargs):

        super().__init__(**kwargs)

        self.message = message

    @property
    def message(self):

        return self._msg

    @message.setter
    def message(self, message):

        if not isinstance(message, str):
            raise ValueError('Message must be a string')

        self._msg = message


class TriggerState(GuiState):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class GreeterState(GuiState):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class PoseState(GuiState):

    def __init__(self, num_picture, **kwargs):

        super().__init__(**kwargs)

        self.num_picture = num_picture

    @property
    def num_picture(self):

        return self._num_picture

    @num_picture.setter
    def num_picture(self, num_picture):

        if not isinstance(num_picture, int):
            raise ValueError('Picture number must be an integer')

        self._num_picture = num_picture


class AssembleState(GuiState):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class CountdownState(GuiState):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class PreviewState(PictureState):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class TeardownState(GuiState):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class PrintState(GuiState):

    def __init__(self, handler, confirmed, **kwargs):

        super().__init__(**kwargs)

        self.handler = handler
        self.confirmed = confirmed

    @property
    def handler(self):

        return self._handler

    @handler.setter
    def handler(self, handler):

        if not callable(handler):
            raise ValueError('handler must be callable')

        self._handler = handler

    @property
    def confirmed(self):

        return self._confirmed

    @confirmed.setter
    def confirmed(self, confirmed):

        if not isinstance(confirmed, bool):
            raise ValueError('confirmed status must be bool')

        self._confirmed = confirmed
