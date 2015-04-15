"AP node class"

from telnethelper import do_remote

CONTROL_VLAN = 2
DUMMY_VLAN = 3
SINK_VLAN = 4

def wl_cmd(ifname, command):
    cmd = 'wl -i %s %s' % (ifname, command)
    return cmd


class ApNode(object):
    def __init__(self, hostname, switchport=None,
                 if2g='wl0', if5g='wl1',
                 username='root', passwd=None, macs=None, sw=None):
        self.hostname = hostname
        self.switchport = switchport
        self.username = username
        self.passwd = passwd
        self.ifs = {2: if2g, 5: if5g}
        self.radio_enabled = True
        self.sw = sw
        self.vlan = DUMMY_VLAN

        if macs is None:
            self.macs = dict()
        else:
            self.macs = macs

    @classmethod
    def fromdict(cls, mydict):
        return cls(hostname=mydict['hostname'],
                   switchport=mydict['switchport'],
                   if2g=mydict['if2g'],
                   if5g=mydict['if5g'],
                   username=mydict['username'],
                   passwd=mydict['passwd'],
                   macs={2: mydict['mac2g'], 5: mydict['mac5g']})

    def ap_cfg(self, channel, bw=0, chains='3x3', band=5):
        ifname = self.ifs[band]
        cmd_list = []

        if band == 5 and bw != 0:
            cmd_list.append(wl_cmd(ifname, 'chanspec ' + str(channel) + '/' + str(bw)))
            cmd_list.append(wl_cmd(ifname, 'radar 0'))
            cmd_list.append(wl_cmd(ifname, 'spect 0'))
            cmd_list.append(wl_cmd(ifname, 'dfs_preism 1'))
            cmd_list.append(wl_cmd(ifname, 'dfs_postism 1'))
        elif bw != 0:
            cmd_list.append(wl_cmd(ifname, 'chanspec -s 0 -b 2 -c ' + str(channel) + ' -w ' + str(bw)))

        if chains == '3x3':
            cmd_list.append(wl_cmd(ifname, 'rxchain 7'))
            cmd_list.append(wl_cmd(ifname, 'txchain 7'))
        elif chains == '2x2':
            cmd_list.append(wl_cmd(ifname, 'rxchain 3'))
            cmd_list.append(wl_cmd(ifname, 'txchain 3'))
        elif chains == '1x1':
            cmd_list.append(wl_cmd(ifname, 'rxchain 1'))
            cmd_list.append(wl_cmd(ifname, 'txchain 1'))
        return cmd_list

    def run_command(self, command_list):
        return do_remote(self.hostname, command_list, self.username, self.passwd)

    def ap_mode(self, extra_cmds=None, band=5):
        ifname = self.ifs[band]
        cmd_list = []
        cmd_list.append(wl_cmd(ifname, 'down'))
        cmd_list.append(wl_cmd(ifname, 'ap 1'))

        if extra_cmds is not None:
            cmd_list = cmd_list + extra_cmds

        cmd_list.append(wl_cmd(ifname, 'ssid kedi'))
        cmd_list.append('ifconfig %s down' % ifname)
        cmd_list.append('ifconfig %s up' % ifname)
        cmd_list.append(wl_cmd(ifname, 'bss up'))
        cmd_list.append(wl_cmd(ifname, 'up'))
        cmd_list.append(wl_cmd(ifname, 'status'))
        cmd_list.append(wl_cmd(ifname, 'assoclist'))
        self.run_command(cmd_list)

    def sta_mode(self, extra_cmds=None, band=5, ssid='kedi'):
        ifname = self.ifs[band]
        cmd_list = []
        cmd_list.append(wl_cmd(ifname, 'down'))
        cmd_list.append(wl_cmd(ifname, 'ap 0'))
        if extra_cmds is not None:
            cmd_list = cmd_list + extra_cmds
        cmd_list.append(wl_cmd(ifname, 'up'))
        cmd_list.append(wl_cmd(ifname, 'scan -s %s' % ssid))
        cmd_list.append(wl_cmd(ifname, 'join %s' % ssid))
        cmd_list.append(wl_cmd(ifname, 'wet 1'))
        cmd_list.append(wl_cmd(ifname, 'status'))
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
        cmd_list.append(wl_cmd(ifname, 'ap 1'))
        self.run_command(cmd_list)
        self.radio_enabled = False

    def set_wds_link(self, dest_mac, extra_cmds=None, band=5):
        ifname = self.ifs[band]
        cmd_list = []
        cmd_list.append(wl_cmd(ifname, 'down'))
        cmd_list.append(wl_cmd(ifname, 'ap 1'))
        cmd_list.append(wl_cmd(ifname, 'ssid "kedi"'))

        if extra_cmds is not None:
            cmd_list = cmd_list + extra_cmds

        cmd_list.append(wl_cmd(ifname, 'wdswsec 0'))
        cmd_list.append(wl_cmd(ifname, 'wdswsec_enable 0'))
        cmd_list.append(wl_cmd(ifname, 'lazywds 0'))
        cmd_list.append(wl_cmd(ifname, 'wdstimeout 1'))
        cmd_list.append(wl_cmd(ifname, 'wds ' + dest_mac))
        cmd_list.append(wl_cmd(ifname, 'up'))

        if band == 5:
            cmd_list.append('ifconfig wds1.1 up')
            cmd_list.append('brctl addif br0.1 wds1.1')
        else:
            cmd_list.append('ifconfig wds0.1 up')
            cmd_list.append('brctl addif br0.1 wds0.1')

        self.run_command(cmd_list)

    def tear_wds_links(self, band=5):
        ifname = self.ifs[band]
        cmd_list = []
        cmd_list.append(wl_cmd(ifname, 'wds none'))
        self.run_command(cmd_list)

    def ping(self, ipaddr):
        cmd_list = []
        for e in xrange(3):
            cmd_list.append('ping ' + ipaddr + ' -c 1')
            cmd_list.append('sleep 1')
        output = self.run_command(cmd_list)

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

    def get_rssi_nrate(self, dest_mac, band=5):
        ifname = self.ifs[band]
        cmd_list = []
        cmd_list.append(wl_cmd(ifname, 'nrate'))
        cmd_list.append(wl_cmd(ifname, 'rssi ' + dest_mac))
        lines = self.run_command(cmd_list)
        return lines

    def get_switchport(self):
        return self.switchport

    def get_idle_vlan(self):
        return self.switchport + 10

    def to_control_vlan(self):
        if self.vlan != CONTROL_VLAN:
            self.sw.add_ports_to_vlan(CONTROL_VLAN, [self.switchport])
            self.vlan = CONTROL_VLAN

    def to_sink_vlan(self):
        if self.vlan != SINK_VLAN:
            self.sw.add_ports_to_vlan(SINK_VLAN, [self.switchport])
            self.vlan = SINK_VLAN

    def to_idle_vlan(self):
        if self.vlan != self.get_idle_vlan():
            self.sw.add_ports_to_vlan(self.get_idle_vlan(), [self.switchport])
            self.vlan = self.get_idle_vlan()


def main():
    pass

if __name__ == '__main__':
    main()
