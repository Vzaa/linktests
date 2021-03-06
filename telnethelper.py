"telnet helper with pexpect"
#from __future__ import unicode_literals
import pexpect


def do_remote(hostname, command_list, username='root', passwd=''):
    res = ''
    c = pexpect.spawn('telnet ' + hostname, timeout=120)
    c.expect('login:')
    c.sendline(username)
    if passwd is not None:
        c.expect('Password:')
        c.sendline(passwd)
    c.expect('#')
    for command in command_list:
        c.sendline(command)
        c.expect('#')
        res += c.before
        print c.before,
    c.sendline('exit')
    c.kill(1)
    return res.split('\n')


def do_remote_plc(hostname, command_list, username='admin', passwd='admin'):
    res = ''
    c = pexpect.spawn('telnet ' + hostname, timeout=120)
    c.expect('Login:')
    c.sendline(username)
    if passwd is not None:
        c.expect('Password:')
        c.sendline(passwd)
    c.expect('>')
    c.sendline('sh')
    c.expect('#')
    for command in command_list:
        c.sendline(command)
        c.expect('#')
        res += c.before
        print c.before,
    c.sendline('exit')
    c.expect('>')
    c.sendline('exit')
    c.kill(1)
    return res.split('\n')


def main():
    pass

if __name__ == '__main__':
    main()
