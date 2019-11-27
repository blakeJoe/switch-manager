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
        # self.channel.settimeout(self.timeout)
        self.channel.get_pty()
        self.channel.invoke_shell()
        result = ''
        while not result.endswith('>'):
            resp = self.channel.recv(4096)
            result += resp

    def close(self):
        if self.ssh:
            if self.channel:
                self.channel.close()
            self.ssh.close()

    def execute(self, cmd):
        if self.channel:
            self.channel.send(cmd+'\n')
            result = ''
            while not result.endswith(']') and not result.endswith('>'):
                resp = self.channel.recv(4096)
                if '---- More ----' in resp:
                    self.channel.send(' ')
                result += resp

            if 'The system is busy' in result:
                time.sleep(1)
                return self.execute(cmd)
            # elif 'Error' in result:
            #     LOG.error('error for cmd:[{}],result is {}'.format(cmd, result))
            #     raise VPLSException(
            #         error='VPLS Exception Error. command: [{}] execute failed, for: {}'.format(cmd, result))

            result = result[result.find('\n') + 1:result.rfind('\n')]
            return result
        else:
            pass
            # LOG.error('SSH client is not connected to {}'.format(self.ip))

    def printfNow(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
