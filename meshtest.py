import os
import time
import pexpect
import requests
from apnode import ApNode
from plcnode import PlcNode
from hp1910 import Switch1910


SOURCEIP = '192.168.2.201'
#SOURCEIP = '192.168.2.100'
SINKIP = '192.168.2.202'
SINKPORT = 10
TIMESTAMP = time.strftime("%d_%m_%y_%I_%M_%S")
TARGET_DIR = 'logs/'


def wds_link(ap1, ap2, channel=36, bw=80, chains='3x3', band=5):

    ap2.enable_radio(band=band)
    ap2.arp_clean()
    cfg = ap2.ap_cfg(channel, bw, chains, band=band)
    ap2.set_wds_link(ap1.macs[band], extra_cmds=cfg, band=band)
    pid = ap2.eth_time_bomb()

    ap1.enable_radio(band=band)
    ap1.arp_clean()
    cfg = ap1.ap_cfg(channel, bw, chains, band=band)
    ap1.set_wds_link(ap2.macs[band], extra_cmds=cfg, band=band)

    time.sleep(3)
    os.system('arp -d ' + ap2.hostname)
    ret = 1
    for e in xrange(10):
        ret = os.system('ping -c 1 -w 1 %s' % ap2.hostname)
        if ret == 0:
            break
        time.sleep(1)

    if ret == 0:
        return pid
    else:
        return 0


def wds_cleanup(ap1, ap2, band=5):

    ap2.tear_wds_links(band=band, eth_enable=True)
    ap2.disable_radio(band=2)
    ap2.disable_radio(band=5)

    ap1.tear_wds_links(band=band)
    ap1.disable_radio(band=2)
    ap1.disable_radio(band=5)


def run_test(ap1, ap2):
    cli_log = []
    serv_log = []
    dev_log = []

    time.sleep(3)
    print 'ping tests...'
    os.system('arp -d ' + SINKIP)
    os.system('arp -d ' + ap1.hostname)
    os.system('arp -d ' + ap2.hostname)
    ap1.ping(ap2.hostname)
    ap1.ping(SINKIP)

    ret = 1
    for e in xrange(10):
        ret = os.system('ping -c 1 ' + SINKIP)
        if ret == 0:
            break
        time.sleep(1)

    os.system('arp -d ' + SINKIP)
    os.system('arp -d ' + ap1.hostname)
    os.system('arp -d ' + ap2.hostname)


def main():
    try:
        os.mkdir(TARGET_DIR)
    except OSError:
        pass

    node_list = []
    node_list.append((ApNode(hostname='192.168.2.20'), PlcNode(hostname='192.168.2.31')))
    node_list.append((ApNode(hostname='192.168.2.21'), PlcNode(hostname='192.168.2.31')))

    print 'Init states of APs'
    for wifi, plc in node_list:
        while True:
            try:
                wifi.learn_macs()
                wifi.disable_radio(band=2)
                wifi.disable_radio(band=5)
                wifi.tear_wds_links(band=2)
                wifi.tear_wds_links(band=5)
                break
            except pexpect.EOF:
                print 'Try again...'
                pass
            except pexpect.TIMEOUT:
                print 'Try again...'
                pass

    tests_done = set()

    for wifi1, plc1 in node_list:
        for wifi2, plc2 in node_list:
            if wifi1 is wifi2:
                continue

            #check for symmetry
            #test_id = (wifi1.hostname, wifi2.hostname)
            #if test_id not in tests_done:
                #tests_done.add(test_id)
            #else:
                #print 'skip test because of symmetry'
                #continue

            #test_id = (wifi2.hostname, wifi1.hostname)
            #if test_id not in tests_done:
                #tests_done.add(test_id)
            #else:
                #print 'skip test because of symmetry'
                #continue

            while True:
                try:
                    pid = wds_link(wifi1, wifi2)
                    if pid != 0:
                        wifi2.kill_pid(pid)
                    else:
                        ret = 1
                        while True:
                            ret = os.system('ping -c 1 -w 1 %s' % wifi2.hostname)
                            if ret == 0:
                                break
                            time.sleep(1)

                    ret = os.system('ping -c 5 %s' % wifi2.hostname)
                    wds_cleanup(wifi1, wifi2)
                    break
                except pexpect.EOF:
                    print 'EOF Try again...'
                    pass
                except pexpect.TIMEOUT:
                    print 'Timeout Try again...'
                    pass


if __name__ == '__main__':
    main()
