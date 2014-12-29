import os
import time
import pexpect
import requests
from apnode import ApNode
from hp1910 import Switch1910
import pyperf.pyperfapi as perf


SOURCEIP = '192.168.2.201'
SINKIP = '192.168.2.202'
SINKPORT = 10
TIMESTAMP = time.strftime("%d_%m_%y_%I_%M_%S")
TARGET_DIR = 'logs/'


def run_udp(cli_ip, serv_ip, port=4444, duration=5, bw=500, band=5, ap_src=None, ap_sink=None, is_plc=False):
    dev_log = []
    if is_plc and ap_src is not None:
        dev_log += ap_src.get_plc_info()
        #result = []
        pass
    print 'start server'
    while True:
        try:
            perf.stop(serv_ip, port, -1)
            serv_id = perf.udp_server_start(serv_ip, port)
        except requests.Timeout:
            continue
        break
    print 'start client'
    while True:
        try:
            perf.stop(cli_ip, port, -1)
            cli_id = perf.udp_client_start(cli_ip, port, serv_ip, duration, bw)
        except requests.Timeout:
            continue
        break

    while True:
        cli_info = perf.get_info(cli_ip, port, cli_id)
        if cli_info['running']:
            time.sleep(1)
            if ap_src is not None and ap_sink is not None:
                dev_log += ap_src.get_rssi_nrate(ap_sink.macs[band], band=band)
            print 'running...'
        else:
            break

    print 'done'
    print 'stop server'
    perf.stop(serv_ip, port, serv_id)
    print 'cli log get'
    cli_log = perf.get_log(cli_ip, port, cli_id)
    print 'server log get'
    serv_log = perf.get_log(serv_ip, port, serv_id)

    return (cli_log['log'], serv_log['log'], dev_log)


def run_test(sw, ap1, ap2, band=5, channel=36, bw=80, chains='3x3', use_apsta=False):
    cli_log = []
    serv_log = []
    dev_log = []
    filename_base = '{}_{}_{}_{}g_ch{}_bw{}_{}'.format(TIMESTAMP, ap1.hostname, ap2.hostname, band, channel, bw, chains)
    filename_base = TARGET_DIR + filename_base
    os.system('arp -d ' + SINKIP)
    sw.add_ports_to_vlan(3, [ap1.switchport])
    sw.add_ports_to_vlan(4, [ap2.switchport, SINKPORT])

    sw.add_ports_to_vlan(2, [ap1.switchport])
    ap1.plc_disable()
    ap1.enable_radio(band=band)
    sw.add_ports_to_vlan(3, [ap1.switchport])

    sw.add_ports_to_vlan(2, [ap2.switchport])
    ap2.plc_disable()
    ap2.enable_radio(band=band)
    sw.add_ports_to_vlan(4, [ap2.switchport])

    # config aps
    sw.add_ports_to_vlan(2, [ap1.switchport])
    ap1.arp_clean()
    ap1.tear_wds_links(band=band)
    cfg = ap1.ap_cfg(channel, bw, chains, band=band)
    if not use_apsta:
        ap1.set_wds_link(ap2.macs[band], extra_cmds=cfg, band=band)
    else:
        ap1.ap_mode(extra_cmds=cfg, band=band)
    sw.add_ports_to_vlan(3, [ap1.switchport])

    sw.add_ports_to_vlan(2, [ap2.switchport])
    ap2.arp_clean()
    ap2.tear_wds_links(band=band)
    cfg = ap2.ap_cfg(channel, bw, chains, band=band)
    if not use_apsta:
        ap2.set_wds_link(ap1.macs[band], extra_cmds=cfg, band=band)
    else:
        ap2.sta_mode(extra_cmds=cfg, band=band)
    sw.add_ports_to_vlan(4, [ap2.switchport])

    # add APs and generators to their respective vlans
    sw.add_ports_to_vlan(2, [ap1.switchport])
    sw.add_ports_to_vlan(4, [SINKPORT, ap2.switchport])

    time.sleep(2)
    print 'ping tests...'
    ap1.ping(ap2.hostname)
    ap1.ping(SINKIP)

    ret = os.system('ping -c 3 ' + SINKIP)

    if ret != 0:
        print "can't reach the sink, skip test"
    else:
        while True:
            try:
                cli_log, serv_log, dev_log = run_udp(SOURCEIP, SINKIP, band=band, ap_src=ap1, ap_sink=ap2)
            except requests.Timeout:
                continue
            break

    with open(filename_base + '_serv.log', 'w') as writer:
        for item in serv_log:
            writer.write(item.strip() + '\n')

    with open(filename_base + '_cli.log', 'w') as writer:
        for item in cli_log:
            writer.write(item.strip() + '\n')

    with open(filename_base + '_dev.log', 'w') as writer:
        for item in dev_log:
            writer.write(item.strip() + '\n')

    sw.add_ports_to_vlan(2, [ap1.switchport])
    ap1.disable_radio(band=2)
    ap1.disable_radio(band=5)
    sw.add_ports_to_vlan(3, [ap1.switchport])

    sw.add_ports_to_vlan(2, [ap2.switchport])
    ap2.tear_wds_links(band=band)
    ap2.disable_radio(band=2)
    ap2.disable_radio(band=5)
    sw.add_ports_to_vlan(4, [ap2.switchport])

    sw.add_ports_to_vlan(3, [ap1.switchport])
    sw.add_ports_to_vlan(3, [ap2.switchport])


def run_test_plc(sw, ap1, ap2):
    cli_log = []
    serv_log = []
    dev_log = []
    filename_base = '{}_{}_{}_plc'.format(TIMESTAMP, ap1.hostname, ap2.hostname)
    filename_base = TARGET_DIR + filename_base
    os.system('arp -d ' + SINKIP)
    sw.add_ports_to_vlan(3, [ap1.switchport])
    sw.add_ports_to_vlan(4, [ap2.switchport, SINKPORT])

    sw.add_ports_to_vlan(2, [ap1.switchport])
    ap1.plc_enable()
    ap1.disable_radio(band=2)
    ap1.disable_radio(band=5)
    sw.add_ports_to_vlan(3, [ap1.switchport])

    sw.add_ports_to_vlan(2, [ap2.switchport])
    ap2.plc_enable()
    ap2.disable_radio(band=2)
    ap2.disable_radio(band=5)
    sw.add_ports_to_vlan(4, [ap2.switchport])

    # config aps
    sw.add_ports_to_vlan(2, [ap1.switchport])
    ap1.arp_clean()
    sw.add_ports_to_vlan(3, [ap1.switchport])

    sw.add_ports_to_vlan(2, [ap2.switchport])
    ap2.arp_clean()
    sw.add_ports_to_vlan(4, [ap2.switchport])

    # add APs and generators to their respective vlans
    sw.add_ports_to_vlan(2, [ap1.switchport])
    sw.add_ports_to_vlan(4, [SINKPORT, ap2.switchport])

    time.sleep(2)
    print 'ping tests...'
    ap1.ping(ap2.plchostname)
    ap1.ping(ap2.hostname)
    ap1.ping(SINKIP)

    print 'ping sink...'
    ret = os.system('ping -c 3 ' + SINKIP)

    if ret != 0:
        print "can't reach the sink, skip test"
    else:
        while True:
            try:
                cli_log, serv_log, dev_log = run_udp(SOURCEIP, SINKIP, ap_src=ap1, is_plc=True)
            except requests.Timeout:
                continue
            break

    with open(filename_base + '_serv.log', 'w') as writer:
        for item in serv_log:
            writer.write(item.strip() + '\n')

    with open(filename_base + '_cli.log', 'w') as writer:
        for item in cli_log:
            writer.write(item.strip() + '\n')

    with open(filename_base + '_dev.log', 'w') as writer:
        for item in dev_log:
            writer.write(item.strip() + '\n')

    sw.add_ports_to_vlan(2, [ap1.switchport])
    ap1.plc_disable()
    sw.add_ports_to_vlan(3, [ap1.switchport])

    sw.add_ports_to_vlan(2, [ap2.switchport])
    ap2.plc_disable()
    sw.add_ports_to_vlan(4, [ap2.switchport])

    sw.add_ports_to_vlan(3, [ap1.switchport])
    sw.add_ports_to_vlan(3, [ap2.switchport])


def main():
    os.system('mkdir ' + TARGET_DIR)
    sw = Switch1910('192.168.2.200', 'admin', 'admin')
    sw.add_ports_to_vlan(3, range(3,17))
    #sw.add_ports_to_vlan(2, [13])
    #sw.add_ports_to_vlan(2, [SINKPORT])
    #quit()

    ap_list = []
    ap_list.append(ApNode(hostname='192.168.2.21', plchostname='192.168.2.31', switchport=3, username='root', passwd=None))
    ap_list.append(ApNode(hostname='192.168.2.22', plchostname='192.168.2.32', switchport=4, username='root', passwd=None))
    ap_list.append(ApNode(hostname='192.168.2.23', plchostname='192.168.2.33', switchport=5, username='root', passwd=None))
    ap_list.append(ApNode(hostname='192.168.2.24', plchostname='192.168.2.34', switchport=6, username='root', passwd=None))
    ap_list.append(ApNode(hostname='192.168.2.25', plchostname='192.168.2.35', switchport=7, username='root', passwd=None))
    ap_list.append(ApNode(hostname='192.168.2.26', plchostname='192.168.2.36', switchport=8, username='root', passwd=None))
    ap_list.append(ApNode(hostname='192.168.2.27', plchostname='192.168.2.37', switchport=9, username='root', passwd=None))

    #sw.add_ports_to_vlan(4, [ap_list[6].switchport])
    #sw.add_ports_to_vlan(2, [ap_list[1].switchport])
    #quit()

    chain_list_5g = ['3x3', '2x2', '1x1']
    bw_list_5g = [20, 40, 80]

    chain_list_2g = ['2x2', '1x1']
    bw_list_2g = [20, 40]

    #sw.add_ports_to_vlan(2, [ap_list[0].switchport])
    #quit()

    #chain_list_5g = ['3x3']
    #bw_list_5g = [80]

    #chain_list_2g = ['2x2']
    #bw_list_2g = [40]

    #run_test(sw, ap2, ap2)
    #run_test_plc(sw, ap1, ap2)
    #return 

    print 'Disable radios and plc interfaces'
    for ap in ap_list:
        while True:
            try:
                sw.add_ports_to_vlan(2, [ap.switchport])
                ap.learn_macs()
                ap.plc_disable()
                ap.disable_radio(band=2)
                ap.disable_radio(band=5)
                ap.tear_wds_links(band=2)
                ap.tear_wds_links(band=5)
                sw.add_ports_to_vlan(3, [ap.switchport])
                break
            except pexpect.EOF:
                print 'Try again...'
                pass
            except pexpect.TIMEOUT:
                print 'Try again...'
                pass


    for ap1 in ap_list:
        for ap2 in ap_list:
            if ap1 is ap2:
                continue

            print 'Running plc test {} to {}'.format(ap1.hostname, ap2.hostname)
            while True:
                try:
                    run_test_plc(sw, ap1, ap2)
                    break
                except pexpect.EOF:
                    print 'Try again...'
                    pass
                except pexpect.TIMEOUT:
                    print 'Try again...'
                    pass

            for chain in chain_list_5g:
                for bw in bw_list_5g:
                    print 'Wifi {} {} {}, {} to {}'.format(5, chain, bw, ap1.hostname, ap2.hostname)
                    while True:
                        try:
                            run_test(sw, ap1, ap2, band=5, chains=chain, channel=36, bw=bw)
                            break
                        except pexpect.EOF:
                            print 'Try again...'
                            pass
                        except pexpect.TIMEOUT:
                            print 'Try again...'
                            pass

            for chain in chain_list_2g:
                for bw in bw_list_2g:
                    print 'Wifi {} {} {}, {} to {}'.format(2, chain, bw, ap1.hostname, ap2.hostname)
                    while True:
                        try:
                            run_test(sw, ap1, ap2, band=2, chains=chain, channel=6, bw=bw, use_apsta=True)
                            break
                        except pexpect.EOF:
                            print 'Try again...'
                            pass
                        except pexpect.TIMEOUT:
                            print 'Try again...'
                            pass


if __name__ == '__main__':
    main()
