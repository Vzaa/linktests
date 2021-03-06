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
PORTA = 11
PORTB = 12
TIMESTAMP = time.strftime("%d_%m_%y_%I_%M_%S")
TARGET_DIR = 'logs/'

CONTROL_VLAN = 2
DUMMY_VLAN = 3
SINK_VLAN = 4


def run_udp(cli_ip, serv_ip, port=4444, duration=30, bw=600, band=5, filename_base='/tmp/x', sw=None):
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


def run_test(ap2, port, band=5, channel=36, ssid=''):
    sw = ap2.sw
    #config ap2
    ap2.to_control_vlan()
    ap2.enable_radio(band=band)
    ap2.arp_clean()

    ap2.sta_mode(band=band, ssid=ssid)
    time.sleep(3)
    ap2.to_idle_vlan()

    # add APs to their vlans for tests
    sw.add_ports_to_vlan(SINK_VLAN, [port])
    ap2.to_control_vlan()

    time.sleep(3)
    print 'ping tests...'
    os.system('arp -d ' + SINKIP)
    os.system('arp -d ' + ap2.hostname)

    ret = 1
    for e in xrange(10):
        ret = os.system('ping -c 1 ' + SINKIP)
        if ret == 0:
            break
        time.sleep(1)

    dev_log = []
    dev_log += ap2.get_rssi_nrate(' ', band=band)
    dev_log += ap2.get_rssi_nrate(' ', band=band)

    filename_base = '{}{}_{}_{}g_ch{}_{}'.format(TARGET_DIR, TIMESTAMP, ap2.hostname, band, channel, port)
    with open(filename_base + '_rssi.log', 'w') as writer:
        for item in dev_log:
            writer.write(item.strip() + '\n')

    os.system('arp -d ' + SINKIP)
    os.system('arp -d ' + ap2.hostname)

    sw.add_ports_to_vlan(port + 10, [port])

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



def test_apsta(ap_list, port, band, channel, ssid):
    for ap1 in ap_list:
        print 'Wifi {} {}'.format(band, ap1.hostname)
        while True:
            try:
                run_test(ap1, port, band=band, channel=channel, ssid=ssid)
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

    #symmetric 2g ap-sta tests
    test_apsta(ap_list, PORTA, 5, 44, 'domates_a_5')
    test_apsta(ap_list, PORTB, 5, 44, 'domates_b_5')
    test_apsta(ap_list, PORTA, 2, 6, 'domates_a_2')
    test_apsta(ap_list, PORTB, 2, 6, 'domates_b_2')




if __name__ == '__main__':
    main()
