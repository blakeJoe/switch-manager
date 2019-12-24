#!/usr/bin/python
# -*- coding: UTF-8 -*

from driver.driver import get_driver


class HandlerPool(object):

    def __init__(self, switch, **kwargs):
        self.driver = get_driver(switch)

    def get_down_interfaces(self):
        self.driver.connect()
        each_res, both_res, result = self.driver.get_interface_status()
        self.driver.disconnect()
        return each_res, both_res, result



