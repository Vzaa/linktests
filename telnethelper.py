"telnet helper with pexpect"
#from __future__ import unicode_literals
import pexpect


def do_remote(hostname, command, username='root', passwd=''):
    c = pexpect.spawn('telnet ' + hostname)
    c.expect('login:')
    c.sendline(username)
    c.expect('Password:')
    c.sendline(passwd)
    c.expect('#')
    c.sendline(command)
    c.expect('#')
    res = c.before
    c.sendline('exit')
    c.kill(1)
    return res.split('\n')



def main():
    #do_remote('192.168.2.5', "wl ssid kedi")
    #get_output('192.168.2.5', "ifconfig wl0 | grep -o ..:..:..:..:..:..")
    asd = do_remote('192.168.2.5', "ls -l")

if __name__ == '__main__':
    main()
