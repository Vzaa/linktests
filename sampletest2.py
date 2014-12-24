import os
import time
from apnode import ApNode
from hp1910 import Switch1910
import pyperf.pyperfapi as perf


SOURCEIP = '192.168.2.100'
SINKIP = '192.168.2.202'
SINKPORT = 14


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


def run_test(sw, ap1, ap2, band=5, channel=36, bw=80, chains='3x3'):
    os.system('arp -d ' + SINKIP)
    sw.add_ports_to_vlan(3, [ap1.switchport])
    sw.add_ports_to_vlan(4, [ap2.switchport, SINKPORT])

    sw.add_ports_to_vlan(2, [ap1.switchport])
    ap1.learn_macs()
    sw.add_ports_to_vlan(3, [ap1.switchport])

    sw.add_ports_to_vlan(2, [ap2.switchport])
    ap2.learn_macs()
    sw.add_ports_to_vlan(4, [ap2.switchport])

    # config aps
    sw.add_ports_to_vlan(2, [ap1.switchport])
    ap1.arp_clean()
    ap1.tear_wds_links(band=band)
    cfg = ap1.ap_cfg(channel, bw, chains, band=band)
    ap1.set_wds_link(ap2.macs[band], extra_cmds=cfg, band=band)
    sw.add_ports_to_vlan(3, [ap1.switchport])

    sw.add_ports_to_vlan(2, [ap2.switchport])
    ap2.arp_clean()
    ap2.tear_wds_links(band=band)
    cfg = ap2.ap_cfg(channel, bw, chains, band=band)
    ap2.set_wds_link(ap1.macs[band], extra_cmds=cfg, band=band)
    sw.add_ports_to_vlan(4, [ap2.switchport])

    # add APs and generators to their respective vlans
    sw.add_ports_to_vlan(2, [ap1.switchport])
    sw.add_ports_to_vlan(4, [SINKPORT, ap2.switchport])

    ap1.ping(SOURCEIP)
    ap1.ping(ap2.hostname)
    ap1.ping(SINKIP)
    print "start test"
    # run udp test
    run_udp(SOURCEIP, SINKIP)
    #run_udp(SINKIP, SOURCEIP)

    sw.add_ports_to_vlan(2, [ap1.switchport])
    ap1.tear_wds_links(band=band)
    sw.add_ports_to_vlan(3, [ap1.switchport])

    sw.add_ports_to_vlan(2, [ap2.switchport])
    ap2.tear_wds_links(band=band)
    sw.add_ports_to_vlan(4, [ap2.switchport])

    sw.add_ports_to_vlan(3, [ap1.switchport])
    sw.add_ports_to_vlan(4, [ap2.switchport, SINKPORT])


def main():
    sw = Switch1910('192.168.2.200', 'admin', 'admin')
    #sw.add_ports_to_vlan(2, [13, 15])
    #sw.add_ports_to_vlan(2, [PORTA, SINKPORT])
    #quit()
    ap1 = ApNode(hostname='192.168.2.21', switchport=15, username='root', passwd=None)
    ap2 = ApNode(hostname='192.168.2.22', switchport=13, username='root', passwd=None)

    chain_list = ['2x2', '1x1']
    bw_list = [40, 20]

    for chain in chain_list:
        for bw in bw_list:
            print "{} {}".format(bw, chain)
            run_test(sw, ap1, ap2, band=2, chains=chain, channel=1, bw=bw)
    #run_test(sw, ap2, ap1)


if __name__ == '__main__':
    main()
