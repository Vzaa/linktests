"AP node class"

from telnethelper import do_remote


def wl_cmd(ifname, command):
    cmd = 'wl -i ' + ifname + ' ' + command
    return cmd


class ApNode(object):
    def __init__(self, hostname, switchport,
                 plchostname='', if2g='wl0', if5g='wl1',
                 username='root', passwd=''):
        self.hostname = hostname
        self.switchport = switchport
        self.plchostname = plchostname
        self.username = username
        self.passwd = passwd
        self.ifs = {2: if2g, 5: if5g}
        self.radio_enabled = True
        self.macs = {}

    def run_command(self, command_list):
        return do_remote(self.hostname, command_list, self.username, self.passwd)

    def ap_mode(self, band=5):
        ifname = self.ifs[band]
        cmd_list = []
        cmd_list.append(wl_cmd(ifname, 'down'))
        cmd_list.append(wl_cmd(ifname, 'ap 1'))
        cmd_list.append(wl_cmd(ifname, 'up'))
        self.run_command(cmd_list)

    def sta_mode(self, ssid, band=5):
        ifname = self.ifs[band]
        cmd_list = []
        cmd_list.append(wl_cmd(ifname, 'down'))
        cmd_list.append(wl_cmd(ifname, 'ap 0'))
        cmd_list.append(wl_cmd(ifname, 'up'))
        cmd_list.append(wl_cmd(ifname, 'join ' + ssid))
        cmd_list.append(wl_cmd(ifname, 'wet 1'))
        self.run_command(cmd_list)

    def set_ssid(self, ssid, band=5):
        ifname = self.ifs[band]
        cmd_list = []
        cmd_list.append(wl_cmd(ifname, 'down'))
        cmd_list.append(wl_cmd(ifname, 'ssid ' + ssid))
        cmd_list.append(wl_cmd(ifname, 'up'))
        self.run_command(cmd_list)

    def set_chbw(self, ssid, channel, bw, band=5):
        ifname = self.ifs[band]
        cmd_list = []
        cmd_list.append(wl_cmd(ifname, 'down'))
        cmd_list.append(wl_cmd(ifname, 'chanspec ' + str(channel) + '/' + str(bw)))
        cmd_list.append(wl_cmd(ifname, 'up'))
        self.run_command(cmd_list)

    def enable_radio(self, band=5):
        ifname = self.ifs[band]
        cmd_list = []
        cmd_list.append(wl_cmd(ifname, 'up'))
        self.run_command(cmd_list)
        self.radio_enabled = True

    def disable_radio(self, band=5):
        ifname = self.ifs[band]
        cmd_list = []
        cmd_list.append(wl_cmd(ifname, 'down'))
        self.run_command(cmd_list)
        self.radio_enabled = False

    def set_wds_link(self, dest_mac, band=5):
        ifname = self.ifs[band]
        cmd_list = []
        cmd_list.append(wl_cmd(ifname, 'down'))
        cmd_list.append(wl_cmd(ifname, 'ssid "kedi"'))
        cmd_list.append(wl_cmd(ifname, 'chanspec 36/80'))
        cmd_list.append(wl_cmd(ifname, 'wdswsec 0'))
        cmd_list.append(wl_cmd(ifname, 'wdswsec_enable 0'))
        cmd_list.append(wl_cmd(ifname, 'lazywds 0'))
        cmd_list.append(wl_cmd(ifname, 'wdstimeout 1'))
        cmd_list.append(wl_cmd(ifname, 'wds ' + dest_mac))
        cmd_list.append(wl_cmd(ifname, 'up'))
        cmd_list.append('ifconfig wds1.1 up')
        cmd_list.append('brctl addif br0.1 wds1.1')
        self.run_command(cmd_list)

    def tear_wds_links(self, band=5):
        ifname = self.ifs[band]
        cmd_list = []
        cmd_list.append(wl_cmd(ifname, 'wds none'))
        self.run_command(cmd_list)

    def ping(self, ipaddr):
        cmd_list = []
        cmd_list.append('ping ' + ipaddr + ' -c 3')
        output = self.run_command(cmd_list)
        for line in output:
            print line

    def arp_clean(self):
        cmd_list = []
        cmd_list.append('brctl setageing br0.1 25')
        cmd_list.append('ip -s -s neigh flush all')
        output = self.run_command(cmd_list)

    def learn_macs(self):
        self.macs = {2: self.learn_mac(2), 5: self.learn_mac(5)}

    def learn_mac(self, band=5):
        ifname = self.ifs[band]
        cmd_list = []
        cmd_list.append('ifconfig ' + ifname + ' | grep -o ..:..:..:..:..:..')
        lines = self.run_command(cmd_list)
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
