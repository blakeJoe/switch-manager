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

    def shutdown_interfaces(self):
        shutdown_intfs = []
        self.driver.connect()
        _, both_res, _ = self.driver.get_interface_status()

        self.driver.return_root()
        for intf in both_res:
            if 'GigabitEthernet' in intf or '40GE' in intf or '100GE' in intf \
                    or 'HGE' in intf or 'XGE' in intf or '10GE' in intf:
                self.driver.shutdown_interface(intf)
                shutdown_intfs.append(intf)

        self.driver.commit()
        self.driver.save()

        _, _, result = self.driver.get_interface_status(no_processing=True)
        self.driver.disconnect()
        return result, shutdown_intfs

