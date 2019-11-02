#!/usr/bin/env python
# -*- coding:utf-8 -*-
import re
import getopt
import os
import sys
import datetime
import pandas as pd
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
        if os.path.isfile(dir_path + '/' + f) \
                and 'insert' not in f.lower() and 'update' not in f.lower() and 'read' not in f.lower():
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


def add_sheet_to_workbook(workbook, dir_path, files, share_name,sheets,dbsize,dbsize_sheet,suffix=''):
    count = 0
    for file_name in files.keys():
        if not file_name.startswith('prepare') and 'redolog' not in file_name:
            # count += 1
            # worksheet = workbook.add_worksheet((file_name.replace('oltp_', ''))[:31] + suffix)
            # col = 0
            # for ext in sorted(files[file_name], reverse=True):
            #     if 'all_part' not in ext:
            #         col = add_csv_to_sheet(worksheet, dir_path + '/' + file_name + ext, col, suffix) + 1
            count += 1
            sht_name=file_name
            if share_name != '':
                sht_name = '{0}-{1}'.format(file_name, share_name)
            worksheet = workbook.add_worksheet(sht_name[:31])
            if 'dbsz' in sht_name:  # dbsz has the different way to add into summary
                dbszfile = os.path.join(dir_path, '{0}{1}'.format(file_name, '.csv'))
                dbszinfo = pd.read_csv(dbszfile, usecols=['workload']).to_dict(orient='dict')
                for k, v in dbszinfo['workload'].items():
                    dbsize.update({v: k + 2})
                dbsize_sheet.append(sht_name)
            else:
                sheets.append(sht_name[:31])
            col = 0
            for ext in sorted(files[file_name], reverse=True):
                sfile = os.path.join(dir_path, '{}{}'.format(file_name, ext))
                col = add_csv_to_sheet(worksheet, sfile, col) + 2
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
    help_str = 'sb-result.py -d path1,path2 -s suffix1,suffix2 -o output_xlsx_path [-t sysbench|ycsb]'
    try:
        opts, args = getopt.getopt(argv[1:], 'hd:s:o:t:')
    except getopt.GetoptError:
        print(help_str)
        sys.exit(1)

    result_dir_list = list()
    suffix_list = list()
    out_file = ''
    data_type = 'sysbench'

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
        elif opt == '-t':
            if arg.lower() in ('sysbench', 'ycsb'):
                data_type = arg

    if len(result_dir_list) == 0 or len(suffix_list) == 0 or len(out_file) == 0:
        print(help_str)
        sys.exit(2)

    if len(result_dir_list) != len(suffix_list):
        print(help_str)
        sys.exit(3)

    tuple_list = list()
    for result_dir, suffix in zip(result_dir_list, suffix_list):
        tuple_list.append((result_dir, suffix))

    return tuple_list, out_file, data_type


def fill_summary_sysbench(workbook, suffix, row_idx, dbsizes, dbsizes_physical):
    formula_average = '=AVERAGE(\'{0}\'!{1}2:{1}2000)'
    formula_average_percent = '=100-AVERAGE(\'{0}\'!{1}2:{1}2000)'
    formula_size = '={0}'
    formula_size_sector = '={0}/2/1024/1024'
    columns = [
        ('TPS', 'B', formula_average),
        ('%99 latency', 'D', formula_average),
        ('Read throughput (MB/s)', 'G', formula_average),
        ('Write throughput (MB/s)', 'H', formula_average),
        ('%util i/o', 'O', formula_average),
        ('%user cpu', 'Q', formula_average),
        ('%sys cpu', 'R', formula_average),
        ('%iowait cpu', 'S', formula_average),
        ('%cpu', 'T', formula_average_percent),
        # this fields do not use formula, instead data comes from the dicts passed in
        ('DB size (GB)', dbsizes, formula_size),
        ('DB size physical (GB)', dbsizes_physical, formula_size_sector),
    ]
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


def fill_summary_ycsb(workbook, suffix, row_idx, dbsizes, dbsizes_physical):
    formula_average = '=AVERAGE(\'{0}\'!{1}2:{1}2000)'
    formula_average_percent = '=100-AVERAGE(\'{0}\'!{1}2:{1}2000)'
    formula_size = '={0}'
    formula_size_sector = '={0}/2/1024/1024'
    workloads = [
        ('load', 'load'),
        ('100% update', 'u100'),
        ('50% read / 50% update', 'r50_u50'),
        ('90% read / 10% update', 'r90_u10'),
    ]
    columns = [
        ('ops/sec', 'A', formula_average),
        ('Read throughput (MB/s)', 'D', formula_average),
        ('Write throughput (MB/s)', 'E', formula_average),
        ('avgrq-sz', 'F', formula_average),
        ('%util i/o', 'L', formula_average),
        ('%user cpu', 'N', formula_average),
        ('%sys cpu', 'O', formula_average),
        ('%iowait cpu', 'P', formula_average),
        ('%cpu', 'Q', formula_average_percent),
        # this fields do not use formula, instead data comes from the dicts passed in
        ('DB size (GB)', dbsizes, formula_size),
        ('DB size physical (GB)', dbsizes_physical, formula_size_sector),
    ]

    # DB size here means the size before the workload runs
    workloads_dbsizes_mapping = [
        ('load', 'load'),
        ('100% update', 'u100'),
        ('50% read / 50% update', 'r50_u50'),
        ('90% read / 10% update', 'r90_u10'),
    ]
    num_format = workbook.add_format()
    num_format.set_num_format('#,##0')
    sheet = workbook.get_worksheet_by_name('summary')
    sheet.write(row_idx, 0, suffix)

    for i in range(0, len(columns)):
        sheet.write(row_idx, i + 1, columns[i][0] + '-' + suffix)
    row_idx += 1

    for i in range(0, len(workloads)):
        workload = workloads[i]
        if workload[1] + '-' + suffix not in workbook.sheetnames:
            continue
        mapping = workloads_dbsizes_mapping[i]
        sheet.write(row_idx, 0, workload[0])
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
            sheet.write(row_idx, j + 1, value, num_format)
        row_idx += 1
    return row_idx + 1


def collect_db_size_sysbench(result_dir):
    pattern = re.compile(r'.*user data size\s([0-9]+).*')
    file_ext = '.dbsize'
    magic_str = 'mysql-5.7.25'
    workloads = [
        'prepare',
        'oltp_update_index',
        'oltp_update_non_index',
        'oltp_read_write',
        'oltp_write_only',
        'oltp_read_only'
    ]

    dbsizes = {}
    dbsizes_physical = {}

    if len(result_dir) > 0 and result_dir[-1] != '/':
        result_dir += '/'

    for workload in workloads:
        wl_file = result_dir + workload + file_ext
        if not os.path.exists(wl_file):
            continue

        lines = open(wl_file, 'r').readlines()
        workload_key = workload.replace('oltp_', '')
        for line in lines:
            if line.strip('\n').strip('/')[-len(magic_str):] == magic_str:
                dbsizes[workload_key] = line.split('\t')[0]
            if line.lower().startswith('free space'):
                match = pattern.match(line.lower())
                if match:
                    dbsizes_physical[workload_key] = match.group(1)

    for workload_key in dbsizes.keys():
        if workload_key not in dbsizes_physical.keys():
            dbsizes_physical[workload_key] = int(dbsizes[workload_key]) * 2 * 1024 * 1024

    return dbsizes, dbsizes_physical

def collect_db_size_ycsb(result_dir):
    pattern = re.compile(r'.*user data size\s([0-9]+).*')
    file_ext = '.600g.dbsize'
    magic_str = 'rocksdb-5.11.3'
    workloads = [
        'load',
        'u100',
        'r50_u50',
        'r90_u10',
    ]

    dbsizes = {}
    dbsizes_physical = {}

    if len(result_dir) > 0 and result_dir[-1] != '/':
        result_dir += '/'

    for workload in workloads:
        wl_file = result_dir + workload + file_ext
        if not os.path.exists(wl_file):
            continue

        lines = open(wl_file, 'r').readlines()
        workload_key = workload
        for line in lines:
            if line.strip('\n').strip('/')[-len(magic_str):] == magic_str:
                dbsizes[workload_key] = line.split('\t')[0]
            if line.lower().startswith('free space'):
                match = pattern.match(line.lower())
                if match:
                    dbsizes_physical[workload_key] = match.group(1)

    for workload_key in dbsizes.keys():
        if workload_key not in dbsizes_physical.keys():
            dbsizes_physical[workload_key] = int(dbsizes[workload_key]) * 2 * 1024 * 1024

    return dbsizes, dbsizes_physical


def collect_result_files(dir_path):
    f = os.listdir(dir_path)
    results = dict()
    for f in f:
        if os.path.isfile(os.path.join(dir_path,f)):
            key = f.split('.')[0]
            if key not in results.keys():
                results[key] = list()
            results[key].append('.' + '.'.join(f.split('.')[1:]))
    return results


def fill_summary_mongodb(workbook, sheet,row_idx,sheetname,dbsize,dbsize_sheet,suffix):
    num_format = workbook.add_format()
    num_format.set_num_format('#,##0.0')

    formula_average = '=AVERAGE(\'{0}\'!{1}2:{1}4000)'
    formula_average_percent = '=100-AVERAGE(\'{0}\'!{1}2:{1}4000)'
    formula_size = '=\'{0}\'!{1}'
    formula_size_sector = '=\'{0}\'!{1}/2/1024/1024'
    formula_storage_saving = '=(C{0}-D{0})/C{0}'  # temporary value =(C2-D2)/C2
    parts_interval = 3
    columns_ss = [
        ['storage saving', '', formula_storage_saving]
    ]
    columns_sz = [
        ['DB size logical (GB)', 'B', formula_size],
        ['DB size physical (GB)', 'C', formula_size_sector]
    ]
    columns = [
        ['ops/sec', 'D', formula_average],
        ['%99 latency', 'M', formula_average],
        ['Read throughput (MB/s)', 'S', formula_average],
        ['Write throughput (MB/s)', 'T', formula_average],
        ['avgqu-sz', 'V', formula_average],
        ['%util i/o', 'AA', formula_average],
        ['%user cpu', 'AD', formula_average],
        ['%sys cpu', 'AE', formula_average],
        ['%iowait cpu', 'AF', formula_average],
        ['%cpu', 'AG', formula_average_percent]
    ]

    ssl=len(columns_ss)
    szl=len(columns_sz)
    # add the first colum of head tt
    sheet.write(row_idx, 0, suffix)

    # add head of stroage saving
    for i in range(0, len(columns_ss)):
        sheet.write(row_idx, i + 1, columns_ss[i][0])
    # add head of szinfo
    for i in range(0, len(columns_sz)):
        sheet.write(row_idx, i + 1+ssl, columns_sz[i][0])
    # add others data info head
    for i in range(0, len(columns)):
        sheet.write(row_idx, i + 1+ssl+szl, columns[i][0])

    for i in range(0, len(sheetname)):
        wksheet = sheetname[i]
        # get db size from dbsize sheet
        prename,suffixname=wksheet.split('-',1)
        dbsz_sheet=dbsize_sheet[0]
        dblogical_cell='{0}{1}'.format('B',dbsize[prename])
        dbphy_cell='{0}{1}'.format('C',dbsize[prename])
        columns_sz[0][1]=dblogical_cell
        columns_sz[1][1]=dbphy_cell
        if 'intel' in wksheet: # 如何是intel或者Micron的ssd, logical size = physical size
            columns_sz[1][1] = dblogical_cell
            columns_sz[1][2] = formula_size
        # get db size from dbsize sheet

        # write workload name to the first column
        sheet.write(row_idx + i + 1, 0, wksheet)

        # add db size data first
        for j in range(0, len(columns_sz)):
            column = columns_sz[j]
            value = column[2].format(dbsz_sheet, column[1])
            if not value:
                value = 0
            sheet.write(row_idx + i + 1, j + 1+ssl, value, num_format)
        # add storage saving data secound
        if 'intel-none' in wksheet:
            # 不需要计算storage saving
            pass
        elif 'vanda' in wksheet:
            for j in range(0, ssl):
                column = columns_ss[j]
                column_index=i+2 # +2 真正存放dbsize的地方 是从第3列开始 前面2列一个是workload, 另外一个是storage saving
                value = column[2].format(column_index)
                if not value:
                    value = 0
                sheet.write(row_idx + i + 1, j + 1, value, num_format)
        elif 'intel-snappy' in wksheet:
            # 需要先知道intel-none得到的存储size后才能计算 所以放到最后合并summary的时候再计算
            for j in range(0, ssl):
                columns_ss[0][2]='=(C{0}-C{1})/C{0}'
                column = columns_ss[j]
                column_index=i+2 # +2 真正存放dbsize的地方 是从第3列开始 前面2列一个是workload, 另外一个是storage saving
                value = column[2].format(column_index,column_index+7)
                if not value:
                    value = 0
                sheet.write(row_idx + i + 1, j + 1, value, num_format)
        elif 'intel-zlib' in wksheet:
            # 需要先知道intel-none得到的存储size后才能计算 所以放到最后合并summary的时候再计算
            for j in range(0, ssl):
                columns_ss[0][2]='=(C{0}-C{1})/C{0}'
                column = columns_ss[j]
                column_index=i+2 # +2 真正存放dbsize的地方 是从第3列开始 前面2列一个是workload, 另外一个是storage saving
                value = column[2].format(column_index,column_index+14)
                if not value:
                    value = 0
                sheet.write(row_idx + i + 1, j + 1, value, num_format)
        #add the others data
        workloads = ['load', 'u100', 'r50_u50', 'r90_u10']
        if prename == workloads[2] or prename == workloads[3]:
            columns[2][1] = 'AD'
            columns[3][1] = 'AE'
            columns[4][1] = 'AG'
            columns[5][1] = 'AL'
            columns[6][1] = 'AO'
            columns[7][1] = 'AP'
            columns[8][1] = 'AQ'
            columns[9][1] = 'AR'
        else:
            columns[2][1] = 'S'
            columns[3][1] = 'T'
            columns[4][1] = 'V'
            columns[5][1] = 'AA'
            columns[6][1] = 'AD'
            columns[7][1] = 'AE'
            columns[8][1] = 'AF'
            columns[9][1] = 'AG'
        for j in range(0, len(columns)):
            column = columns[j]
            value = column[2].format(wksheet, column[1])
            if not value:
                value = 0
            sheet.write(row_idx + i + 1, j + 1+ssl+szl, value, num_format)
    return row_idx + len(sheetname) + parts_interval


if __name__ == '__main__':
    # result_dirs, out_file, data_type = process_args(argv)
    if len(sys.argv) == 1:
        print("Please input the csv folder")
        exit(0)
    result_dirs = [
        sys.argv[1],
    ]
    suffix=''
    if len(sys.argv) == 3:
        suffix=sys.argv[2]

    st=datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    out_file = os.path.join(result_dirs[0], '{0}_{1}{2}'.format(st,'comparison', '.xlsx'))
    workbook = xlsxwriter.Workbook(out_file)
    summary_sheet=workbook.add_worksheet('summary')
    if not workbook:
        print('Failed to create Excel workbook!')
        sys.exit(10)

    summary_row_idx = 0
    for result_dir in result_dirs:
        dir_list = os.listdir(result_dir)
        for d in dir_list:
            pp = os.path.join(result_dir, d)
            dir_path = os.path.join(pp, 'csv')
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                # read mgod.opts.log to get some re-configruation value
                if suffix == "bfo":
                    reconfigfile = os.path.join(os.path.dirname(dir_path), "mgod.opts.log")
                    if os.path.isfile(reconfigfile):
                        with open(reconfigfile) as mf:
                            key = "Reconfiguring"
                            for ones in mf.readlines():
                                if key in ones:
                                    confi_info=ones.split('"')
                                    pmin = re.compile(r'.*threads_min=([0-9]+).*')
                                    match = pmin.match(ones)
                                    if match:
                                        evc_min=match.group(1)
                                    pmax = re.compile(r'.*threads_max=([0-9]+).*')
                                    match = pmax.match(ones)
                                    if match:
                                        evc_max=match.group(1)
                                    pdirty = re.compile(r'.*eviction_dirty_target=([0-9]+).*')
                                    match = pdirty.match(ones)
                                    if match:
                                        evc_dirty=match.group(1)
                                    ptarget = re.compile(r'.*eviction_target=([0-9]+).*')
                                    match = ptarget.match(ones)
                                    if match:
                                        evc_target=match.group(1)
                                    ptrigger = re.compile(r'.*eviction_trigger=([0-9]+).*')
                                    match = ptrigger.match(ones)
                                    if match:
                                        evc_trigger=match.group(1)
                                    suffix='evcInfo_{}_{}-{}.{}.{}'.format(evc_min,evc_max,evc_trigger,evc_target,evc_dirty)

                dbsize_sheet = []
                sheets_list = []
                dbsize = {}
                # get the ssd_name coompression_mode
                share_name = ''
                ssd = ''
                comp = ''
                dbsz = ''
                maxleafsz = ''
                kvsize = ''
                benchfp = os.path.join(os.path.dirname(dir_path), "bench.info")
                if os.path.isfile(benchfp):
                    with open(benchfp) as fw:
                        rt = fw.readline().split()
                        ssd = rt[0].split('=')[1][:-4]
                        comp = rt[1].split('=')[1]
                        dbsz = rt[2].split('=')[1]
                        maxleafsz = rt[3].split('=')[1].rstrip('KB')
                        kvsize = rt[4].split('=')[1]
                        if dbsz == '2048G':
                            dbsz='2T'
                        if comp == 'none':
                            share_name = '{0}-{1}{2}-{3}'.format(ssd, dbsz, maxleafsz, kvsize)
                        else:
                            share_name = '{0}-{1}-{2}{3}-{4}'.format(ssd, comp, dbsz, maxleafsz,kvsize)
                        share_name = share_name.lstrip('.')
                        share_name = share_name.rstrip('.')
                files = collect_result_files(dir_path)
                count = add_sheet_to_workbook(workbook, dir_path, files,share_name,sheets_list, dbsize, dbsize_sheet)
                # summary_row_idx = fill_summary_fio(workbook,summary_sheet,summary_row_idx,sheets_list,
                #                                        dbsize,dbsize_sheet,'{0}-{1}'.format(kvsize,suffix))
    workbook.close()
