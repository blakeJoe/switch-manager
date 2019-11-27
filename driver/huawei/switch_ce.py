import re
import time
from driver.telnet import TelnetClient
from driver.ssh import SSHClient
from driver.utils import vlan_str_to_list, remove_null, get_vsi_name, get_vsi_by_vsi_name, get_port_list, \
                        get_vpn_instance_list, ip_to_segment, int_netmask


class SwitchCE:

    def __init__(self, switch):
        self.ip = switch.m_ip
        self.protocol = switch.protocol
        self.port = switch.port
        self.username = switch.username
        self.password = switch.password
        self.client = None

    def _execute(self, commands):
        result = None
        for cmd in commands:
            result = self.client.execute(cmd)
        return result

    def connect(self):
        if 'SSH' == self.protocol:
            self.client = SSHClient(ip=self.ip,
                                    username=self.username,
                                    password=self.password,
                                    port=self.port)
            self.client.login()
        else:
            self.client = TelnetClient(ip=self.ip,
                                       username=self.username,
                                       password=self.password,
                                       port=self.port)
            self.client.login()
        time.sleep(1)
        self.client.execute('screen-length 0 temporary')
        self.client.execute('system-view')

    def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None

    def commit(self):
        cmd = [
            'commit'
        ]
        self._execute(cmd)

    def return_root(self):
        cmd = [
            'return',
            'system-view'
        ]
        self._execute(cmd)

    def quit(self):
        cmd = [
            'quit'
        ]
        self._execute(cmd)

    def save(self):
        cmd = [
            'save',
            'y'
        ]
        self._execute(cmd)

    '*******************************check**********************************'
    def get_mpls_te_tunnel_num(self):
        cmd = [
            'dis  mpls te tunnel | count'
        ]
        result = self._execute(cmd)
        if 'Error' in result:
            return result
        else:
            r = 'Total lines: (\w+).'
            res = re.match(r, result)
            return res.group(1)

    def get_tedb_network_lsa(self):
        cmd = [
            'dis mpls te cspf tedb network-lsa'
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        if result:
            if 'Error: Failed to pass the authorization.' in result:
                return result
            elif " % Unrecognized command found at '^' position." in result:
                return 'h3c'
            else:
                result = result[0:3]
                if 'IGP-Type' in result[2]:
                    return result
                else:
                    return result[:2]
        else:
            return None

    def has_vsi(self, vsi):
        cmd = [
            'display vpls vsi | include {}'.format(vsi),
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        for line in result:
            if vsi in line:
                lines = line.split()
                if lines[0] == vsi:
                    return True
        return False

    def get_interface_status(self, no_processing=False):
        cmd = [
            'display interface brief'
        ]
        one_down_intf = []
        both_down_intf = []
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        if no_processing:
            return one_down_intf, both_down_intf, result
        else:
            for line in result:
                line = line.split()
                if len(line) > 4:
                    if line[1] == 'down' or line[2] == 'down':
                        if line[1] == 'down' and line[2] == 'down':
                            both_down_intf.append(line[0])
                        elif line[1] == '*down':
                            pass
                        else:
                            one_down_intf.append(line[0])
            return one_down_intf, both_down_intf, result

    def get_time(self):
        cmd = [
            'display clock'
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        return result[2]

    def get_clock_status(self, sw_name):
        if '12804' in sw_name:
            cmd = [
                'display ntp status'
            ]
        else:
            cmd = [
                'display ntp-service status'
            ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        return result[0]

    def get_ntp_conf(self):
        cmd = [
            'dis cu | include ntp'
        ]
        result = self._execute(cmd)
        return result

    def get_stp_status(self):
        cmd = [
            'display stp'
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        if result and isinstance(result, list) and 'Disabled' in result[0]:
            return True
        else:
            return False

    def get_cpu_status(self):
        cmd = [
            'display cpu'
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        res = result[2].split(':')
        return [res[1][:res[1].index('%')+1].strip(),
                res[2][:res[2].index('%') + 1].strip(),
                res[3][:res[3].index('%') + 1].strip()]

    '*******************************config**********************************'
    def shutdown_interface(self, interface):
        cmd = [
            'interface {}'.format(interface),
            'shutdown',
            'quit'
        ]
        self._execute(cmd)