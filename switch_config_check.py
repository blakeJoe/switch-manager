#!/usr/bin/python
# -*- coding: UTF-8 -*

import re
import threading
import MySQLdb
from driver.driver import get_driver
from driver.utils import get_data_in_tuple, remove_null, int_netmask, format_netmask
from concurrent.futures import ThreadPoolExecutor

INFO = []


class Switch(object):

    def __init__(self, **kwargs):
        self.name = None
        self.switch_type = None
        self.sub_type = None
        self.m_ip = None
        self.protocol = None
        self.port = None
        self.username = None
        self.password = None
        self.lsr_id = None
        self.port_ip_info = None


class MyThread(threading.Thread):   #继承父类threading.Thread

    def __init__(self, result):

        threading.Thread.__init__(self)
        self.result = result

    def run(self):                   #把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        switch = Switch()

        "生产环境信息"
        switch.name = self.result[0]
        switch.m_ip = self.result[1]
        switch.protocol = "TELNET"
        switch.port = 23
        switch.username = "sdn-server"
        switch.password = "SDNsyscloud20!7"

        "测试环境信息"
        # switch.switch_type = self.result[0]
        # switch.sub_type = self.result[1]
        # switch.m_ip = self.result[2]
        # switch.protocol = self.result[3]
        # switch.port = self.result[4]
        # switch.username = self.result[5]
        # switch.password = self.result[6]

        "指定交换机"
        # switch.switch_type = "h3c_s"
        # switch.sub_type = "h3c_s6820"
        # switch.m_ip = "192.168.211.18"
        # switch.protocol = "TELNET"
        # switch.port = 23
        # switch.username = "admin"
        # switch.password = "syscloud123"

        "指定交换机"
        # switch.name = "huawei_S6700"
        # switch.m_ip = "3.3.3.3"
        # switch.protocol = "SSH"
        # switch.port = 22
        # switch.username = "admin"
        # switch.password = "syscloud@123"

        driver = get_driver(switch)
        driver.connect()
        # self.check_snmp_acl(switch, driver)
        #
        '每周一次'
        self.check_tedb_network_lsa(switch, driver)
        '==========='
        # self.check_mpls_tunnel_num(switch, driver)
        '==========='
        # self.check_cpu_usage(switch, driver)
        # self.check_transceiver(switch, driver)
        # self.check_down_interfaces(switch, driver)
        # self.check_ntp(switch, driver)
        # self.check_stp(switch, driver)
        # self.check_cpu(switch, driver)

        'test'
        # print "=========================="
        # self.test(switch, driver)
        # driver.commit()
        driver.quit()
        # driver.save()
        # lsr_id = self.check_mpls_lsr_id(switch, driver)z
        # if lsr_id:
        #     switch.lsr_id = lsr_id
        #     switch.port_ip_info = self.check_interface_ip(switch, driver)
        # INFO.append(switch)
        driver.disconnect()

    def get_data_from_databases(self, databases, table, data):
        db = MySQLdb.connect('10.88.66.3', 'queryuser1', 'querypasswd1', 'syscxp_tunnel', 5536, databases)
        cursor = db.cursor()
        sql = 'SELECT {} FROM {}'.format(data, table)
        try:
            cursor.execute(sql)
            result = cursor.fetchall()
        except:
            result = 'Error'
            print "Error: unable to fecth data"
        db.close()
        return result

    def check_vlan(self, switch, driver):
        rub_vlan_list = []
        vlan_ports_state = {}
        vlanif_config = {}
        vlan_config = {}
        switch_vlan_list = driver.get_vlan_list()
        result = self.get_data_from_databases('syscxp_tunnel', 'TunnelSwitchPortVO', 'vlan')
        db_vlan_list = map(get_data_in_tuple, result)

        for vlan in switch_vlan_list:
            if vlan not in db_vlan_list:
                rub_vlan_list.append(vlan)
        print 'Inconsistent vlan in {}: \n{}'.format(switch.m_ip, rub_vlan_list)

        for vlan in rub_vlan_list:
            port_state_result = driver.get_vlan_port_state(vlan)
            vlan_ports_state.update(port_state_result)

            vlanif_result = driver.get_vlanif_config(vlan)
            vlanif_config.update(vlanif_result)

            vlan_result = driver.get_vlan_config(vlan)
            vlan_config.update(vlan_result)

        print 'vlan-port-state in {}: \n{}'.format(switch.m_ip, vlan_ports_state)
        print 'vlanif-config in {}: \n{}'.format(switch.m_ip, vlanif_config)
        print 'vlan-config in {}: \n{}'.format(switch.m_ip, vlan_config)

    def check_vsi(self, switch, driver):
        rub_vsi_name_list = []
        vsi_config = []
        switch_vsi_dict = driver.get_vsi_dict()
        result = self.get_data_from_databases('syscxp_tunnel', 'TunnelVO', 'vsi')
        db_vsi_list = map(get_data_in_tuple, result)

        for vsi_name in switch_vsi_dict.keys():
            if switch_vsi_dict[vsi_name] not in db_vsi_list:
                rub_vsi_name_list.append(vsi_name)
        print 'Inconsistent vsi in {}: \n{}'.format(switch.m_ip, rub_vsi_name_list)

        for vsi_name in rub_vsi_name_list:
            vsi_state_result = driver.get_vsi_state(vsi_name)
            vsi_config.append(vsi_state_result)
        print 'vsi-state in {}: \n{}'.format(switch.m_ip, vsi_config)

    def check_vpn_instance(self, switch, driver):
        rub_vpn_instance_list = []
        vpn_instance_config = {}
        switch_vpn_instance_dict = driver.get_vpn_instance_dict()

        result = self.get_data_from_databases('syscxp_tunnel', 'L3NetworkVO', 'vid')
        db_vrf_id_list = map(get_data_in_tuple, result)

        for vpn_instance in switch_vpn_instance_dict.keys():
            if switch_vpn_instance_dict[vpn_instance] not in db_vrf_id_list:
                rub_vpn_instance_list.append(vpn_instance)
        print 'Inconsistent vpn_instance in {}: \n{}'.format(switch.m_ip, rub_vpn_instance_list)

        for vpn_instance in rub_vpn_instance_list:
            vpn_instance_state = driver.get_vpn_instance_state(vpn_instance)
            vpn_instance_config.update(vpn_instance_state)
        print 'vpn_instance config in {}: \n{}'.format(switch.m_ip, vpn_instance_config)

    def check_power(self, switch, driver):
        result = None
        result = driver.get_power()
        print 'power in {}: \n{}\n\n'.format(switch.m_ip, result)

    def check_mpls_te_interface(self, switch, driver):
        no_mple_te_interface_list = []
        switch_interface_list = driver.get_interface_with_mplse_te_list()
        for interface in switch_interface_list:
            result = driver.check_mpls_te(interface)
            if not result:
                no_mple_te_interface_list.append(interface)

        if no_mple_te_interface_list:
            print 'required interface in {}： \n{}'.format(switch.m_ip, no_mple_te_interface_list)

    def check_mpls_te_cspf_tedb(self, switch, driver):
        result = driver.get_mpls_te_cspf_tedb_info()
        print '\ninfomation in {}: \n{}'.format(switch.m_ip, result)

    def check_version(self, switch, driver):
        result = driver.get_version()
        print '\n{} ----- {}: \n{}'.format(switch.name, switch.m_ip, result)

    def check_patch_info(self, switch, driver):
        result = driver.has_port(switch.port)
        print '\n{} ----- {}: \n{}\n{}\n{}\n{}'.format(switch.name, switch.m_ip, result[0], result[1], result[2], result[3])

    def check_mpls_lsr_id(self, switch, driver):
        lsr_id = driver.get_mpls_lsr_id()
        return lsr_id

    def check_interface_ip(self, switch, driver):
        port_list = []
        result = driver.get_interface_with_ip()
        for port in result:
            port_ip_info = {}
            port = re.split('[\r\n]', port)
            port = port[0].split(' ')
            port = remove_null(port)
            port_ip_info['port_name'] = port[0]
            if port[2] == 'up':
                port_ip_info['up_ip'] = port[1]
            else:
                port_ip_info['down_ip'] = port[1]
            port_list.append(port_ip_info)
        return port_list

    "每周一次"
    def check_tedb_network_lsa(self, switch, driver):
        if '93' in switch.name or '57' in switch.name or '6820' in switch.name:
            pass
        else:
            result = driver.get_tedb_network_lsa()
            if result:
                if len(result) == 1:
                    print '\n{} ----- {}: \n{}'.format(switch.name, switch.m_ip, result[0])
                elif len(result) == 3:
                    print '\n{} ----- {}: \n{}\n{}\n{}'.format(switch.name, switch.m_ip, result[0], result[1], result[2])
                else:
                    print '\n{} ----- {}: \n{}\n{}'.format(switch.name, switch.m_ip, result[0], result[1])
            else:
                print '\n{} ----- {}: \n{}'.format(switch.name, switch.m_ip, 'None')

    def check_cpu_defend_statistics(self, switch, driver):
        if '93' in switch.name or '12804' in switch.name:
            result = driver.get_cpu_defend_statistics_93()
            print '\n{} ----- {}: \n'.format(switch.name, switch.m_ip)
            for line in result:
                print line
        elif '6820' in switch.name:
            pass
        else:
            result = driver.get_cpu_defend_statistics()
            print '\n{} ----- {}: \n'.format(switch.name, switch.m_ip)
            for line in result:
                print line

    def check_ntp_status(self, switch, driver):
        result = driver.get_nts_status()
        print '\n{} ----- {}: \n{}'.format(switch.name, switch.m_ip, result)

    def check_cpu_usage(self, switch, driver):
        if '6720' in switch.name:
            result = driver.get_cpu_usage()
            if len(result) == 1:
                print '\n{} ----- {}: \n{}'.format(switch.name, switch.m_ip, result['Error'])
            else:
                print '\n{}: \n{}   {}  {}  {}'.format(switch.name, switch.m_ip,
                                                               result['usage'], result['headline'],
                                                               result['AGNT'], result['SFPT'])

    def check_transceiver(self, switch, driver):
        if '6720' in switch.name:
            result = driver.get_transceiver()
            w = file("G:/docu/tra/{}.txt".format(switch.name), "a+")  # 以追加的方式
            w.write('{} ----------------------------------------------------------------------- {}:\n\n'.format(switch.name, switch.m_ip))
            for line in result:
                w.write('{}\n'.format(line))

    def check_snmp_acl(self, switch, driver):
        if '67' in switch.name or '68' in switch.name:
            result = driver.get_snmp_agent_acl()
            if result:
                print '\n{} ----- {}: \n{}'.format(switch.name, switch.m_ip, result)
            else:
                print '\n{} ----- {}: \n{}'.format(switch.name, switch.m_ip, 'None')

    def check_mpls_tunnel_num(self, switch, driver):
        result = driver.get_mpls_te_tunnel_num()
        if result:
            print '\n{} ----- {}: \n{}'.format(switch.name, switch.m_ip, result)

    def check_down_interfaces(self, switch, driver):
        each_res, both_res, _ = driver.get_interface_status()
        print '\n{} ----- {}: \n each_down_interfaces:  {}'.format(switch.name, switch.m_ip, each_res)
        # print '\n{} ----- {}: \n both_down_interfaces:  {} '.format(switch.name, switch.m_ip, both_res)

    def check_ntp(self, switch, driver):
        dev_time = driver.get_time()
        clock_status = driver.get_clock_status(switch.name)
        if '08:00' not in dev_time or 'synchronized' not in clock_status:


            ntp_conf = driver.get_ntp_conf()
            if not ntp_conf:
                ntp_conf = None
            print '\n{} ----- {}: \n{}'.format(switch.name, switch.m_ip, ntp_conf)

    def config_user_interface_protocol_all(self, switch, driver):
        driver.set_user_intf_protocol_inbound_all()
        print '{} --- {}: done!'.format(switch.name, switch.m_ip)

    def config_ssh(self, switch, driver):
        driver.enable_local_account_ssh()
        driver.create_ssh_account()
        driver.start_ssh_service()
        print '{} --- {}: done!'.format(switch.name, switch.m_ip)

    def check_stp(self, switch, driver):
        if not driver.get_stp_status():
            print switch.name

    def check_cpu(self, switch, driver):
        result = driver.get_cpu_status()
        print '{}   {}  {}  {}'.format(switch.name, result[0], result[1], result[2])

    '========================================test==========================================='
    def test(self, switch, driver):
        result = driver.check_vpnv4_advertise()
        # print switch.m_ip + ' DONE!'
        print result


# f = open('G:/docu/test.txt')


# while 1:
#     # result = re.split('[\t]', f.readline())
#     result = re.split('[\n]', f.readline())
#     if not result[0]:
#         break
#     else:
#         result = result[0].split(' ')
#         # result[1] = re.split('[\n]', result[1])[0]
#         result = remove_null(result)
#         thread = MyThread(result)
#         thread.start()

def main():
    """
    open('G:/docu/has.txt')
    open('G:/docu/switch.txt')
    """
    thread = MyThread()
    with open('G:/docu/switch.txt', 'r') as f:
        switch_list = f.readlines()
    with ThreadPoolExecutor(20) as executor:
        for switch in switch_list:
            switch = re.split(r'[\t\n]', switch)
            executor.submit(self.get_isispeer_remote, obj)







# while 1:
#     result = re.split('[\n]', f.readline())
#     if not result[0]:
#         break
#     else:
#         thread = MyThread([None, result[0]])
#         thread.start()


# time.sleep(30)
"新建EXCEL"
# wbk = xlwt.Workbook()
# sheet = wbk.add_sheet('sheet0')

"修改EXCEL"
# old_wbk = xlrd.open_workbook('G:/docu/data.xls')
# wbk = copy(old_wbk)
# sheet = wbk.get_sheet(0)

# i = 1
# for switch in INFO:
#     print '---------------------------- {}'.format(switch.m_ip)
#     sheet.write(i, 0, switch.name)
#     sheet.write(i, 1, switch.m_ip)
#     if switch.lsr_id:
#         sheet.write(i, 2, switch.lsr_id)
#         for port in switch.port_ip_info:
#             sheet.write(i, 3, port['port_name'])
#             if 'up_ip' in port.keys():
#                 sheet.write(i, 4, port['up_ip'])
#             else:
#                 sheet.write(i, 5, port['down_ip'])
#             i = i + 1
#     i = i + 1
# wbk.save('G:/docu/data1.xls')
#

if __name__ == '__main__':
    main()
