from metadata import ONLINE_USER, ONLINE_PSW, TEST_USER, TEST_PSW


class Switch(object):

    def __init__(self, *args, **kwargs):
        self.name = kwargs['name']
        self.m_ip = kwargs['m_ip']
        self.protocol = "TELNET"
        self.port = 23
        self.username = None
        self.password = None

        self.switch_type = self.switch_name_analyze(self.name)
        self.set_user_data(type='online')

    def set_user_data(self, type='test'):
        if type == 'test':
            self.username = TEST_USER
            self.password = TEST_PSW
        else:
            self.username = ONLINE_USER
            self.password = ONLINE_PSW

    def switch_name_analyze(self, name):
        if '6820' in name:
            return 'h3c_s'
        elif '12804' in name:
            return 'huawei_ce'
        else:
            return 'huawei_s'