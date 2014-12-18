"AP node class"

from telnethelper import do_remote


class ApNode(object):
    def __init__(self, hostname, switchport,
                 plchostname='', if2g='wl0', if5g='wl1'):
        self.hostname = hostname
        self.switchport = switchport
        self.plchostname = plchostname
        self.if2g = if2g
        self.if5g = if5g
        self.radio_enabled = True

    def run_command(self, command):
        do_remote(self.hostname, command)

    def band_2_ifname(self, band):
        ifname = None
        if band == 2:
            ifname = self.if2g
        else:
            ifname = self.if5g
        return ifname

    def ap_mode(self, band=5):
        ifname = self.band_2_ifname(band)
        cmd = ''
        cmd += 'wl -i ' + ifname + ' down;'
        cmd += 'wl -i ' + ifname + ' ap 1;'
        cmd += 'wl -i ' + ifname + ' up;'
        self.run_command(cmd)

    def sta_mode(self, band=5):
        ifname = self.band_2_ifname(band)
        cmd = ''
        cmd += 'wl -i ' + ifname + ' down;'
        cmd += 'wl -i ' + ifname + ' ap 0;'
        cmd += 'wl -i ' + ifname + ' up;'
        self.run_command(cmd)

    def set_ssid(self, ssid, band=5):
        ifname = self.band_2_ifname(band)
        cmd = ''
        cmd += 'wl -i ' + ifname + ' down;'
        cmd += 'wl -i ' + ifname + ' ssid ' + ssid + ';'
        cmd += 'wl -i ' + ifname + ' up;'
        self.run_command(cmd)

    def enable_radio(self, band=5):
        ifname = self.band_2_ifname(band)
        self.run_command('wl -i ' + ifname + ' up')
        self.radio_enabled = True

    def disable_radio(self, band=5):
        ifname = self.band_2_ifname(band)
        self.run_command('wl -i ' + ifname + ' down')
        self.radio_enabled = False

    def set_wds_link(self, dest_mac, band=5):
        ifname = self.band_2_ifname(band)
        self.run_command('wl -i ' + ifname + ' wds ' + dest_mac)


def main():
    asd = ApNode('192.168.2.5', '', 2)
    asd.set_ssid('potato', band=2)
    asd.set_ssid('tomato', band=2)
    pass

if __name__ == '__main__':
    main()
