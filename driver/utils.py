def remove_null(l):
    while '' in l:
        l.remove('')
    while ' ' in l:
        l.remove(' ')
    return l


def vlan_str_to_list(s):
    ss = s.split()
    res = []
    toflag = False
    startnum = ""
    for tempstr in ss:
        if "to" == tempstr:
            toflag = True
        else:
            if toflag:
                for i in range(int(startnum), int(tempstr) + 1):
                    res.append(i)
                toflag = False
                startnum = ""
            else:
                if startnum:
                    res.append(int(startnum))
                startnum = tempstr
    return res


def get_data_in_tuple(data):
    return int(data[0])


def get_vsi_name(data):
    l = data.split(' ')
    l = remove_null(l)
    if l[0] == '\x1b[42D':
        vsi_name = ''.join(list(l[1])[5:])
    else:
        vsi_name = l[0]
    return vsi_name


def get_vsi_by_vsi_name(vsi_name):
    l = list(vsi_name)
    vsi = ''.join(l[3:])
    return vsi


def get_port_list(data):
    port_list = []
    for line in data:
        if '40GE' in line or 'XGE' in line:
            line = line.split(' ')
            line = remove_null(line)
            if 'common' in line:
                for i in line[2:]:
                    a = list(i)
                    if a[-5] == '/':
                        port_list.append(''.join(a[-4:-3]))
                    else:
                        port_list.append(''.join(a[-5:-3]))
            else:
                for i in line:
                    a = list(i)
                    if a[-5] == '/':
                        port_list.append(''.join(a[-4:-3]))
                    else:
                        port_list.append(''.join(a[-5:-3]))
    return port_list


def get_vpn_instance_list(data):
    vpn_instance_list = []
    for line in data:
        line = line.split(' ')
        line = remove_null(line)
        vpn_instance_list.append(line[0])
    return vpn_instance_list


def format_netmask(netmask):
    if '.' in str(netmask):
        return str(netmask)
    else:
        netmask = int(netmask)
        bin_arr = ['0' for i in range(32)]
        for i in range(netmask):
            bin_arr[i] = '1'
        tmp_mask = [''.join(bin_arr[i * 8:i * 8 + 8]) for i in range(4)]
        tmp_mask = [str(int(tmp_str, 2)) for tmp_str in tmp_mask]
        return '.'.join(tmp_mask)


def int_netmask(netmask):
    if isinstance(netmask, int):
        return netmask
    else:
        mask = 0
        for i in netmask.split('.'):
            mask += bin(int(i)).count('1')
        return mask


def ip_to_segment(ip, netmask):
    netmask = format_netmask(netmask)
    ips = ip.split(".")
    netmasks = netmask.split(".")
    res = ""
    for i in range(4):
        if res:
            res = res + "."
        res = res + str(int(ips[i]) & int(netmasks[i]))
    return res