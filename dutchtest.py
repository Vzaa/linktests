import os
import json
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


def run_tput(cli_ip, serv_ip, protocol='udp', port=4444, duration=60, udp_bw=600, tcp_pairs=1, band=5, filename_base='/tmp/x', sw=None):
    dev_log = []
    sw.add_ports_to_vlan(CONTROL_VLAN, [SINKPORT])
    os.system('arp -d ' + SINKIP)
    print 'start server'
    while True:
        try:
            perf.stop(serv_ip, port, -1)
            if protocol == 'udp':
                serv_id = perf.udp_server_start(serv_ip, port)
            elif protocol == 'tcp':
                serv_id = perf.tcp_server_start(serv_ip, port)
        except requests.Timeout:
            continue
        break
    sw.add_ports_to_vlan(SINK_VLAN, [SINKPORT])
    os.system('arp -d ' + SINKIP)
    print 'start client'
    while True:
        try:
            perf.stop(cli_ip, port, -1)
            if protocol == 'udp':
                cli_id = perf.udp_client_start(cli_ip, port, serv_ip, duration, udp_bw)
            elif protocol == 'tcp':
                cli_id = perf.tcp_client_start(cli_ip, port, serv_ip, duration, tcp_pairs)
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


def run_test(ap2, port, name, direction='down', band=5, channel=36, ssid='', chains=None, protocol='tcp'):
    sw = ap2.sw
    #config ap2
    ap2.to_control_vlan()
    ap2.enable_radio(band=band)
    ap2.arp_clean()

    cfg = None
    if chains is not None:
        cfg = ap2.ap_cfg(channel, band=band, chains=chains)
    ap2.sta_mode(extra_cmds=cfg, band=band, ssid=ssid)
    time.sleep(3)
    ap2.to_idle_vlan()

    # add APs to their vlans for tests
    if direction == 'down':
        sw.add_ports_to_vlan(CONTROL_VLAN, [port])
        ap2.to_sink_vlan()
    else:
        sw.add_ports_to_vlan(SINK_VLAN, [port])
        ap2.to_control_vlan()

    time.sleep(3)
    print 'ping tests...'

    ret = 1
    for e in xrange(10):
        os.system('arp -d ' + SINKIP)
        os.system('arp -d ' + ap2.hostname)
        ret = os.system('ping -c 1 ' + SINKIP)
        if ret == 0:
            break
        time.sleep(1)

    if ret != 0:
        print "can't reach the sink, skip test"
    else:
        while True:
            try:
                filename_base = '{}{}_{}_{}g_ch{}_{}_{}'.format(TARGET_DIR, TIMESTAMP, ap2.hostname, band, channel, name, direction)
                run_tput(SOURCEIP, SINKIP, protocol=protocol, band=band, filename_base=filename_base, sw=ap2.sw)
            except requests.Timeout:
                continue
            except requests.ConnectionError:
                continue
            except pexpect.TIMEOUT:
                continue
            break

    os.system('arp -d ' + SINKIP)
    os.system('arp -d ' + ap2.hostname)

    sw.add_ports_to_vlan(port + 10, [port])

    #clean ap2 state
    ap2.to_control_vlan()
    ap2.tear_wds_links(band=band)
    ap2.disable_radio(band=2)
    ap2.disable_radio(band=5)
    ap2.to_idle_vlan()

def log_rssi(ap2, port, name, band=5, channel=36, ssid=''):
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

    ret = 1
    for e in xrange(10):
        os.system('arp -d ' + SINKIP)
        os.system('arp -d ' + ap2.hostname)
        ret = os.system('ping -c 1 ' + SINKIP)
        if ret == 0:
            break
        time.sleep(1)

    dev_log = []
    dev_log += ap2.get_rssi_nrate(' ', ccachan=channel, band=band)
    dev_log += ap2.get_rssi_nrate(' ', ccachan=channel, band=band)

    filename_base = '{}{}_{}_{}g_ch{}_{}'.format(TARGET_DIR, TIMESTAMP, ap2.hostname, band, channel, name)
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



def test_apsta(ap_list, port, band, channel, ssid, name, chains=None, protocol='tcp'):
    for ap1 in ap_list:
        print 'Wifi {} {}'.format(band, ap1.hostname)
        while True:
            try:
                run_test(ap1, port, name, chains=chains, direction='down', band=band, channel=channel, ssid=ssid, protocol=protocol)
                #run_test(ap1, port, name, chains=chains, direction='up', band=band, channel=channel, ssid=ssid, protocol=protocol)
                log_rssi(ap1, port, name, band=band, channel=channel, ssid=ssid)
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
        #sw.add_ports_to_vlan(CONTROL_VLAN, [port])
    #sw.add_ports_to_vlan(CONTROL_VLAN, [12])
    #quit()

    with open('config.json') as fds:
        conf = json.load(fds)

    ap_list = []

    for sta in conf['sta_list']:
        ap_list.append(ApNode(hostname=sta['hostname'], switchport=sta['switchport'], sw=sw))

    #put the sink to sink vlan
    sw.add_ports_to_vlan(SINK_VLAN, [SINKPORT])

    reset_ap_states(ap_list)
    #sw.add_ports_to_vlan(CONTROL_VLAN, [3])

    for test in conf['tests']:
        for ap in conf['ap_list']:
            if ap['band'] != test['band']:
                continue
            test_apsta(ap_list, ap['switchport'], ap['band'], ap['channel'], ap['ssid'], ap['name'] + test['chains'], chains=test['chains'], protocol=test['protocol'])

if __name__ == '__main__':
    main()
