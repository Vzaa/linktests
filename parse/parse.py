"Parse logs dir"
import os
import re
import json

import matplotlib.pyplot as plt
import numpy as np


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


def filter_tests(tests, testid, band, bw, chain_src, chain_dst, t_type):
    "filter tests"
    filtered = [test for test in tests
                if test['testid'] == testid and
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

def get_unique_nodes(tests):
    "return a list of unique nodes in a tests list"
    nodes = set()
    for test in tests:
        nodes.add(test['src'])
        nodes.add(test['dest'])
    return list(nodes)


def plot_heatmap(mat, filename, vmin=0, vmax=600):
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

    plt.savefig('./plots/%s.png' % filename)

def get_dat_matrix(tests, testid, nodes, band, bw, chain_src, chain_dst):
    mat = []
    table = filter_tests(tests, testid, band, bw, chain_src, chain_dst, 'serv')
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
    tests = parse_dir('./5th_floor_logs/')
    testids = get_unique_testids(tests)

    ch_5g = [('3x3', '3x3'), ('2x2', '2x2'), ('1x1', '1x1'), ('3x3', '2x2'), ('3x3', '1x1'), ('2x2', '1x1')]
    ch_2g = [('2x2', '2x2'), ('1x1', '1x1'), ('2x2', '1x1')]

    bw_2g = ['bw20', 'bw40']
    bw_5g = ['bw20', 'bw40', 'bw80']


    for testid in testids:
        nodes = get_unique_nodes(tests) #TODO: check testid
        for bw in bw_5g:
            for (chain_src, chain_dst) in ch_5g:
                mat = get_dat_matrix(tests, testid, nodes, '5g', bw, chain_src, chain_dst)
                filename = "%s_%s_%s_%s" % ('5g', chain_src, chain_dst, bw)
                plt.clf()
                plot_heatmap(mat, filename)
                mat = get_rssi_mat(tests, testid, nodes, '5g', bw, chain_src, chain_dst)
                filename = "%s_%s_%s_%s_rssi" % ('5g', chain_src, chain_dst, bw)
                plt.clf()
                plot_heatmap(mat, filename, -100, 0)

        for bw in bw_2g:
            for (chain_src, chain_dst) in ch_2g:
                mat = get_dat_matrix(tests, testid, nodes, '2g', bw, chain_src, chain_dst)
                filename = "%s_%s_%s_%s" % ('2g', chain_src, chain_dst, bw)
                plt.clf()
                plot_heatmap(mat, filename)
                mat = get_rssi_mat(tests, testid, nodes, '2g', bw, chain_src, chain_dst)
                filename = "%s_%s_%s_%s_rssi" % ('2g', chain_src, chain_dst, bw)
                plt.clf()
                plot_heatmap(mat, filename, -100, 0)

        test_dat = [test for test in tests
                if test['testid'] == testid and (test['type'] == 'serv' or test['type'] == 'dev')]
        with open('%s.json' % testid, 'w') as fpd:
            json.dump(test_dat, fpd, indent=4)


if __name__ == '__main__':
    main()
