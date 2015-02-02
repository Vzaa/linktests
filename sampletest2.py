import os
import time
import pexpect
import requests
from apnode import ApNode
from hp1910 import Switch1910
import pyperf.pyperfapi as perf


#SOURCEIP = '192.168.2.201'
SOURCEIP = '192.168.2.100'
SINKIP = '192.168.2.202'
SINKPORT = 10
TIMESTAMP = time.strftime("%d_%m_%y_%I_%M_%S")
TARGET_DIR = 'logs/'

CONTROL_VLAN = 2
DUMMY_VLAN = 3
SINK_VLAN = 4


def run_udp(cli_ip, serv_ip, port=4444, duration=5, bw=500, band=5, ap_src=None, ap_sink=None, filename_base='/tmp/x'):
    dev_log = []
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

    cli_log, serv_log, dev_log = (cli_log['log'], serv_log['log'], dev_log)

    with open(filename_base + '_serv.log', 'w') as writer:
        for item in serv_log:
            writer.write(item.strip() + '\n')

    with open(filename_base + '_cli.log', 'w') as writer:
        for item in cli_log:
            writer.write(item.strip() + '\n')

    with open(filename_base + '_dev.log', 'w') as writer:
        for item in dev_log:
            writer.write(item.strip() + '\n')


def run_test(ap1, ap2, band=5, channel=36, bw=80, chains='3x3', use_apsta=False, two_way=False):
    cli_log = []
    serv_log = []
    dev_log = []

    # config ap1
    ap1.to_control_vlan()
    ap1.enable_radio(band=band)
    ap1.arp_clean()
    cfg = ap1.ap_cfg(channel, bw, chains, band=band)
    if not use_apsta:
        ap1.set_wds_link(ap2.macs[band], extra_cmds=cfg, band=band)
    else:
        ap1.ap_mode(extra_cmds=cfg, band=band)
    ap1.to_idle_vlan()

    #config ap2
    ap2.to_control_vlan()
    ap2.enable_radio(band=band)
    ap2.arp_clean()
    cfg = ap2.ap_cfg(channel, bw, chains, band=band)
    if not use_apsta:
        ap2.set_wds_link(ap1.macs[band], extra_cmds=cfg, band=band)
    else:
        ap2.sta_mode(extra_cmds=cfg, band=band)
        time.sleep(3)
    ap2.to_idle_vlan()

    # add APs to their vlans for tests
    ap1.to_control_vlan()
    ap2.to_sink_vlan()

    time.sleep(3)
    print 'ping tests...'
    os.system('arp -d ' + SINKIP)
    os.system('arp -d ' + ap1.hostname)
    os.system('arp -d ' + ap2.hostname)
    ap1.ping(ap2.hostname)
    ap1.ping(SINKIP)

    ret = 1
    for e in xrange(3):
        ret = os.system('ping -c 1 ' + SINKIP)
        if ret == 0:
            break
        time.sleep(1)

    if ret != 0:
        print "can't reach the sink, skip test"
    else:
        while True:
            try:
                filename_base = '{}{}_{}_{}_{}g_ch{}_bw{}_{}'.format(TARGET_DIR, TIMESTAMP, ap1.hostname, ap2.hostname, band, channel, bw, chains)
                run_udp(SOURCEIP, SINKIP, band=band, ap_src=ap1, ap_sink=ap2, filename_base=filename_base)
            except requests.Timeout:
                continue
            except requests.ConnectionError:
                continue
            except pexpect.TIMEOUT:
                break
            break

        if two_way:
            ap2.to_idle_vlan()
            ap1.to_sink_vlan()
            ap2.to_control_vlan()
            os.system('arp -d ' + SINKIP)
            os.system('arp -d ' + ap1.hostname)
            os.system('arp -d ' + ap2.hostname)
            ret = 1
            for e in xrange(100):
                ret = os.system('ping -c 1 ' + SINKIP)
                if ret == 0:
                    break
                time.sleep(1)

            if ret == 0:
                print 'start second test'
                while True:
                    try:
                        filename_base = '{}{}_{}_{}_{}g_ch{}_bw{}_{}'.format(TARGET_DIR, TIMESTAMP, ap2.hostname, ap1.hostname, band, channel, bw, chains)
                        run_udp(SOURCEIP, SINKIP, band=band, ap_src=ap2, ap_sink=ap1, filename_base=filename_base)
                    except requests.Timeout:
                        continue
                    except requests.ConnectionError:
                        continue
                    except pexpect.TIMEOUT:
                        break
                    break

    os.system('arp -d ' + SINKIP)
    os.system('arp -d ' + ap1.hostname)
    os.system('arp -d ' + ap2.hostname)

    ap1.to_idle_vlan()
    ap2.to_idle_vlan()
    #clean ap1 state
    ap1.to_control_vlan()
    ap1.tear_wds_links(band=band)
    ap1.disable_radio(band=2)
    ap1.disable_radio(band=5)
    ap1.to_idle_vlan()

    #clean ap2 state
    ap2.to_control_vlan()
    ap2.tear_wds_links(band=band)
    ap2.disable_radio(band=2)
    ap2.disable_radio(band=5)
    ap2.to_idle_vlan()


def main():
    try:
        os.mkdir(TARGET_DIR)
    except OSError:
        pass
    sw = Switch1910('192.168.2.200', 'admin', 'admin')

    #chain_list_5g = ['2x2', '1x1']
    #bw_list_5g = [40, 80]

    chain_list_5g = ['3x3', '2x2', '1x1']
    bw_list_5g = [20, 40, 80]

    chain_list_2g = ['2x2', '1x1']
    bw_list_2g = [20, 40]

    for port in range(3, 17):
        sw.add_ports_to_vlan(port + 10, [port])
    #quit()

    ap_list = []
    ap_list.append(ApNode(hostname='192.168.2.21', switchport=3, sw=sw))
    ap_list.append(ApNode(hostname='192.168.2.22', switchport=4, sw=sw))
    ap_list.append(ApNode(hostname='192.168.2.23', switchport=5, sw=sw))
    #ap_list.append(ApNode(hostname='192.168.2.24', switchport=6, sw=sw))
    #ap_list.append(ApNode(hostname='192.168.2.25', switchport=7, sw=sw))
    #ap_list.append(ApNode(hostname='192.168.2.26', switchport=8, sw=sw))
    #ap_list.append(ApNode(hostname='192.168.2.27', switchport=9, sw=sw))

    #put the sink to sink vlan
    sw.add_ports_to_vlan(SINK_VLAN, [SINKPORT])

    for ap in ap_list:
        ap.to_idle_vlan()

    print 'Init states of APs'
    for ap in ap_list:
        while True:
            try:
                ap.to_control_vlan()
                ap.learn_macs()
                ap.disable_radio(band=2)
                ap.disable_radio(band=5)
                ap.tear_wds_links(band=2)
                ap.tear_wds_links(band=5)
                ap.to_idle_vlan()
                break
            except pexpect.EOF:
                print 'Try again...'
                pass
            except pexpect.TIMEOUT:
                print 'Try again...'
                pass

    tests_done_5g_wds = set()

    for ap1 in ap_list:
        for ap2 in ap_list:
            if ap1 is ap2:
                continue

            #check for symmetry
            test_id = (ap1.hostname, ap2.hostname)
            if test_id not in tests_done_5g_wds:
                tests_done_5g_wds.add(test_id)
            else:
                print 'skip test because of symmetry'
                continue

            test_id = (ap2.hostname, ap1.hostname)
            if test_id not in tests_done_5g_wds:
                tests_done_5g_wds.add(test_id)
            else:
                print 'skip test because of symmetry'
                continue

            for chain in chain_list_5g:
                for bw in bw_list_5g:
                    print 'Wifi {} {} {}, {} to {}'.format(5, chain, bw, ap1.hostname, ap2.hostname)
                    while True:
                        try:
                            run_test(ap1, ap2, band=5, chains=chain, channel=36, bw=bw, two_way=True)
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

            for chain in chain_list_2g:
                for bw in bw_list_2g:
                    print 'Wifi {} {} {}, {} to {}'.format(2, chain, bw, ap1.hostname, ap2.hostname)
                    while True:
                        try:
                            run_test(ap1, ap2, band=2, chains=chain, channel=6, bw=bw, use_apsta=True)
                            break
                        except pexpect.EOF:
                            print 'Try again...'
                            pass
                        except pexpect.TIMEOUT:
                            print 'Try again...'
                            pass


if __name__ == '__main__':
    main()
