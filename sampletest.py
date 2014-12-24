import time
from apnode import ApNode
from hp1910 import Switch1910
import pyperf.pyperfapi as perf


GENA = '192.168.2.201'
PORTA = 16
GENB = '192.168.2.202'
PORTB = 14


def run_udp(cli_ip, serv_ip):
    time.sleep(1)
    print 'start server'
    serv_id = perf.udp_server_start(serv_ip, 4444)
    print 'start client'
    cli_id = perf.udp_client_start(cli_ip, 4444, serv_ip, 5, 1000)

    while True:
        cli_info = perf.get_info(cli_ip, 4444, cli_id)
        if cli_info['running']:
            time.sleep(2)
            print 'running...'
        else:
            break

    print 'done'
    time.sleep(2)
    print 'stop server'
    perf.stop(serv_ip, 4444, serv_id)
    print 'cli log get'
    cli_log = perf.get_log(cli_ip, 4444, cli_id)
    print 'server log get'
    serv_log = perf.get_log(serv_ip, 4444, serv_id)

    for line in cli_log['log']:
        print line,
    for line in serv_log['log']:
        print line,


def main():
    sw = Switch1910('192.168.2.200', 'admin', 'admin')
    #sw.add_ports_to_vlan(2, [15])
    #sw.add_ports_to_vlan(2, [PORTA, PORTB])
    #quit()
    ap1 = ApNode(hostname='192.168.2.21', switchport=15, username='root', passwd=None)
    ap2 = ApNode(hostname='192.168.2.22', switchport=13, username='root', passwd=None)

    sw.add_ports_to_vlan(3, [ap1.switchport, PORTA])
    sw.add_ports_to_vlan(4, [ap2.switchport, PORTB])

    sw.add_ports_to_vlan(2, [ap1.switchport])
    ap1.learn_macs()
    sw.add_ports_to_vlan(3, [ap1.switchport])

    sw.add_ports_to_vlan(2, [ap2.switchport])
    ap2.learn_macs()
    sw.add_ports_to_vlan(4, [ap2.switchport])

    # config aps
    sw.add_ports_to_vlan(2, [ap1.switchport])
    ap1.arp_clean()
    ap1.tear_wds_links(band=5)
    ap1.set_wds_link(ap2.macs[5], band=5)
    sw.add_ports_to_vlan(3, [ap1.switchport])

    sw.add_ports_to_vlan(2, [ap2.switchport])
    ap2.arp_clean()
    ap2.tear_wds_links(band=5)
    ap2.set_wds_link(ap1.macs[5], band=5)
    sw.add_ports_to_vlan(4, [ap2.switchport])

    # add APs and generators to their respective vlans
    sw.add_ports_to_vlan(2, [PORTA, ap1.switchport])
    sw.add_ports_to_vlan(4, [PORTB, ap2.switchport])

    ap1.ping(GENA)
    ap1.ping(ap2.hostname)
    ap1.ping(GENB)
    print "start test"
    # run udp test
    run_udp(GENA, GENB)
    #run_udp(GENB, GENA)

    sw.add_ports_to_vlan(2, [ap1.switchport])
    ap1.tear_wds_links(band=5)
    sw.add_ports_to_vlan(3, [ap1.switchport])

    sw.add_ports_to_vlan(2, [ap2.switchport])
    ap2.tear_wds_links(band=5)
    sw.add_ports_to_vlan(4, [ap2.switchport])

    sw.add_ports_to_vlan(3, [ap1.switchport, PORTA])
    sw.add_ports_to_vlan(4, [ap2.switchport, PORTB])


if __name__ == '__main__':
    main()
