from driver.driver import get_driver


class Device(object):

    def __init__(self, switch):
        self.switch = switch
        self.driver = get_driver(switch)

    def run(self):
        self.driver.connect()

        self.check_tedb_network_lsa()
        # self.check_mpls_tunnel_num()
        # self.check_down_interfaces()
        # self.shutdown_interfaces()

        self.driver.disconnect()

    def check_tedb_network_lsa(self):
        if '93' in self.switch.name or '57' in self.switch.name or '6820' in self.switch.name:
            pass
        else:
            result = self.driver.get_tedb_network_lsa()
            if result:
                if len(result) == 1:
                    print '\n{} ----- {}: \n{}'.format(self.switch.name, self.switch.m_ip, result[0])
                elif len(result) == 3:
                    print '\n{} ----- {}: \n{}\n{}\n{}'.format(self.switch.name, self.switch.m_ip, result[0],
                                                               result[1], result[2])
                else:
                    print '\n{} ----- {}: \n{}\n{}'.format(self.switch.name, self.switch.m_ip, result[0], result[1])
            else:
                print '\n{} ----- {}: \n{}'.format(self.switch.name, self.switch.m_ip, 'None')

    def check_mpls_tunnel_num(self):
        result = self.driver.get_mpls_te_tunnel_num()
        if result:
            print '\n{} ----- {}: \n{}'.format(self.switch.name, self.switch.m_ip, result)

    def check_down_interfaces(self):
        each_res, both_res, _ = self.driver.get_interface_status()
        # print '\n{} ----- {}: \n each_down_interfaces:  {}'.format(self.switch.name, self.switch.m_ip, each_res)
        print '\n{} ----- {}: \n both_down_interfaces:  {}'.format(self.switch.name, self.switch.m_ip, both_res)

    def shutdown_interfaces(self):
        shutdown_intfs = []
        _, both_res, _ = self.driver.get_interface_status()
        self.driver.return_root()
        for intf in both_res:
            self.driver.shutdown_interface(intf)
            shutdown_intfs.append(intf)
        self.driver.commit()
        self.driver.quit()
        self.driver.save()
        # _, _, result = self.driver.get_interface_status(no_processing=True)
        print '\n{} ----- {}: \n shutdown interfaces:  {}'.format(self.switch.name, self.switch.m_ip, shutdown_intfs)

    def check_ssh(self):
        pass

    def check_interface_ip(self):
        ip = '3.3.3.3'
        result = self.driver.check_interfae_ip(ip)
        print result


