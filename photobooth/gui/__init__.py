#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Available gui modules as tuples of (config name, module name, class name)
modules = ( ('qt5', 'PyQt5Gui', 'PyQt5Gui'), )


class Gui:

    def __init__(self):

        pass


    def run(self, send, recv):

        raise NotImplementedError()



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

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class AssembleState(GuiState):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class CountdownState(GuiState):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class PreviewState(MessageState, PictureState):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

class TeardownState(GuiState):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)
