import telnetlib
import time


class TelnetClient(object):

    def __init__(self, ip, username, password, port):
        self.ip = ip
        self.port = port
        if not self.port:
            self.port = 23
        self.username = username
        self.password = password
        self.tn = telnetlib.Telnet(host=self.ip, port=int(self.port), timeout=30)

    def login(self, switch_type='huawei'):
        if switch_type == 'h3c':
            self.tn.read_until('login: ', timeout=5)
            username = self.username.encode('utf-8')
            self.tn.write(username + '\n')
            self.tn.read_until('word: ')
            password = self.password.encode('utf-8')
            self.tn.write(password + '\n')
            self.tn.read_until('>', timeout=50)
        else:
            self.tn.read_until('name:', timeout=10)
            username = self.username.encode('utf-8')
            self.tn.write(username + '\n')
            self.tn.read_until('word:')
            password = self.password.encode('utf-8')
            self.tn.write(password + '\n')
            self.tn.read_until('>', timeout=50)

    def close(self):
        if self.tn:
            self.tn.close()

    def execute(self, cmd, sysview=False):
        if self.tn:
            self.tn.write(cmd + '\n')
            if 'quit' == cmd:
                if sysview:
                    result = self.tn.read_until(']', timeout=4)
                else:
                    result = self.tn.read_until('>', timeout=3)
            elif 'y' == cmd:
                result = self.tn.read_until('>', timeout=3)
            elif 'return' == cmd:
                result = self.tn.read_until('>', timeout=3)
            elif 'screen-length 0 temporary' == cmd:
                result = self.tn.read_until('>', timeout=3)
            elif 'undo vsi' in cmd:
                result = self.tn.read_until(']:', timeout=3)
            else:
                result = self.tn.read_until(']', timeout=30)

            if 'The system is busy' in result:
                time.sleep(1)
                return self.execute(cmd)

            while '---- More ----' in result:
                self.tn.write(' ')
                result = result.replace('---- More ----', '').strip()
                lines = self.tn.read_until(']', timeout=1)
                if "\x1b[42D" in lines:
                    lines = lines.split("\x1b[42D")[2]
                result += "\n" + lines
            # print [result]
            # first_nl = result.find('\n')
            # last_nl = result.rfind('\n')
            # result = result[first_nl+1: last_nl] if first_nl != last_nl else result[first_nl+1:]
            result = result[result.find('\n') + 1:result.rfind('\n')]
            return result
        else:
            pass
            # LOG.error('Telnet client is not connected to {}'.format(self.ip))

    def printfNow(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())