"AP node class"

from telnethelper import do_remote_plc

CONTROL_VLAN = 2
DUMMY_VLAN = 3
SINK_VLAN = 4


class PlcNode(object):
    def __init__(self, hostname, switchport=None,
                 username='admin', passwd='admin', sw=None):
        self.hostname = hostname
        self.switchport = switchport
        self.username = username
        self.passwd = passwd
        self.sw = sw
        self.vlan = DUMMY_VLAN

    @classmethod
    def fromdict(cls, mydict):
        return cls(hostname=mydict['hostname'],
                   switchport=mydict['switchport'],
                   username=mydict['username'],
                   passwd=mydict['passwd'])

    def run_command(self, command_list):
        return do_remote_plc(self.hostname, command_list, self.username, self.passwd)

    def ping(self, ipaddr):
        cmd_list = []
        for e in xrange(3):
            cmd_list.append('ping ' + ipaddr + ' -c 1')
            cmd_list.append('sleep 1')
        output = self.run_command(cmd_list)

    def brctl_timeout_set(self):
        cmd_list = []
        cmd_list.append('brctl setageing br0 15')
        output = self.run_command(cmd_list)

    def get_assoc(self):
        cmd_list = []
        cmd_list.append('homeplugctl assocdevices')
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
    #asd = ApNode('192.168.2.5', '', 2, if2g='wl0', if5g='wl0')
    #asd.set_ssid('potato', band=2)
    #asd.set_ssid('kereviz', band=2)
    #print asd.macs
    pass

if __name__ == '__main__':
    main()
