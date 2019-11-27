import re
import time
from driver.telnet import TelnetClient
from driver.sw_ssh import SSHClient
from utils import vlan_str_to_list, remove_null, get_vsi_name, get_vsi_by_vsi_name, get_port_list, \
                        get_vpn_instance_list, ip_to_segment, int_netmask


class SwitchS:

    def __init__(self, switch):
        self.ip = switch.m_ip
        self.protocol = switch.protocol
        self.port = switch.port
        self.username = switch.username
        self.password = switch.password
        self.client = None
        self.client_sysview = False

    def _execute(self, commands):
        result = None
        for cmd in commands:
            result = self.client.execute(cmd, sysview=self.client_sysview)
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
        self.client_sysview = True
        self.client.execute('system-view', sysview=self.client_sysview)

    def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None

    def commit(self):
        pass

    def return_root(self):
        self.client_sysview = True
        cmd = [
            'return',
            'system-view'
        ]
        self._execute(cmd)

    def quit(self):
        self.client_sysview = False
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
    def get_vlan_list(self):
        vlan_list = []
        cmd = [
            'display vlan sum'
        ]
        result = self._execute(cmd)
        print result
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        for line in result[2:]:
            if 'Dynamic VLAN:' in line:
                break
            vlan_list.append(line)
        vlan_str = ''.join(vlan_list[0:])
        vlan_list = vlan_str_to_list(vlan_str)
        return vlan_list

    def get_vsi_dict(self):
        vsi_dict = {}
        cmd = [
            'display vsi'
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        for line in result[7:]:
            vsi_name = get_vsi_name(line)
            if 'vsi' in vsi_name:
                vsi = get_vsi_by_vsi_name(vsi_name)
            else:
                cmd = [
                    'display vsi name {} verbose'.format(vsi_name)
                ]
                result = self._execute(cmd)
                result = re.split('[\r\n]', result)
                for line in result:
                    if 'VSI ID' in line:
                        lint_l = line.split(' ')
                        vsi = lint_l[-1]
            vsi_dict[vsi_name] = int(vsi)
        return vsi_dict

    def get_vlan_port_state(self, vlan):
        data = {}
        port_state = {}
        cmd = [
            'display vlan {}'.format(vlan)
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        port_list = get_port_list(result)
        for port_num in port_list:
            cmd = [
                'display interface XGigabitEthernet 0/0/{}'.format(port_num)
            ]
            result = self._execute(cmd)
            result = re.split('[\r\n]', result)
            result = list(result[0])
            if result[37] == ' ':
                port_state[port_num] = ''.join(result[38:])
            else:
                port_state[port_num] = ''.join(result[39:])
        data[vlan] = port_state
        return data

    def get_vlanif_config(self, vlan):
        data = {}
        cmd = [
            'display current-configuration interface vlan {}'.format(vlan)
        ]
        result = self._execute(cmd)
        if 'Error' in result:
            result = None
        data[vlan] = result
        return data

    def get_vlan_config(self, vlan):
        data = {}
        cmd = [
            'dis current-configuration configuration vlan {}'.format(vlan)
        ]
        result = self._execute(cmd)
        if 'Error' in result:
            result = None
        data[vlan] = result
        return data

    def get_vsi_state(self, vsi_name):
        data = {}
        state = {}
        interface = {}
        cmd = [
            'display vsi name {} verbose'.format(vsi_name)
        ]
        result = self._execute(cmd)
        if not result or 'Error' in result:
            state = None
        else:
            result = re.split('[\r\n]', result)
            result = remove_null(result)
            state_line = remove_null(list(result[16]))
            state['state'] = ''.join(state_line[9:])
            if len(result) > 33:
                interface_name_line = remove_null(list(result[33]))
                interface_state_line = remove_null(list(result[34]))
                interface['name'] = ''.join(interface_name_line[14:])
                interface['state'] = ''.join(interface_state_line[6:])
                state['interface'] = interface
            else:
                state['interface'] = None
        data[vsi_name] = state
        return data

    def get_vpn_instance_dict(self):
        data = {}
        cmd = [
            'display ip vpn-instance'
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        vpn_instance_list = get_vpn_instance_list(result[4:])
        for name in vpn_instance_list:
            if '_VPN' in name:
                vrf_id = int(''.join(list(name)[14:]))
            else:
                vrf_id = None
            data[name] = vrf_id
        return data

    def get_vpn_instance_state(self, vpn_instance):
        data = {}
        vpn_instance_config = {}
        interface = {}
        cmd = [
            'display ip vpn-instance verbose {}'.format(vpn_instance)
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        for line in result:
            if 'Interfaces' in line:
                interface['name'] = ''.join(list(line)[15:])
                cmd = [
                    'display interface {}'.format(interface['name'])
                ]
                result = self._execute(cmd)
                result = re.split('[\r\n]', result)
                result = list(result[0])
                if 'Vlanif' in interface['name']:
                    interface['state'] = ''.join(result[27:])
                else:
                    if result[37] == ' ':
                        interface['state'] = ''.join(result[38:])
                    else:
                        interface['state'] = ''.join(result[39:])
            elif 'Route Distinguisher' in line:
                vpn_instance_config['RD'] = ''.join(list(line)[24:])
            elif 'Export VPN Targets' in line:
                vpn_instance_config['Export VPN Targets'] = ''.join(list(line)[24:])
            elif 'Import VPN Targets' in line:
                vpn_instance_config['Import VPN Targets'] = ''.join(list(line)[24:])
        vpn_instance_config['interface'] = interface
        data[vpn_instance] = vpn_instance_config
        return data

    def get_interface_with_mplse_te_list(self):
        interface_list = []
        cmd = [
            'dis current-configuration interface'
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        for line in result:
            if 'interface' in line:
                if '\x1b[42D' in line:
                    interface = ''.join(list(line)[64:])
                else:
                    interface = ''.join(list(line)[10:])
                cmd = [
                    'dis current-configuration interface {}'.format(interface)
                ]
                result = self._execute(cmd)
                result = re.split('[\r\n]', result)
                if ' mpls te' in result:
                    interface_list.append(interface)
        return interface_list

    def check_mpls_te(self, interface):
        cmd = [
            'dis mpls te tunnel outgoing-interface {}'.format(interface)
        ]
        result = self._execute(cmd)
        if result:
            return True
        else:
            cmd = [
                'dis mpls te tunnel incoming-interface {}'.format(interface)
            ]
            result = self._execute(cmd)
            return True if result else False

    def get_mpls_te_cspf_tedb_info(self):
        cmd = [
            'dis mpls te cspf tedb network-lsa | in Current'
        ]
        result = self._execute(cmd)
        return result

    def get_power(self):
        cmd = [
            'display power'
        ]
        result = self._execute(cmd)
        return result

    def get_version(self):
        cmd = [
            'display version'
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        for line in result:
            if 'VRP (R) software' in line:
                return line
        return result

    def get_patch_info(self):
        cmd = [
            'display patch-information'
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        return result

    def get_mpls_lsr_id(self):
        cmd = [
            'dis curr conf | in lsr'
        ]
        result = self._execute(cmd)
        if 'Permission denied' in result:
            return None
        else:
            result = re.split('[\r\n]', result)
            result = result[0].split(' ')
            result = remove_null(result)
            return result[2]

    def get_interface_with_ip(self):
        cmd = [
            'dis ip int br'
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        for line in result:
            if 'Interface' not in line:
                result.remove(line)
            else:
                break
        result = result[1:]
        result = remove_null(result)
        results = []
        for line in result:
            if 'unassigned' not in line and 'Tunnel' not in line:
                results.append(line)
        return results

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
            else:
                result = result[0:3]
                if 'IGP-Type' in result[2]:
                    return result
                else:
                    return result[:2]
        else:
            return None

    def get_cpu_defend_statistics(self):
        cmd = [
            'display cpu-defend statistics'
        ]
        request = ['arp-miss', 'arp-reply', 'arp-request', 'bfd', 'bgp', 'isis',
                   'mpls-fib-hit', 'mpls-ldp', 'mpls-one-label', 'mpls-ping',
                   'mpls-rsvp', 'mpls-ttl-expired', 'mpls-vccv-ping', 'tcp']
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        if 'Error: Failed to pass the authorization.' in result:
            return result
        else:
            result_list = []
            result_list.append(result[1])
            result_list.append(result[2])
            result_list.append(result[3])
            for line in result[4:]:
                if line.split(' ')[0] in request:
                    result_list.append(line)
            return result_list

    def get_cpu_defend_statistics_93(self):
        cmd = [
            'display cpu-defend statistics all'
        ]
        request = ['arp-miss', 'arp-reply', 'arp-request', 'bfd', 'bgp', 'isis',
                   'mpls-fib-hit', 'mpls-ldp', 'mpls-one-label', 'mpls-ping',
                   'mpls-rsvp', 'mpls-ttl-expired', 'mpls-vccv-ping', 'tcp']
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        if 'Error: Failed to pass the authorization.' in result:
            return result
        else:
            number = None
            for line in result:
                if 'Statistics on slot' in line:
                    line = line.split(' ')[4]
                    number = list(line)[0]
                elif 'Statistics(packets) on slot' in line:
                    number = line.split(' ')[3]
            cmd = [
                'display cpu-defend statistics slot {}'.format(number)
            ]
            result = self._execute(cmd)
            result = re.split('[\r\n]', result)
            result = remove_null(result)
            result_list = []
            result_list.append(result[1])
            result_list.append(result[2])
            result_list.append(result[3])
            for line in result[4:]:
                if line.split(' ')[0] in request:
                    result_list.append(line)
            return result_list

    def get_l3vpn_bfd_list(self, name, vlan_id):
        cmd = [
            'display cur | include vpn-instance {} interface Vlanif{}'.format(name, vlan_id)
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        bfd_list = []
        for line in result:
            # print line.split(' ')
            bfd_list.append(line.split(' ')[1])
        return bfd_list

    def get_nts_status(self):
        cmd = [
            'dis ntp status'
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        return result[0]

    def get_cpu_usage(self):
        cmd = [
            'display cpu-usage'
        ]
        info = {}
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        for line in result:
            if 'Error' in line:
                info['Error'] = line
            else:
                if 'CPU Usage' in line and 'Max' in line and 'Time' not in line:
                    info['usage'] = line
                elif 'TaskName' in line:
                    info['headline'] = line
                elif 'AGNT' in line:
                    info['AGNT'] = line
                elif 'SFPT' in line:
                    info['SFPT'] = line
        return info

    def get_transceiver(self):
        cmd = [
            'display transceiver'
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        info = []
        for line in result:
            if 'Info:' not in line:
                info.append(line)
        return info

    def get_snmp_agent_acl(self):
        cmd = [
            'dis current-configuration | in snmp-agent'
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        if result:
            if 'Error: Failed to pass the authorization.' in result:
                return result
            elif 'Permission denied.' in result:
                return result
            else:
                for line in result:
                    if 'snmp-agent acl' in line:
                        return line
        return None

    def get_vlanif_vpn(self, vlan_id):
        """
            L3NET function: check PE BGP,RR VPNV4.
            :return:name,ip
        """
        cmd = [
            'display current-configuration interface Vlanif{}'.format(vlan_id)
        ]
        group_name = ""
        ip_address = []
        vsi_name = ""
        try:
            result = self._execute(cmd)
        except:
            return group_name, ip_address, vsi_name
        result = re.split('[\r\n]', result)
        for line in result:
            name_pattern = re.compile(r'((?=.*vpn-instance).*)')
            if name_pattern.search(line):
                group_name = re.search('(vpn-instance\s+)(.*)', line, re.S).group(2)
            ip_pattern = re.compile(r'((?=.*ip address).*)')
            if ip_pattern.search(line):
                ip = re.search('(ip address\s+)(.*)', line, re.S).group(2)
                ip_address.append(ip)
            vsi_pattern = re.compile(r'((?=.*l2 binding vsi).*)')
            if vsi_pattern.search(line):
                vsi_name = re.search('(l2 binding vsi\s+)(.*)', line, re.S).group(2)
        return group_name, ip_address, vsi_name

    def has_ip_prefix(self, name, ip, mask):
        cmd = [
            'dis cur | in ip ip-prefix {}'.format(name),
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        prefix = 'ip ip-prefix {} index (\w+) permit (\w+).(\w+).(\w+).(\w+) (\w+)'.format(name)
        for line in result:
            res_prefix = re.match(prefix,  line)
            if res_prefix:
                if '{}.{}.{}.{}'.format(res_prefix.group(2), res_prefix.group(3), res_prefix.group(4),
                                        res_prefix.group(5)) == ip_to_segment(ip, mask) and \
                        res_prefix.group(6) == str(int_netmask(mask)):
                    return res_prefix.group(1)
        return None

    def get_ip_prefix_index(self, name, ip_section, mask):
        index = ""
        ip_section = ip_to_segment(ip_section, mask)
        cmd = [
            'dis this | include ip ip-prefix {}'.format(name)
        ]
        result = self._execute(cmd)
        print result
        result = re.split('[\r\n]', result)
        for line in result:
            if "{} {}".format(ip_section, mask) in line and "index" in line and "permit" in line:
                index = re.split('index|permit', line)[1].strip()
                return index
        return index

    def get_ip_prefix_size(self, name, type):
        cur_index_li = []
        if type == 'net':
            size = 10
        else:
            size = 510
        cmd = [
            'dis cur | include ip ip-prefix {}'.format(name),
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        prefix = 'ip ip-prefix {} index (\w+)'.format(name)
        for line in result:
            res_prefix = re.match(prefix, line)
            if res_prefix:
                cur_index_li.append(res_prefix.group(1))
        print cur_index_li
        while str(size) in cur_index_li:
            size += 10
        return size

    def get_ip_prefix_number(self, name):
        cur_index_li = []
        cmd = [
            'dis cur | include ip ip-prefix {}'.format(name),
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        prefix = 'ip ip-prefix {} index (\w+)'.format(name)
        for line in result:
            res_prefix = re.match(prefix, line)
            if res_prefix:
                if int(res_prefix.group(1)) <= 500:
                    cur_index_li.append(res_prefix.group(1))
        return len(cur_index_li)

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
            if int(res.group(1)) != 0:
                return str(int(res.group(1)) - 3)
        return result

    def get_isispeer_info(self):
        cmd = [
            'disp isis peer verb'
        ]
        result = self._execute(cmd)
        return result

    def get_l3vpn_bfd_local(self):
        cmd = [
            # 'display bfd configuration all'
            'display bfd session all'
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        bfd = []
        for line in result:
            line_str = line.split()
            if len(line_str) > 1 and line_str[0].isdigit():
                bfd.append(line_str[0])
        return bfd

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

    def get_begin_user_interface(self):
        cmd = [
            'dis cu | begin user-interface'
        ]
        result = self._execute(cmd)
        result = re.split('[\r\n]', result)
        result = remove_null(result)
        a = result.index('user-interface vty 0 4')
        b = result.index('user-interface vty 16 20')
        result = result[a:b]
        return result

    def has_pebgp_ce_peer(self, name, vid, peer_ip):
        cmd = [
            'bgp {}'.format(vid),
            'ipv4-family vpn-instance {}'.format(name),
            'display this | in peer {}'.format(peer_ip)
        ]
        result = self._execute(cmd)
        self._execute(['quit', 'quit'])
        if peer_ip in result:
            return True
        else:
            return False

    '*******************************config**********************************'
    def shutdown_interface(self, interface):
        cmd = [
            'interface {}'.format(interface),
            'shutdown',
            'quit'
        ]
        self._execute(cmd)

    def undo_vsi(self, vsi):
        cmd = [
            # 'display vsi'
            'undo vsi {}'.format(vsi)
        ]
        result = self._execute(cmd)
        print [result]
        if 'VSI will be deleted' in result and 'Y/N' in result:
            print 2222222222222222222222222
            self._execute(['Y'])

    def set_user_intf_protocol_inbound_all(self):
        cmd = [
            'user-interface vty 0 4',
            'protocol inbound all',
            'quit'
        ]
        self._execute(cmd)

    def enable_local_account_ssh(self):
        cmd = [
            'aaa',
            'local-user syscloud password irreversible-cipher leenstorkMED#035',
            'local-user syscloud privilege level3',
            'local-user syscloud service-type ssh telnet terminal',
            'quit'
        ]
        self._execute(cmd)

    def create_ssh_account(self):
        cmd = [
            'ssh user syscloud',
            'ssh user syscloud service-type stelnet',
            'ssh user syscloud authentication-type password',
            'ssh authentication-type default password'
        ]
        self._execute(cmd)

    def start_ssh_service(self):
        cmd = [
            'stelnet server enable'
        ]
        self._execute(cmd)

    def has_traffic_policy(self, policy):
        cmd = [
            'display current-configuration configuration | include traffic policy {} match-order config'.format(policy)]
        result = self._execute(cmd)
        print [result]
        if 'traffic policy {} match-order config'.format(policy) in result:
            return True
        return False

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
        res = result[3].split(':')
        return [res[1].strip(), res[3].strip(), res[5].strip()]

    def has_rr_peer(self):
        cmd = [
            'display bgp vpnv4 all peer'
        ]
        result = self._execute(cmd)
        print(result)
        if result and 'BGP local router ID' in result:
            return True
        else:
            return False

    def has_vlanif(self, vlan):
        cmd = [
            'display current-configuration | include Vlanif{}'.format(vlan),
        ]
        result = self._execute(cmd)
        if not result:
            return False
        print 1111111111111
        result = re.split('[\r\n]', result)
        for line in result:
            if str(vlan) in line:
                lines = line.split()
                if 'Vlanif{}'.format(vlan) == lines[1]:
                    return True
        return False

    def check_vpnv4_advertise(self):
        cmd = [
            'dis cu con bgp'
        ]
        result = self._execute(cmd)
        print result
        if result.find('ipv4-family vpnv4') == -1:
            return False
        result = result[result.find('ipv4-family vpnv4'): result.rfind('#')]
        if not 'peer 10.52.255.255 advertise-community' in result or 'peer 10.255.254.100 advertise-community' not in result:
            return False
        else:
            return True

