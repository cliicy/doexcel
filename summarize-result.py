#!/usr/bin/env python
# -*- coding:utf-8 -*-
import re
import getopt
import os
import sys
from sys import argv

import xlsxwriter


def auto_str_number(text, suffix=''):
    pattern = re.compile(r'^\s*[+-]?\d*[.]\d+$|^\s*[+-]?\s*\d+$')
    match = pattern.match(text)
    if match:
        if '.' in text:
            return float(text)
        else:
            return int(text)
    else:
        return text.strip('\n').strip(' ') + suffix


def collect_csv_files(dir_path):
    files = os.listdir(dir_path)
    results = dict()
    for f in files:
        if os.path.isfile(os.path.join(dir_path,f)):
            key = f.split('.')[0]
            if key not in results.keys():
                results[key] = list()
            results[key].append('.' + '.'.join(f.split('.')[1:]))
            pass
    return results


def add_csv_to_sheet(worksheet, csv_file, start_col, suffix=''):
    row_idx = 0
    col_idx = 0
    for line in open(csv_file).readlines():
        col_idx = start_col
        cols = line.split(',')
        for col in cols:
            if row_idx == 0:
                worksheet.write(row_idx, col_idx, auto_str_number(col, suffix))
            else:
                worksheet.write(row_idx, col_idx, auto_str_number(col))
            col_idx += 1
        row_idx += 1
    return col_idx


def add_sheet_to_workbook(workbook, dir_path, files, suffix=''):
    count = 0
    for file_name in files.keys():
        if not file_name.startswith('prepare') and 'redolog' not in file_name:
            count += 1
            worksheet = workbook.add_worksheet((file_name.replace('oltp_', ''))[:31] + suffix)
            col = 0
            for ext in sorted(files[file_name], reverse=True):
                if 'all_part' not in ext:
                    col = add_csv_to_sheet(worksheet, dir_path + '/' + file_name + ext, col, suffix) + 1
    return count


def get_prefix(dir_name):
    prefix = 'sb-20200202_020202'

    if dir_name.startswith('sb'):
        prefix = 'sb-20200202_020202'
    elif dir_name.startswith('tpcc'):
        prefix = 'tpcc-20200202_020202'
    elif dir_name.startswith('sysbench'):
        prefix = 'sysbench-20200202_020202'
    elif dir_name.startswith('ycsb'):
        prefix = 'ycsb_200202_020202'

    return prefix


def process_args(argv):
    help_str = 'sb-result.py -d path1,path2 -s suffix1,suffix2 -o output_xlsx_path'

    try:
        opts, args = getopt.getopt(argv[1:], 'hd:s:o:')
    except getopt.GetoptError:
        print(help_str)
        sys.exit(1)

    result_dir_list = list()
    suffix_list = list()
    out_file = ''

    for opt, arg in opts:
        if opt == '-h':
            print(help_str)
            sys.exit()
        elif opt == '-d':
            result_dir_list = arg.split(',')
        elif opt == '-s':
            suffix_list = arg.split(',')
        elif opt == '-o':
            out_file = arg

    if len(result_dir_list) == 0 or len(suffix_list) == 0 or len(out_file) == 0:
        print(help_str)
        sys.exit(2)

    if len(result_dir_list) != len(suffix_list):
        print(help_str)
        sys.exit(3)

    tuple_list = list()
    for result_dir, suffix in zip(result_dir_list, suffix_list):
        tuple_list.append((result_dir, suffix))

    return tuple_list, out_file


def fill_summary_mysql(workbook, suffix, row_idx, dbsizes=0, dbsizes_physical=0):
    formula_average = '=AVERAGE(\'{0}\'!{1}2:{1}4000)'
    formula_average_percent = '=100-AVERAGE(\'{0}\'!{1}2:{1}4000)'
    formula_size = '={0}'
    formula_size_sector = '={0}/2/1024/1024'
    columns = [
        ('ops/sec', 'A', formula_average),
        ('%99 latency', 'J', formula_average),
        ('Read throughput (MB/s)', 'P', formula_average),
        ('Write throughput (MB/s)', 'Q', formula_average),
        ('%util i/o', 'X', formula_average),
        ('%user cpu', 'AA', formula_average),
        ('%sys cpu', 'AB', formula_average),
        ('%iowait cpu', 'AC', formula_average),
        ('%cpu', 'AD', formula_average_percent),
        # this fields do not use formula, instead data comes from the dicts passed in
        ('DB size (GB)', dbsizes, formula_size),
        ('DB size physical (GB)', dbsizes_physical, formula_size_sector),
    ]
    # workloads = [
    #     ('update index', 'update_index'),
    #     ('update non index', 'update_non_index'),
    #     ('read/write', 'read_write'),
    #     ('write only', 'write_only'),
    #     ('read only', 'read_only')
    # ]

    workloads = [
        ('update index', 'update_index'),
        ('update non index', 'update_non_index'),
        ('read/write', 'read_write'),
        ('write only', 'write_only'),
        ('read only', 'read_only')
    ]
    # DB size here means the size before the workload runs
    workloads_dbsizes_mapping = [
        ('update_index', 'prepare'),
        ('update_non_index', 'update_index'),
        ('read_write', 'update_non_index'),
        ('write_only', 'read_write'),
        ('read_only', 'write_only'),
    ]

    num_format = workbook.add_format()
    num_format.set_num_format('#,##0')
    sheet = workbook.get_worksheet_by_name('summary')

    sheet.write(row_idx, 0, suffix)

    for i in range(0, len(columns)):
        sheet.write(row_idx, i + 1, columns[i][0] + '-' + suffix)

    for i in range(0, len(workloads)):
        workload = workloads[i]
        mapping = workloads_dbsizes_mapping[i]
        sheet.write(row_idx + i + 1, 0, workload[0])
        for j in range(0, len(columns)):
            column = columns[j]
            if isinstance(column[1], dict):
                if mapping[1] in column[1].keys():
                    value = column[2].format(column[1][mapping[1]])
                else:
                    value = 0
            else:
                # reference to proper sheet and get the values based on the formula defined
                value = column[2].format(workload[1] + '-' + suffix, column[1])

            if not value:
                value = 0
            sheet.write(row_idx + i + 1, j + 1, value, num_format)

    return row_idx + len(workloads) + 3


# def collect_db_size_mysql(result_dir):
#     pattern = re.compile(r'.*user data size\s([0-9]+).*')
#     file_ext = '.dbsize'
#     magic_str = 'mongodb-4.0.10'
#     workloads = [
#         'load',
#         'u100',
#         'r50_u50',
#         'r90_u10'
#     ]
#
#     dbsizes = {}
#     dbsizes_physical = {}
#
#     for workload in workloads:
#         szfile = '{0}{1}'.format(workload, file_ext)
#         wl_file = os.path.join(result_dir,szfile)
#         if not os.path.exists(wl_file):
#             continue
#
#         lines = open(wl_file, 'r').readlines()
#         workload_key = workload.replace('oltp_', '')
#         for line in lines:
#             if line.strip('\n').strip('\\')[-len(magic_str):] == magic_str:
#                 dbsizes[workload_key] = line.split('\t')[0]
#             if line.lower().startswith('free space'):
#                 match = pattern.match(line.lower())
#                 if match:
#                     dbsizes_physical[workload_key] = match.group(1)
#
#     for workload_key in dbsizes.keys():
#         if workload_key not in dbsizes_physical.keys():
#             dbsizes_physical[workload_key] = int(dbsizes[workload_key]) * 2 * 1024 * 1024
#
#     return dbsizes, dbsizes_physical


if __name__ == '__main__':

    result_dirs, out_file = process_args(argv)

    workbook = xlsxwriter.Workbook(out_file)
    workbook.add_worksheet('summary')
    if not workbook:
        print('Failed to create Excel workbook!')
        sys.exit(10)

    summary_row_idx = 0
    for result_dir, suffix in result_dirs:
        # dbsizes, dbsizes_physical = collect_db_size_mysql(result_dir)

        dir_path = os.path.join(result_dir,'csv')
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            csv_files = collect_csv_files(dir_path)
            count = add_sheet_to_workbook(workbook, dir_path, csv_files, '-' + suffix)

        summary_row_idx = fill_summary_mysql(workbook, suffix, summary_row_idx)
        # summary_row_idx = fill_summary_mysql(workbook, suffix, summary_row_idx, dbsizes, dbsizes_physical)

    workbook.close()

