import os
import time
import pexpect
import requests
from apnode import ApNode
from hp1910 import Switch1910
import pyperf.pyperfapi as perf
from inspect import currentframe, getframeinfo



SOURCEIP = '192.168.2.201'
#SOURCEIP = '192.168.2.100'
SINKIP = '192.168.2.202'
SINKPORT = 10
TIMESTAMP = time.strftime("%d_%m_%y_%I_%M_%S")
TARGET_DIR = 'logs/'

CONTROL_VLAN = 2
DUMMY_VLAN = 3
SINK_VLAN = 4


def run_udp(cli_ip, serv_ip, port=4444, duration=30, bw=600, band=5, ap_src=None, ap_sink=None, filename_base='/tmp/x', sw=None):
    dev_log = []
    sw.add_ports_to_vlan(CONTROL_VLAN, [SINKPORT])
    os.system('arp -d ' + SINKIP)
    print 'start server'
    while True:
        try:
            perf.stop(serv_ip, port, -1)
            serv_id = perf.udp_server_start(serv_ip, port)
        except requests.Timeout:
            continue
        break
    sw.add_ports_to_vlan(SINK_VLAN, [SINKPORT])
    os.system('arp -d ' + SINKIP)
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

    sw.add_ports_to_vlan(CONTROL_VLAN, [SINKPORT])
    os.system('arp -d ' + SINKIP)
    while True:
        try:
            perf.stop(serv_ip, port, serv_id)
            print 'cli log get'
            cli_log = perf.get_log(cli_ip, port, cli_id)
            print 'server log get'
            serv_log = perf.get_log(serv_ip, port, serv_id)
        except requests.Timeout:
            continue
        break
    sw.add_ports_to_vlan(SINK_VLAN, [SINKPORT])
    os.system('arp -d ' + SINKIP)

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


def run_test(ap1, ap2, band=5, channel=36, bw=80, chain='3x3', chain_b=None, use_apsta=False, two_way=False):

    link_type = ''
    if use_apsta:
        link_type = 'apsta'
    else:
        link_type = 'wds'

    # config ap1
    ap1.to_control_vlan()
    ap1.enable_radio(band=band)
    ap1.arp_clean()
    cfg = ap1.ap_cfg(channel, bw, chain, band=band)
    if not use_apsta:
        ap1.set_wds_link(ap2.macs[band], extra_cmds=cfg, band=band)
    else:
        ap1.ap_mode(extra_cmds=cfg, band=band)
    ap1.to_idle_vlan()

    #config ap2
    ap2.to_control_vlan()
    ap2.enable_radio(band=band)
    ap2.arp_clean()

    if chain_b is None:
        chain_b = chain

    cfg = ap2.ap_cfg(channel, bw, chain_b, band=band)
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
    #don't ping from aps as it takes long
    #ap1.ping(ap2.hostname)
    #ap1.ping(SINKIP)

    ret = 1
    for e in xrange(15):
        ret = os.system('ping -c 1 ' + SINKIP)
        if ret == 0:
            break
        time.sleep(1)

    if ret != 0:
        print "can't reach the sink, skip test"
    else:
        while True:
            try:
                filename_base = '{}{}_{}_{}_{}g_ch{}_bw{}_{}_{}_{}'.format(TARGET_DIR, TIMESTAMP, ap1.hostname, ap2.hostname, band, channel, bw, chain, chain_b, link_type)
                run_udp(SOURCEIP, SINKIP, band=band, ap_src=ap1, ap_sink=ap2, filename_base=filename_base, sw=ap1.sw)
            except requests.Timeout:
                continue
            except requests.ConnectionError:
                continue
            except pexpect.TIMEOUT:
                continue
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
                        filename_base = '{}{}_{}_{}_{}g_ch{}_bw{}_{}_{}_{}'.format(TARGET_DIR, TIMESTAMP, ap2.hostname, ap1.hostname, band, channel, bw, chain, chain_b, link_type)
                        run_udp(SOURCEIP, SINKIP, band=band, ap_src=ap2, ap_sink=ap1, filename_base=filename_base, sw=ap1.sw)
                    except requests.Timeout:
                        continue
                    except requests.ConnectionError:
                        continue
                    except pexpect.TIMEOUT:
                        continue
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


def reset_ap_states(ap_list):
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
                frameinfo = getframeinfo(currentframe())
                print frameinfo.filename, frameinfo.lineno
            except pexpect.TIMEOUT:
                print 'Try again...'
                frameinfo = getframeinfo(currentframe())
                print frameinfo.filename, frameinfo.lineno



def test_apsta(ap_list, chain_list, bw_list, band, channel):
    for ap1 in ap_list:
        for ap2 in ap_list:
            if ap1 is ap2:
                continue

            for chain_a, chain_b in chain_list:
                for bw in bw_list:
                    print 'Wifi {} {} {} {}, {} to {}'.format(band, chain_a, chain_b, bw, ap1.hostname, ap2.hostname)
                    while True:
                        try:
                            run_test(ap1, ap2, band=band, chain=chain_a, chain_b=chain_b, channel=channel, bw=bw, use_apsta=True)
                            break
                        except pexpect.EOF:
                            print 'Try again...'
                            frameinfo = getframeinfo(currentframe())
                            print frameinfo.filename, frameinfo.lineno
                        except pexpect.TIMEOUT:
                            print 'Try again...'
                            frameinfo = getframeinfo(currentframe())
                            print frameinfo.filename, frameinfo.lineno


def test_wds(ap_list, chain_list, bw_list, band, channel):
    tests_done = set()

    for ap1 in ap_list:
        for ap2 in ap_list:
            if ap1 is ap2:
                continue

            #check for symmetry
            test_id_a = (ap1.hostname, ap2.hostname)
            test_id_b = (ap2.hostname, ap1.hostname)
            if test_id_a not in tests_done or test_id_b not in tests_done:
                tests_done.add(test_id_a)
                tests_done.add(test_id_b)
            else:
                print 'skip test because of symmetry'
                continue

            for chain_a, chain_b in chain_list:
                for bw in bw_list:
                    print 'Wifi {} {} {} {}, {} to {}'.format(band, chain_a, chain_b, bw, ap1.hostname, ap2.hostname)
                    while True:
                        try:
                            run_test(ap1, ap2, band=band, chain=chain_a, chain_b=chain_b, channel=channel, bw=bw, two_way=True)
                            break
                        except pexpect.EOF:
                            print 'Try again...'
                            frameinfo = getframeinfo(currentframe())
                            print frameinfo.filename, frameinfo.lineno
                        except pexpect.TIMEOUT:
                            print 'Try again...'
                            frameinfo = getframeinfo(currentframe())
                            print frameinfo.filename, frameinfo.lineno


def main():
    try:
        os.mkdir(TARGET_DIR)
    except OSError:
        pass
    sw = Switch1910('192.168.2.200', 'admin', 'admin')

    for port in range(3, 16):
        sw.add_ports_to_vlan(port + 10, [port])

    ap_list = []
    ap_list.append(ApNode(hostname='192.168.2.21', switchport=3, sw=sw))
    ap_list.append(ApNode(hostname='192.168.2.22', switchport=4, sw=sw))
    ap_list.append(ApNode(hostname='192.168.2.23', switchport=5, sw=sw))
    ap_list.append(ApNode(hostname='192.168.2.24', switchport=6, sw=sw))
    ap_list.append(ApNode(hostname='192.168.2.25', switchport=7, sw=sw))
    ap_list.append(ApNode(hostname='192.168.2.26', switchport=8, sw=sw))
    ap_list.append(ApNode(hostname='192.168.2.27', switchport=9, sw=sw))

    #put the sink to sink vlan
    sw.add_ports_to_vlan(SINK_VLAN, [SINKPORT])

    reset_ap_states(ap_list)
    #sw.add_ports_to_vlan(CONTROL_VLAN, [3])


    #symmetric 5g wds tests
    chain_list = [('3x3', '3x3'), ('2x2', '2x2'), ('1x1', '1x1')]
    bw_list = [20, 40, 80]
    test_wds(ap_list, chain_list, bw_list, 5, 100)

    #symmetric 5g ap_sta tests
    chain_list = [('3x3', '3x3'), ('2x2', '2x2'), ('1x1', '1x1')]
    bw_list = [20, 40, 80]
    test_apsta(ap_list, chain_list, bw_list, 5, 100)

    #symmetric 2g ap-sta tests
    chain_list = [('2x2', '2x2'), ('1x1', '1x1')]
    bw_list = [20, 40]
    test_apsta(ap_list, chain_list, bw_list, 2, 6)

    #non-symmetric 2g ap-sta tests
    chain_list = [('2x2', '1x1')]
    bw_list = [20, 40]
    test_apsta(ap_list, chain_list, bw_list, 2, 6)

    #non-symmetric 5g ap-sta tests
    chain_list = [('3x3', '2x2'), ('3x3', '1x1'), ('2x2', '1x1')]
    bw_list = [20, 40, 80]
    test_apsta(ap_list, chain_list, bw_list, 5, 100)



if __name__ == '__main__':
    main()
