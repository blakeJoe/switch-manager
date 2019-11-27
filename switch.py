#!/usr/bin/python
# -*- coding: UTF-8 -*

from metadata import SWITCH_FILE_PATH, TEST_SWITCH_FILE_PATH
from concurrent.futures import ThreadPoolExecutor

class Switch(object):

    def __init__(self, name, m_ip, **kwargs):
        self.name = name
        self.switch_type = None
        self.sub_type = None
        self.m_ip = m_ip
        self.protocol = "TELNET"
        self.port = 23
        "-----------online-----------"
        self.username = "sdn-server"
        self.password = "SDNsyscloud20!7"
        "-----------test-----------"
        # self.username = "admin"
        # self.password = "syscloud@123"


class SwitchPool(object):

    def __init__(self):

        self.switches = []
        self.switches_iter = None
        self.get_switches()
        self.init_switches_iter()

    def get_switches(self):
        with open(TEST_SWITCH_FILE_PATH, mode='r') as f:
        # with open(SWITCH_FILE_PATH, mode='r') as f:
            content = f.read()
            f.close()
        content = content.split()
        for i in range(len(content)//2):
            self.switches.append(Switch(content[2*i], content[2*i+1]))
        print("switches load success!")

    def init_switches_iter(self):
        self.switches_iter = iter(self.switches)
        print("init switches iter success")

    def get_next_switch(self):
        try:
            switch_obj = next(self.switches_iter)
            return switch_obj
        except StopIteration:
            self.init_switches_iter()
            return 'traverse switch complete!'










