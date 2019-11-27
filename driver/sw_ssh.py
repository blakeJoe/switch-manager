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
        self.channel = self.ssh.open_session(timeout=90)
        self.channel.settimeout(30)
        self.channel.get_pty()
        self.channel.invoke_shell()
        result = ''
        while not result.strip().endswith('>'):
            resp = self.channel.recv(4096)
            result += resp
            if '[Y/N]:' in resp:
                self.channel.send('N' + '\n')
        print result

    def close(self):
        if self.ssh:
            if self.channel:
                self.channel.close()
            self.ssh.close()

    def execute(self, cmd, sysview=False):
        if self.channel:
            self.channel.send(cmd + '\n')
            result = ''
            if sysview and cmd != 'return':
                while not result.strip().endswith(']'):
                    resp = self.channel.recv(4096)
                    # resp = self.filter_control_character(resp)
                    # if resp == '\x1b[?1h\x1b=\r':
                    #     continue
                    # elif "\x1b[42D" in resp:
                    #     resp = resp.split("\x1b[42D")[2]
                    result += resp
                    if result.endswith('[Y/N]:'):
                        break
            else:
                while not result.strip().endswith('>'):
                    resp = self.channel.recv(4096)
                    # resp = self.filter_control_character(resp)
                    # if resp == '\x1b[?1h\x1b=\r':
                    #     continue
                    # elif "\x1b[42D" in resp:
                    #     resp = resp.split("\x1b[42D")[2]
                    # elif '[Y/N]:' in resp:
                    #     self.channel.send('\n')
                    result += resp
                    if result.endswith('[Y/N]'):
                        break
                # elif 'Error' in result:
                #     LOG.error('error for cmd:[{}],result is {}'.format(cmd, result))
                #     raise VPLSException(
                #         error='VPLS Exception Error. command: [{}] execute failed, for: {}'.format(cmd, result))
            if result.endswith(']') or result.endswith('>'):
                result = result[result.find('\n') + 1:result.rfind('\n')]
            else:
                first_nl = result.find('\n')
                last_nl = result.rfind('\n')
                result = result[first_nl + 1: last_nl] if first_nl != last_nl else result[first_nl + 1:]
            return result
        else:
            pass

    @staticmethod
    def print_now():
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

    @staticmethod
    def filter_control_character(resp):
        resp = re.sub("\\x1b\[m", "", resp)
        resp = re.sub("\\x1b\[K", "", resp)
        resp = re.sub(" \\x08", "", resp)
        return resp