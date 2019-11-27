#!/usr/bin/python
# -*- coding: UTF-8 -*

import re
from switch import Switch
from device import Device
from concurrent.futures import ThreadPoolExecutor


def main():
    """
    open('G:/docu/has.txt')
    open('G:/docu/switch.txt')
    """
    with open('G:/docu/switch.txt', 'r') as f:
        switch_list = f.readlines()
    with ThreadPoolExecutor(20) as executor:
        for switch_info in switch_list:
            switch_info = re.split(r'[\t\n]', switch_info)
            sw = Switch(name=switch_info[0], m_ip=switch_info[1])
            dev = Device(sw)
            executor.submit(dev.run)


if __name__ == '__main__':
    main()

