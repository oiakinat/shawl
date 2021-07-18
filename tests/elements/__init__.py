# -*- coding: utf-8 -*-
from shawl import BaseCollection, BaseElement


class InputElement(BaseElement):

    def fill_in(self, text: str):
        self.element.clear()
        self.element.send_keys(text)
        assert self.element.text == text

    def only_for_init(self, text: str):
        self.element.clear()
        self.element.send_keys(text)
        assert self.element.text == text


class DivCollection(BaseCollection):

    def is_not_empty(self):
        assert self.collection

    def only_for_init(self):
        assert self.collection
