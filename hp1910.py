"HP1910 switch port control"
from __future__ import unicode_literals
import sys
import pexpect

IPADDR = '192.168.2.200'
SYSPASSWD = '512900'


class Switch1910(object):
    def __init__(self, hostname, username='admin', passwd=''):
        self._hostname = hostname
        self._username = username
        self._passwd = passwd
        self._connect()

    def _connect(self):
        self.c = pexpect.spawnu('telnet ' + self._hostname)
        self.c.expect('Username:')
        self.c.sendline(self._username)
        self.c.expect('Password:')
        self.c.sendline(self._passwd)
        self.c.expect('<HP>')
        self.c.sendline('_cmdline-mode on')
        self.c.expect('[Y/N]')
        self.c.sendline('Y')
        self.c.expect('Please input password:')
        self.c.sendline(SYSPASSWD)
        self.c.expect('<HP>')
        self.c.sendline('SYS')
        self.c.expect('[HP]')

    def close(self):
        self.c.sendline('quit')
        self.c.sendline('quit')
        self.c.kill(1)

    def interact(self):
        self.c.interact()

    def add_ports_to_vlan(self, vlan, ports):
        if not self.c.isalive():
            self._connect()

        try:
            self.c.sendline('vlan ' + str(vlan))
            self.c.expect('[HP-vlan' + str(vlan) + ']')

            for port in ports:
                print '{} -> {}'.format(port, vlan)
                self.c.sendline('port GigabitEthernet 1/0/' + str(port))
                self.c.expect('[HP-vlan' + str(vlan) + ']')

            self.c.sendline('quit')
        except pexpect.EOF:
            self._connect()
            self.add_ports_to_vlan(vlan, ports)


def main():
    pass
    sw = Switch1910(IPADDR, 'admin', 'admin')
    sw.interact()
    #sw.add_ports_to_vlan(1, [2, 3, 4, 5, 6])
    #sw.add_ports_to_vlan(3, range(2, 21))
    #sw.add_ports_to_vlan(2, [15])
    #sw.interact()
    #sw.close()

if __name__ == '__main__':
    main()
