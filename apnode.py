"AP node class"

from telnethelper import do_remote, do_remote_plc


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

    def ap_cfg(self, channel, bw, chains, band=5):
        ifname = self.ifs[band]
        cmd_list = []

        if band == 5:
            cmd_list.append(wl_cmd(ifname, 'chanspec ' + str(channel) + '/' + str(bw)))
        else:
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

    def run_command_plc(self, command_list):
        return do_remote_plc(self.plchostname, command_list, 'admin', 'admin')

    def plc_disable(self):
        cmd_list = []
        #cmd_list.append('ip -s -s neigh flush all')
        cmd_list.append("IPADDR=$'" +  str(self.plchostname) + "'")
        cmd_list.append("ping ${IPADDR} -c 2; ")
        cmd_list.append("arp ${IPADDR}")
        cmd_list.append( ("MAC=$(arp ${IPADDR} | cut -d ' ' -f 4); SHORTMAC= ; "
                        "for i in 1 2 3 4 5 6; do SHORTMAC=${SHORTMAC}$(echo ${MAC} | cut -d ':' -f $i); done; echo ${SHORTMAC};") )

        cmd_list.append( ("if(et sw_mctbl port 0 | grep ${SHORTMAC}); then "
                        "et robowr 0x10 0x0 0x0940 0x02; fi; ") )

        cmd_list.append( ("if(et sw_mctbl port 1 | grep ${SHORTMAC}); then "
                        "et robowr 0x11 0x0 0x0940 0x02; fi;  sleep 1; et port_status; ") )

        self.run_command(cmd_list)

    def plc_enable(self):
        cmd_list = []
        #cmd_list.append('ip -s -s neigh flush all')
        cmd_list.append(("if(et port_status 0 | grep Down); then "
                        "et robowr 0x10 0x0 0x1140 0x02; fi;"
                        "if(et port_status 1 | grep Down); then "
                        "et robowr 0x11 0x0 0x1140 0x02; fi; sleep 3; et port_status;"))
        self.run_command(cmd_list)

    def ap_mode(self, extra_cmds=None, band=5):
        ifname = self.ifs[band]
        cmd_list = []
        cmd_list.append(wl_cmd(ifname, 'down'))
        cmd_list.append(wl_cmd(ifname, 'ap 1'))

        if extra_cmds is not None:
            cmd_list = cmd_list + extra_cmds

        cmd_list.append(wl_cmd(ifname, 'ssid kedi'))
        cmd_list.append('ifconfig wl0 down')
        cmd_list.append('ifconfig wl0 up')
        cmd_list.append(wl_cmd(ifname, 'bss up'))
        cmd_list.append(wl_cmd(ifname, 'up'))
        cmd_list.append(wl_cmd(ifname, 'status'))
        cmd_list.append(wl_cmd(ifname, 'assoclist'))
        self.run_command(cmd_list)

    def sta_mode(self, extra_cmds=None, band=5):
        ifname = self.ifs[band]
        cmd_list = []
        cmd_list.append(wl_cmd(ifname, 'down'))
        cmd_list.append(wl_cmd(ifname, 'ap 0'))
        if extra_cmds is not None:
            cmd_list = cmd_list + extra_cmds
        cmd_list.append(wl_cmd(ifname, 'up'))
        cmd_list.append(wl_cmd(ifname, 'scan -s kedi'))
        cmd_list.append(wl_cmd(ifname, 'join kedi'))
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
        cmd_list.append('ping ' + ipaddr + ' -c 3')
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

    def get_plc_info(self):
        cmd_list = []
        cmd_list.append('homeplugctl assocdevices')
        cmd_list.append('homeplugctl status')
        lines = self.run_command_plc(cmd_list)
        return lines


def main():
    #asd = ApNode('192.168.2.5', '', 2, if2g='wl0', if5g='wl0')
    #asd.set_ssid('potato', band=2)
    #asd.set_ssid('kereviz', band=2)
    #print asd.macs
    pass

if __name__ == '__main__':
    main()
