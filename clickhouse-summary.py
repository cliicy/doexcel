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
        if not file_name.startswith('prepare') and 'query' not in file_name:
            count += 1
            sht_name = '{0}-{1}'.format(file_name.replace(wlprefix, ''), share_name)
            worksheet = workbook.add_worksheet(sht_name[:31])
            if 'dbsz' in sht_name:  # dbsz has the different way to add into summary
                dbszfile = os.path.join(dir_path, '{0}{1}'.format(file_name, '.csv'))
                dbszinfo = pd.read_csv(dbszfile, usecols=['workload']).to_dict(orient='dict')
                for k, v in dbszinfo['workload'].items():
                    dbsize.update({v: k+2})
                dbsize_sheet.append(sht_name)
            else:
                sheets.append(sht_name[:31])
            col = 0
            for ext in sorted(files[file_name], reverse=True):
                sfile = os.path.join(dir_path, '{}{}'.format(file_name, ext))
                col = add_csv_to_sheet(worksheet, sfile, col) + 2
    return count

## there are 5 parts for every workloads,
# like: oltp_read_only.iostat.all_part.csv oltp_read_only.iostat.cpu.csv
# oltp_read_only.iostat.csv oltp_read_only.result.csv oltp_read_only.time.csv
wlprefix=""
pg_fixwls = [
        'dbsz.csv',
        'prepare.result.csv',
        'prepare.time.csv'
    ]

pg_workloads = [
        'prepare'
    ]

# pg_workloads = [
#         'q1_1',
#         'q1_2',
#         'q1_3',
#         'q2_1',
#         'q2_2',
#         'q2_3',
#         'q3_1',
#         'q3_2',
#         'q3_3',
#         'q3_4',
#         'q4_1',
#         'q4_2',
#         'q4_3'
#     ]

pg_workload_suffix = [
    'iostat.all_part.csv',
    'iostat.cpu.csv',
    'iostat.csv',
    'query.csv'
]

def collect_result_files(dir_path):
    f = os.listdir(dir_path)
    results = dict()
    for f in f:
        if os.path.isfile(os.path.join(dir_path, f)):
            key = f.split('.')[0]
            if key not in results.keys():
                results[key] = list()
            results[key].append('.' + '.'.join(f.split('.')[1:]))
    return results


def fill_summary_clickhouse(workbook, sheet,row_idx,sheetname,dbsize,dbsize_sheet,suffix):
    num_format = workbook.add_format()
    num_format.set_num_format('#,##0.0')

    formula_average = '=AVERAGE(\'{0}\'!{1}2:{1}4000)'
    formula_average_percent = '=100-AVERAGE(\'{0}\'!{1}2:{1}4000)'
    formula_size = '=\'{0}\'!{1}'
    formula_size_sector = '=\'{0}\'!{1}/2/1024/1024'
    formula_storage_saving = '=(D{0}-C{0})/D{0}'  # temporary value =(C2-D2)/C2

    parts_interval = 3
    columns_ss = [
        ['storage saving', '', formula_storage_saving]
    ]
    columns_sz = [
        ['DB size physical (GB)', 'B', formula_size_sector],
        ['DB size logical (GB)', 'C', formula_size_sector],
        ['comp_ratio', 'D', formula_size]
    ]
    columns = [
        ['query time (sec)', 'B', formula_average],
        # ['qps', 'F', formula_average],
        # ['%99 latency', 'G', formula_average],
        ['Read throughput (MB/s)', 'J', formula_average],
        # ['Write throughput (MB/s)', 'G', formula_average],
        ['avgrq-sz', 'L', formula_average],
        ['avgqu-sz', 'M', formula_average],
        ['%util i/o', 'R', formula_average],
        ['%user cpu', 'U', formula_average],
        ['%sys cpu', 'V', formula_average],
        ['%iowait cpu', 'W', formula_average],
        ['%cpu', 'X', formula_average_percent]
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
        prename = 'prepare'
        dbsz_sheet=dbsize_sheet[0]
        dblogical_cell='{0}{1}'.format('C',dbsize[prename])
        dbphy_cell='{0}{1}'.format('B',dbsize[prename])
        columns_sz[0][1]=dbphy_cell
        columns_sz[1][1]=dblogical_cell
        columns_sz[2][1]='{0}{1}'.format('D',dbsize[prename])
        # if 'intel' in wksheet: # 如果是intel或者Micron的ssd, logical size = physical size
        if 'vanda' not in wksheet: # 如果是intel或者Micron的ssd, logical size = physical size
            columns_sz[0][1] = dblogical_cell
            columns_sz[0][2] = formula_size
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
        #add comp_ratio
        for j in range(0, len(columns)):
            column = columns[j]
            value = column[2].format(wksheet, column[1])
            if not value:
                value = 0
            sheet.write(row_idx + i + 1, j + 1+ssl+szl, value, num_format)
    return row_idx + len(sheetname) + parts_interval


import glob, time
def search_all_files_return_by_time_reversed(path, reverse=True):
    return sorted(glob.glob(os.path.join(path, '*')),
                  key=lambda x: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getctime(x))),
                  reverse=reverse)


if __name__ == '__main__':
    # ## debug search csv files by modified sequence
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
                   print('todo-list')
                dbsize_sheet = []
                sheets_list = []
                dbsize = {}
                # get the ssd_name coompression_mode
                share_name=ssd = ''
                comp = ''
                dbsz = ''
                maxleafsz = ''
                kvsize = ''
                benchfp = os.path.join(os.path.dirname(dir_path), "bench.info")
                if os.path.isfile(benchfp):
                    with open(benchfp) as fw:
                        rt = fw.readline().split()
                        ssd = rt[0].split('=')[1][:-4]
                        dbsz = dbszinfo = rt[1].split('=')[1]
                        share_name = '{0}{1}'.format(ssd, dbsz)
                if dbsz == '2048G':
                    dbsz='2T'
                share_name = share_name.lstrip('.')
                share_name = share_name.rstrip('.')
                files = collect_result_files(dir_path)
                count = add_sheet_to_workbook(workbook, dir_path, files,share_name,sheets_list, dbsize, dbsize_sheet)
                summary_row_idx = fill_summary_clickhouse(workbook,summary_sheet,summary_row_idx,sheets_list,
                                                       dbsize,dbsize_sheet,'{0}-{1}'.format(kvsize,suffix))
    workbook.close()
