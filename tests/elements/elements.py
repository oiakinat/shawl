# -*- coding: utf-8 -*-
from shawl import BaseCollection, BaseElement


class InputElement(BaseElement):

    def fill_in(self, text: str):
        self.element.clear()
        self.element.send_keys(text)
        assert self.element.text == text


class ButtonElement(BaseElement):

    def click_and_wait(self):
        self.element.click()
        for _ in range(10):
            pass


class DivCollection(BaseCollection):

    def is_not_empty(self):
        assert self.collection


class LiCollection(BaseCollection):

    def is_not_empty(self):
        assert self.collection
