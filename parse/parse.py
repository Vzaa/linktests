"Parse logs dir"
import os
import re
import json

#import matplotlib.pyplot as plt
#import numpy as np


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

    if len(parts) == 15:
        info['filename'] = filename
        info['testid'] = ''.join(parts[0:6])
        info['src'] = parts[6]
        info['dest'] = parts[7]
        info['band'] = parts[8]
        info['channel'] = parts[9]
        info['bw'] = parts[10]
        info['chain_src'] = parts[11]
        info['chain_dst'] = parts[12]
        info['type'] = parts[14].split('.')[0]
        info['link'] = parts[13]
        info['medium'] = 'wifi'
    elif len(parts) == 14:
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
        info['link'] = 'na'
        info['medium'] = 'wifi'
    elif len(parts) == 13:
        info['filename'] = filename
        info['testid'] = ''.join(parts[0:6])
        info['src'] = parts[6]
        info['dest'] = parts[7]
        info['band'] = parts[8]
        info['channel'] = parts[9]
        info['bw'] = parts[10]
        info['chain_src'] = parts[11]
        info['chain_dst'] = parts[11]
        info['type'] = parts[12].split('.')[0]
        info['link'] = 'na'
        info['medium'] = 'wifi'
    elif len(parts) == 10:
        info['filename'] = filename
        info['testid'] = ''.join(parts[0:6])
        info['src'] = parts[6]
        info['dest'] = parts[7]
        info['type'] = parts[9].split('.')[0]
        info['link'] = 'na'
        info['medium'] = 'plc'
    elif len(parts) == 12:
        #15_04_15_08_42_52_192.168.2.102_2g_ch6_12_up_cli.log
        info['filename'] = filename
        info['testid'] = ''.join(parts[0:6])
        info['src'] = parts[6]
        info['band'] = parts[7]
        info['channel'] = parts[8]
        info['port'] = parts[9]
        info['dest'] = parts[9]
        info['direction'] = parts[10]
        info['type'] = parts[11].split('.')[0]
        info['link'] = 'na'
        info['medium'] = 'wifi'
    elif len(parts) == 11:
        #15_04_15_08_42_52_192.168.2.102_2g_ch6_12_up_cli.log
        info['filename'] = filename
        info['testid'] = ''.join(parts[0:6])
        info['src'] = parts[6]
        info['band'] = parts[7]
        info['channel'] = parts[8]
        info['port'] = parts[9]
        info['dest'] = parts[9]
        info['type'] = parts[10].split('.')[0]
        info['link'] = 'na'
        info['medium'] = 'wifi'
    else:
        print filename, len(parts)
        return None
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
    if test == None:
        return None

    if test['type'] == 'serv' or test['type'] == 'cli':
        test['dat'] = get_data_from_file(dirname + test['filename'])
        #test['dat_avg'] = sum([tput for secs, tput in test['dat']]) / len(test['dat'])
        try:
            test['dat'] = sum([tput for secs, tput in test['dat']]) / len(test['dat'])
        except ZeroDivisionError:
            test['dat'] = 0
    elif (test['type'] == 'dev' or test['type'] == 'rssi') and test['medium'] == 'wifi':
        test['rssi'] = get_rssi_vals(dirname + test['filename'])
        try:
            test['rssi'] = sum(test['rssi']) / len(test['rssi'])
        except ZeroDivisionError:
            test['rssi'] = 0
    return test


def filter_tests(tests, testid, band, bw, chain_src, chain_dst, t_type, medium='wifi'):
    "filter tests"
    filtered = None
    if medium == 'wifi':
        filtered = [test for test in tests
                if test['testid'] == testid and
                test['medium'] == 'wifi' and
                test['chain_src'] == chain_src and
                test['chain_dst'] == chain_dst and
                test['type'] == t_type and
                test['bw'] == bw and
                test['band'] == band]
    elif medium == 'plc':
        filtered = [test for test in tests
                if test['testid'] == testid and
                test['medium'] == 'plc' and
                test['type'] == t_type]
    return filtered


def parse_dir(dirname):
    "return a list of dictionaries with test data"
    filenames = os.listdir(dirname)
    tests = list()
    for filename in filenames:
        test = gen_test_dict(dirname, filename)
        if test == None:
            continue
        tests.append(test)
    return tests


def get_unique_testids(tests):
    "return a list of unique ids in a tests list"
    testids = set()
    for test in tests:
        testids.add(test['testid'])
    return list(testids)

def get_unique_nodes(tests, testid, medium):
    "return a list of unique nodes in a tests list"
    nodes = set()
    filtered = [test for test in tests
            if test['testid'] == testid and
            test['medium'] == medium]
    for test in filtered:
        nodes.add(test['src'])
        #nodes.add(test['dest'])
    return list(nodes)

def get_unique_bands(tests, testid, medium):
    "return a list of unique nodes in a tests list"
    nodes = set()
    filtered = [test for test in tests
            if test['testid'] == testid and
            test['medium'] == medium]
    for test in filtered:
        nodes.add(test['band'])
        #nodes.add(test['dest'])
    return list(nodes)

def get_unique_ports(tests, testid, medium):
    "return a list of unique nodes in a tests list"
    nodes = set()
    filtered = [test for test in tests
            if test['testid'] == testid and
            test['medium'] == medium]
    for test in filtered:
        nodes.add(test['port'])
        #nodes.add(test['dest'])
    return list(nodes)


def plot_heatmap(mat, filename, dirname, testid, vmin=0, vmax=600):
    if len(mat) == 0:
        return
    vals = []
    column_names = range(1, 8)
    for i, row in enumerate(mat):
        for j, col in enumerate(row):
            plt.text(j - 0.15, i + 0.1, str(int(round(col))), fontsize=14, color='black')
            vals.append(col)
    plt.imshow(mat, origin='upper', interpolation='nearest', cmap='YlGn', vmin=vmin, vmax=vmax)
    plt.colorbar()
    ticksx = np.arange(0.0, 7, 1)
    plt.xticks(ticksx, column_names)
    plt.yticks(ticksx, column_names)
    plt.ylabel('Source Node')
    plt.xlabel('Destination Node')
    #plt.show()
    #exit()

    plt.savefig('%s/../plots/%s/%s.png' % (dirname, testid, filename))

def get_dat_matrix(tests, testid, nodes, band, bw, chain_src, chain_dst, medium='wifi'):
    mat = []
    table = filter_tests(tests, testid, band, bw, chain_src, chain_dst, 'serv', medium=medium)
    for node_a in nodes:
        row = []
        for node_b in nodes:
            dat = [test for test in table if test['src'] == node_a and test['dest'] == node_b]
            if len(dat) == 0:
                row.append(0)
            else:
                row.append(dat[0]['dat'])
        mat.append(row)
    return mat

def get_rssi_mat(tests, testid, nodes, band, bw, chain_src, chain_dst):
    mat = []
    table = filter_tests(tests, testid, band, bw, chain_src, chain_dst, 'dev')
    for node_a in nodes:
        row = []
        for node_b in nodes:
            dat = [test for test in table if test['src'] == node_a and test['dest'] == node_b]
            if len(dat) == 0:
                row.append(0)
            else:
                row.append(dat[0]['rssi'])
        mat.append(row)
    return mat


def main():
    "main"
    dirname = 'logs/'
    tests = parse_dir(dirname)
    testids = get_unique_testids(tests)


    #ch_5g = [('3x3', '3x3'), ('2x2', '2x2'), ('1x1', '1x1')]
    #ch_2g = [('2x2', '2x2'), ('1x1', '1x1')]
    #ch_2g = [('3x3', '3x3'), ('2x2', '2x2'), ('1x1', '1x1')]

    ch_5g = [('3x3', '3x3'), ('2x2', '2x2'), ('1x1', '1x1'), ('3x3', '2x2'), ('3x3', '1x1'), ('2x2', '1x1')]
    ch_2g = [('2x2', '2x2'), ('1x1', '1x1'), ('2x2', '1x1')]
    bw_2g = ['bw20', 'bw40']
    bw_5g = ['bw20', 'bw40', 'bw80']

    linktypes = ['wds', 'apsta', 'na']


    for testid in testids:
        try:
            os.mkdir('%s/../plots/%s/'%(dirname, testid))
        except OSError:
            pass
        nodes = sorted(get_unique_nodes(tests, testid, 'wifi'))
        for bw in bw_5g:
            for (chain_src, chain_dst) in ch_5g:
                for linktype in linktypes:
                    try:
                        filtered = [test for test in tests if test['testid'] == testid and test['band'] == '5g' and test['link'] == linktype]
                    except KeyError:
                        continue
                    if len(filtered) == 0 :
                        continue
                    mat = get_dat_matrix(filtered, testid, nodes, '5g', bw, chain_src, chain_dst)
                    filename = "%s_%s_%s_%s_%s" % ('5g', chain_src, chain_dst, bw, linktype)
                    plt.clf()
                    plot_heatmap(mat, filename, dirname, testid)
                    mat = get_rssi_mat(filtered, testid, nodes, '5g', bw, chain_src, chain_dst)
                    filename = "%s_%s_%s_%s_%s_rssi" % ('5g', chain_src, chain_dst, bw, linktype)
                    plt.clf()
                    plot_heatmap(mat, filename, dirname, testid, -100, 0)

        for bw in bw_2g:
            for (chain_src, chain_dst) in ch_2g:
                try:
                    filtered = [test for test in tests if test['testid'] == testid and test['band'] == '2g']
                except KeyError:
                    continue
                if len(filtered) == 0 :
                    continue
                mat = get_dat_matrix(tests, testid, nodes, '2g', bw, chain_src, chain_dst)
                filename = "%s_%s_%s_%s_%s" % ('2g', chain_src, chain_dst, bw, 'apsta')
                plt.clf()
                plot_heatmap(mat, filename, dirname, testid)
                mat = get_rssi_mat(tests, testid, nodes, '2g', bw, chain_src, chain_dst)
                filename = "%s_%s_%s_%s_%s_rssi" % ('2g', chain_src, chain_dst, bw, 'apsta')
                plt.clf()
                plot_heatmap(mat, filename, dirname, testid, -100, 0)
        nodes = sorted(get_unique_nodes(tests, testid, 'plc'))
        if len(nodes) == 0:
            continue
        #nodes.append(nodes.pop(0))
        mat = get_dat_matrix(tests, testid, nodes, '2g', bw, chain_src, chain_dst, medium='plc')
        filename = "%s" % ('plc')
        plt.clf()
        plot_heatmap(mat, filename, dirname, testid)

        test_dat = [test for test in tests
                if test['testid'] == testid and (test['type'] == 'serv' or test['type'] == 'dev')]
        with open('%s.json' % testid, 'w') as fpd:
            json.dump(test_dat, fpd, indent=4)


if __name__ == '__main__':
    main()
