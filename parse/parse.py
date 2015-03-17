"Parse logs dir"
import os
import re
import json


def parse_iperf(lines):
    "parse iperf output"
    dat = []

    idx = 0
    for line in lines:
        line = line.strip()
        if re.match(r'.*bits/sec.*', line):
            tputstr = re.search(r'[0-9]+(\.[0-9]+)? .?bits/sec', line).group(0)
            tputstr = re.search(r'[0-9]+(\.[0-9]+)?', tputstr).group(0)
            tput = float(tputstr)
            dat.append((idx, tput))
            idx += 1
    return dat


def parse_rssi(lines):
    "parse rssi output"
    dat = []

    for line in lines:
        line = line.strip()
        if re.match(r'^-', line):
            dat.append(int(line))
    return dat


def get_info_from_filename(filename):
    "extract test info from filename"
    parts = filename.split('_')
    info = dict()

    info['filename'] = filename
    info['testid'] = ''.join(parts[0:6])
    info['src'] = parts[6]
    info['dest'] = parts[7]
    info['band'] = parts[8]
    info['channel'] = parts[9]
    info['bw'] = parts[10]
    info['chain_src'] = parts[11]
    info['chain_dst'] = parts[12]
    info['type'] = parts[13].split('.')[0]
    return info


def get_data_from_file(filename):
    "open a iperf log file and get parsed (sec, tput) tuple list"
    with open(filename) as fld:
        lines = fld.readlines()
    dat = parse_iperf(lines)
    return dat


def get_rssi_vals(filename):
    "open a rssi log"
    with open(filename) as fld:
        lines = fld.readlines()
    dat = parse_rssi(lines)
    return dat


def gen_test_dict(dirname, filename):
    "return a filled dictionary from a file"
    test = get_info_from_filename(filename)
    if test['type'] == 'serv' or test['type'] == 'cli':
        test['dat'] = get_data_from_file(dirname + test['filename'])
        #test['dat_avg'] = sum([tput for secs, tput in test['dat']]) / len(test['dat'])
        test['dat'] = sum([tput for secs, tput in test['dat']]) / len(test['dat'])
    elif test['type'] == 'dev':
        test['rssi'] = get_rssi_vals(dirname + test['filename'])
        test['rssi'] = sum(test['rssi']) / len(test['rssi'])
    return test


def filter_tests(tests, testid, band, bw, channel, chain_src, chain_dst, t_type):
    "filter tests"
    filtered = [test for test in tests
                if test['channel'] == channel and
                test['testid'] == testid and
                test['chain_src'] == chain_src and
                test['chain_dst'] == chain_dst and
                test['type'] == t_type and
                test['bw'] == bw and
                test['band'] == band]
    return filtered


def parse_dir(dirname):
    "return a list of dictionaries with test data"
    filenames = os.listdir(dirname)
    tests = list()
    for filename in filenames:
        test = gen_test_dict(dirname, filename)
        tests.append(test)
    return tests


def get_unique_testids(tests):
    "return a list of unique ids in a tests list"
    testids = set()
    for test in tests:
        testids.add(test['testid'])
    return list(testids)


def main():
    "main"
    #tests = parse_dir('../logs/')
    tests = parse_dir('./5th_floor_logs/')
    testids = get_unique_testids(tests)

    for testid in testids:
        #dat = filter_tests(tests, testid, '5g', 'bw80', 'ch100', '3x3', '1x1')
        test_dat = [test for test in tests
                if test['testid'] == testid and (test['type'] == 'serv' or test['type'] == 'dev')]
        with open('%s.json' % testid, 'w') as fpd:
            json.dump(test_dat, fpd, indent=4)





    quit()
    #ch_5g= [('3x3', '3x3'), ('2x2', '2x2'), ('1x1', '1x1'), ('3x3', '2x2'), ('3x3', '1x1'), ('2x2', '1x1')]
    #ch_2g= [('2x2', '2x2'), ('1x1', '1x1'), ('2x2', '1x1')]
    #dump rssis
    ch_5g= [('3x3', '3x3')]
    ch_2g= [('2x2', '2x2')]

    #for bw in ['bw20', 'bw40', 'bw80']:
    for bw in ['bw80']:
        for cha, chb in ch_5g:
            dat = filter_tests(tests, testid, '5g', bw, 'ch100', cha, chb, 'dev')
            for item in dat:
                #print item['rssi'], item['src'], item['dest'], item['chain_src'], item['chain_dst'], item['bw']
                print item['rssi'], item['src'], item['dest'], item['band']

    #for bw in ['bw20', 'bw40']:
    for bw in ['bw40']:
        for cha, chb in ch_2g:
            dat = filter_tests(tests, testid, '2g', bw, 'ch6', cha, chb, 'dev')
            for item in dat:
                #print item['rssi'], item['src'], item['dest'], item['chain_src'], item['chain_dst'], item['bw']
                print item['rssi'], item['src'], item['dest'], item['band']


if __name__ == '__main__':
    main()
