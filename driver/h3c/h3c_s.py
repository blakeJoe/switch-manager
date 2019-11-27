import re
from driver.telnet import TelnetClient
from driver.ssh import SSHClient
from string import strip
from utils import remove_null, ip_to_segment


class H3CS:

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
            self.client.login(switch_type='h3c')
        self.client.execute('screen-length disable')
        self.client.execute('system-view')

    def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None

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

    def commit(self):
        pass

    def save(self):
        cmd = [
            'save',
            'y',
            'flash:/startup.cfg',
            'y'
        ]
        self._execute(cmd)

    '*******************************check**********************************'
    def has_port(self, port_name):
        cmd = [
            'interface {}'.format(port_name),
            'display this'

        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        for line in result:
            if port_name in line:
                lines = line.split()
                print(lines)

    def get_port_link_type(self, port_name):
        cmd = [
            'interface {}'.format(port_name),
            'display this'
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        for line in result:
            if 'port link-type' in line:
                line = line.split()
                return line[2]
        return 'access'

    def get_track_entry_number(self, remote_ip, local_ip):
        cmd = [
            'display current-configuration | include {}'.format(remote_ip)
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        for line in result:
            if 'remote ip {} local ip {}'.format(remote_ip, local_ip) in line:
                return line.split(' ')[2]
        return None

    def get_track_entry_number_list(self, vlan_id=None, local_ip=None):
        cmd = [
            'display current-configuration | include track'
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        number_list = []
        for line in result:
            if vlan_id:
                if 'Vlan-interface{}'.format(vlan_id) in line:
                    if local_ip not in line:
                        number_list.append(line.split(' ')[2])
            else:
                if 'bfd echo' in line:
                    number_list.append(line.split(' ')[2])
        return number_list

    def get_interface_status(self, no_processing=False):
        count = 0
        cmd = [
            'display interface brief'
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        both_down_intf = []
        one_down_intf = []
        if no_processing:
            return one_down_intf, both_down_intf, result
        else:
            for line in result:
                line = line.split()
                if line[0] == 'Brief':
                    if count == 1:
                        break
                    else:
                        count += 1
                        continue
                if len(line) > 3:
                    if line[1] == 'DOWN' or line[2] == 'DOWN':
                        if line[1] == 'DOWN' and line[2] == 'DOWN':
                            both_down_intf.append(line[0])
                        elif line[1] == 'ADM':
                            pass
                        else:
                            one_down_intf.append(line[0])
            return one_down_intf, both_down_intf, result

    def get_vlan_list(self):
        cmd = [
            'display vlan static'
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        result = result[2].split(',')
        result = list(map(strip, result))
        return result

    def get_vlanif_ip(self, vlan_id, type):
        cmd = [
            'display current-configuration interface Vlan-interface {}'.format(vlan_id)
        ]
        ip_address = []
        ip = None
        netmask = None

        try:
            result = self._execute(cmd)
        except:
            return ip_address
        result = re.split('[\r\n]', result)
        for line in result:
            ip_pattern = re.compile(r'((?=.*ip address).*)')
            if ip_pattern.search(line):
                ip = re.search('(ip address\s+)(.*)', line, re.S).group(2)
                ip_address.append(ip)
        for line in ip_address:
            if type == 'net':
                if 'sub' not in line:
                    line = line.split(' ')
                    ip = line[0]
                    netmask = line[1]
            else:
                if 'sub' in line:
                    line = line.split(' ')
                    ip = line[0]
                    netmask = line[1]
        return ip, netmask

    def has_ip_prefix(self, name, ip, mask):
        cmd = [
            'dis cur | include {}'.format(name)
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        prefix = ' ip prefix-list {} index (\w+) permit (\w+).(\w+).(\w+).(\w+) (\w+)'.format(name)
        for line in result:
            if 'ip prefix-list' in line:
                res_prefix = re.match(prefix, line)
                if res_prefix:
                    print '{}.{}.{}.{}'.format(res_prefix.group(2), res_prefix.group(3), res_prefix.group(4),
                                            res_prefix.group(5))
                    print ip_to_segment(ip, mask)
                    print "=========================="
                    print res_prefix.group(6)
                    print str(mask)
                    if '{}.{}.{}.{}'.format(res_prefix.group(2), res_prefix.group(3), res_prefix.group(4),
                                            res_prefix.group(5)) == ip_to_segment(ip, mask) and \
                            res_prefix.group(6) == str(mask):
                        return res_prefix.group(1)
        return None

    def get_time(self):
        cmd = [
            'display clock'
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        if len(result) > 1:
            return result[1]
        else:
            return 'None'

    def get_clock_status(self, sw_name):
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
            'dis stp'
        ]
        result = self._execute(cmd)
        if 'STP is not configured' in result:
            return True
        else:
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
        return [result[1][:result[1].index('%')+1].strip(),
                result[2][:result[2].index('%') + 1].strip(),
                result[3][:result[3].index('%') + 1].strip()]

    '*******************************config**********************************'
    def shutdown_interface(self, interface):
        cmd = [
            'interface {}'.format(interface),
            'shutdown',
            'quit'
        ]
        self._execute(cmd)
