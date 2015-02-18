import os
import time
import pexpect
import requests
from plcnode import PlcNode
from hp1910 import Switch1910
import pyperf.pyperfapi as perf


SOURCEIP = '192.168.2.201'
#SOURCEIP = '192.168.2.100'
SINKIP = '192.168.2.202'
SINKPORT = 10
TIMESTAMP = time.strftime("%d_%m_%y_%I_%M_%S")
TARGET_DIR = 'logs/'

CONTROL_VLAN = 2
DUMMY_VLAN = 3
SINK_VLAN = 4


def run_udp(cli_ip, serv_ip, port=4444, duration=5, bw=500, node_src=None, node_sink=None, filename_base='/tmp/x'):
    dev_log = []
    dev_log += node_src.get_assoc()
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
            #if node_src is not None and node_sink is not None:
                #dev_log += node_src.get_rssi_nrate(node_sink.macs[band], band=band)
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


def run_test(node1, node2, two_way=False):
    # add APs to their vlans for tests
    node1.to_control_vlan()
    node2.to_sink_vlan()

    time.sleep(3)
    print 'ping tests...'
    os.system('arp -d ' + SINKIP)
    os.system('arp -d ' + node1.hostname)
    os.system('arp -d ' + node2.hostname)
    node1.ping(node2.hostname)
    node1.ping(SINKIP)

    ret = 1
    for e in xrange(10):
        ret = os.system('ping -c 1 ' + SINKIP)
        if ret == 0:
            break
        time.sleep(1)

    if ret != 0:
        print "can't reach the sink, skip test"
    else:
        while True:
            try:
                filename_base = '{}{}_{}_{}_plc'.format(TARGET_DIR, TIMESTAMP, node1.hostname, node2.hostname)
                run_udp(SOURCEIP, SINKIP, node_src=node1, node_sink=node2, filename_base=filename_base)
            except requests.Timeout:
                continue
            except requests.ConnectionError:
                continue
            except pexpect.TIMEOUT:
                continue
            break

        if two_way:
            node2.to_idle_vlan()
            node1.to_sink_vlan()
            node2.to_control_vlan()
            os.system('arp -d ' + SINKIP)
            os.system('arp -d ' + node1.hostname)
            os.system('arp -d ' + node2.hostname)
            ret = 1
            for e in xrange(100):
                ret = os.system('ping -c 1 ' + SINKIP)
                if ret == 0:
                    break
                time.sleep(1)

            print 'start second test'
            while True:
                try:
                    filename_base = '{}{}_{}_{}_plc'.format(TARGET_DIR, TIMESTAMP, node2.hostname, node1.hostname)
                    run_udp(SOURCEIP, SINKIP, node_src=node2, node_sink=node1, filename_base=filename_base)
                except requests.Timeout:
                    continue
                except requests.ConnectionError:
                    continue
                except pexpect.TIMEOUT:
                    continue
                break

    os.system('arp -d ' + SINKIP)
    os.system('arp -d ' + node1.hostname)
    os.system('arp -d ' + node2.hostname)

    node1.to_idle_vlan()
    node2.to_idle_vlan()


def main():
    try:
        os.mkdir(TARGET_DIR)
    except OSError:
        pass
    sw = Switch1910('192.168.2.200', 'admin', 'admin')

    for port in range(3, 17):
        sw.add_ports_to_vlan(port + 10, [port])

    plc_list = []
    plc_list.append(PlcNode(hostname='192.168.2.31', switchport=12, sw=sw))
    plc_list.append(PlcNode(hostname='192.168.2.33', switchport=14, sw=sw))
    plc_list.append(PlcNode(hostname='192.168.2.34', switchport=16, sw=sw))

    sw.add_ports_to_vlan(SINK_VLAN, [SINKPORT])

    print 'Put Nodes to their idle vlans'
    for node in plc_list:
        while True:
            try:
                node.to_control_vlan()
                os.system('arp -d ' + node.hostname)
                node.brctl_timeout_set()
                node.to_idle_vlan()
                break
            except pexpect.EOF:
                print 'Try again...'
                pass
            except pexpect.TIMEOUT:
                print 'Try again...'
                pass

    tests_done = set()

    for node1 in plc_list:
        for node2 in plc_list:
            if node1 is node2:
                continue
            os.system('arp -d ' + node1.hostname)
            os.system('arp -d ' + node2.hostname)

            #check for symmetry
            test_id_a = (node1.hostname, node2.hostname)
            test_id_b = (node2.hostname, node1.hostname)
            if test_id_a not in tests_done or test_id_b not in tests_done:
                tests_done.add(test_id_a)
                tests_done.add(test_id_b)
            else:
                print 'skip test because of symmetry'
                continue

            print 'PLC {} to {}'.format(node1.hostname, node2.hostname)
            while True:
                try:
                    run_test(node1, node2, two_way=True)
                    break
                except pexpect.EOF:
                    print 'Try again...'
                    pass
                except pexpect.TIMEOUT:
                    print 'Try again...'
                    pass


if __name__ == '__main__':
    main()
