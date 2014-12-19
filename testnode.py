"AP node class"

from telnethelper import do_remote, get_output


def wl_cmd(ifname, command):
    cmd = 'wl -i ' + ifname + ' ' + command + ';'
    return cmd


class ApNode(object):
    def __init__(self, hostname, switchport,
                 plchostname='', if2g='wl0', if5g='wl1'):
        self.hostname = hostname
        self.switchport = switchport
        self.plchostname = plchostname
        self.ifs = {2: if2g, 5: if5g}
        self.radio_enabled = True
        self.macs = {2: self.learn_mac(2), 5: self.learn_mac(5)}

    def run_command(self, command):
        return do_remote(self.hostname, command)

    def ap_mode(self, band=5):
        ifname = self.ifs[band]
        cmd = ''
        cmd += wl_cmd(ifname, 'down')
        cmd += wl_cmd(ifname, 'ap 1')
        cmd += wl_cmd(ifname, 'up')
        self.run_command(cmd)

    def sta_mode(self, band=5):
        ifname = self.ifs[band]
        cmd = ''
        cmd += wl_cmd(ifname, 'down')
        cmd += wl_cmd(ifname, 'ap 0')
        cmd += wl_cmd(ifname, 'up')
        self.run_command(cmd)

    def set_ssid(self, ssid, band=5):
        ifname = self.ifs[band]
        cmd = ''
        cmd += wl_cmd(ifname, 'down')
        cmd += wl_cmd(ifname, 'ssid ' + ssid)
        cmd += wl_cmd(ifname, 'up')
        self.run_command(cmd)

    def enable_radio(self, band=5):
        ifname = self.ifs[band]
        cmd = wl_cmd(ifname, 'up')
        self.run_command(cmd)
        self.radio_enabled = True

    def disable_radio(self, band=5):
        ifname = self.ifs[band]
        cmd = wl_cmd(ifname, 'down')
        self.run_command(cmd)
        self.radio_enabled = False

    def set_wds_link(self, dest_mac, band=5):
        ifname = self.ifs[band]
        cmd = wl_cmd(ifname, 'wds ' + dest_mac)
        self.run_command(cmd)

    def learn_mac(self, band=5):
        ifname = self.ifs[band]
        cmd = 'ifconfig ' + ifname + ' | grep -o ..:..:..:..:..:..'
        lines = self.run_command(cmd)
        mac = lines[-2].strip()
        return mac


def main():
    asd = ApNode('192.168.2.5', '', 2, if2g='wl0', if5g='wl0')
    #asd.set_ssid('potato', band=2)
    #asd.set_ssid('kereviz', band=2)
    print asd.macs
    pass

if __name__ == '__main__':
    main()
