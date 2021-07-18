# -*- coding: utf-8 -*-
from shawl import BasePage


class CustomPage(BasePage):

    def click_on_search_btn(self):
        assert self.search_button.is_visible()
        self.search_button.click()
