# -*- coding: utf-8 -*-

import re
import paramiko
import time


class SSHClient(object):
    def __init__(self, ip, username, password, port):
        self.ip = ip
        self.port = port
        if not self.port:
            self.port = 22
        self.username = username
        self.password = password
        # self.ssh = paramiko.SSHClient()
        # self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh = None
        self.channel = None

    def login(self):
        # self.ssh.connect(hostname=self.ip, port=self.port, username=self.username, password=self.password)
        # self.channel = self.ssh.invoke_shell()
        self.ssh = paramiko.Transport(sock=(self.ip, self.port))
        self.ssh.connect(username=self.username, password=self.password)
        self.channel = self.ssh.open_session()
        # self.channel.settimeout(1)
        self.channel.get_pty()
        self.channel.invoke_shell()
        result = ''
        while not result.strip().endswith('$'):
            resp = self.channel.recv(4096)
            result += resp

    def close(self):
        if self.ssh:
            if self.channel:
                self.channel.close()
            self.ssh.close()

    def execute(self, cmd):
        if self.channel:
            self.channel.send(cmd + '\n')
            result = ''
            while not result.strip().endswith('$'):
                if result.strip().endswith('#'):
                    break
                else:
                    resp = self.channel.recv(4096)
                    resp = self.filter_control_character(resp)
                    if resp == '\x1b[?1h\x1b=\r':
                        continue
                    # elif "\x1b[42D" in resp:
                    #     resp = resp.split("\x1b[42D")[2]
                    elif ':' in resp:
                        self.channel.send(' ')
                    result += resp

                # elif 'Error' in result:
                #     LOG.error('error for cmd:[{}],result is {}'.format(cmd, result))
                #     raise VPLSException(
                #         error='VPLS Exception Error. command: [{}] execute failed, for: {}'.format(cmd, result))
            return result

    @staticmethod
    def print_now():
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

    @staticmethod
    def filter_control_character(resp):
        resp = re.sub("\\x1b\[m", "", resp)
        resp = re.sub("\\x1b\[K", "", resp)
        resp = re.sub(" \\x08", "", resp)
        return resp



s = SSHClient(ip='222.222.22.22', username='root', password='password', port=22)
s.login()
s.execute('dispaly this')
s.close()