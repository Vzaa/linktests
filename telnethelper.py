"telnet helper with pexpect"
from __future__ import unicode_literals
import pexpect


def do_remote(hostname, command):
    c = pexpect.spawnu('telnet ' + hostname)
    c.expect('login:')
    c.sendline('root')
    c.expect('Password:')
    c.sendline('')
    c.expect('#')
    c.sendline(command)
    c.expect('#')
    c.sendline('exit')
    c.kill(1)
    pass

def main():
    do_remote('192.168.2.5', "wl ssid kedi")
    pass

if __name__ == '__main__':
    main()
