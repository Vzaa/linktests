"Parse logs dir"
#import json

import parse as p

def main():
    "main"
    dirname = '../logs/'
    tests = p.parse_dir(dirname)
    testids = p.get_unique_testids(tests)

    bands = ['2g', '5g']

    for testid in testids:
        nodes = sorted(p.get_unique_nodes(tests, testid, 'wifi'))
        ports = sorted(p.get_unique_ports(tests, testid, 'wifi'))
        bands = sorted(p.get_unique_bands(tests, testid, 'wifi'))

        print testid

        for port in ports:
            print port
            for band in bands:
                print '\t%s' % (band)
                for node in nodes:
                    try:
                        test_up = [test for test in tests \
                                if test['testid'] == testid and\
                                test['band'] == band and\
                                test['type'] == 'serv' and\
                                test['src'] == node and\
                                test['direction'] == 'up' and\
                                test['port'] == port]
                        test_down = [test for test in tests \
                                if test['testid'] == testid and\
                                test['band'] == band and\
                                test['type'] == 'serv' and\
                                test['src'] == node and\
                                test['direction'] == 'down' and\
                                test['port'] == port]
                        rssi_dat = [test for test in tests \
                                if test['testid'] == testid and\
                                test['band'] == band and\
                                test['type'] == 'rssi' and\
                                test['src'] == node and\
                                test['port'] == port]
                    except KeyError:
                        continue

                    if len(rssi_dat) == 0:
                        rssi = 0
                    else:
                        rssi = rssi_dat[0]['rssi']

                    if len(test_down) == 0:
                        test_down = 0
                    else:
                        test_down = test_down[0]['dat']

                    if len(test_up) == 0:
                        test_up = 0
                    else:
                        test_up = test_up[0]['dat']

                    print '\t%s %s %.2f %.2f' % (node, rssi, test_down, test_up)



    #ch_5g = [('3x3', '3x3'), ('2x2', '2x2'), ('1x1', '1x1')]
    #ch_2g = [('2x2', '2x2'), ('1x1', '1x1')]
    #ch_2g = [('3x3', '3x3'), ('2x2', '2x2'), ('1x1', '1x1')]

if __name__ == '__main__':
    main()
