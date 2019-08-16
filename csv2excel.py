#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import xlsxwriter
import sys
import csv
import pandas as pd


def auto_str_number(text):
    import re
    pattern = re.compile(r'^\s*[+-]?\d*[.]\d+$|^\s*[+-]?\s*\d+$')
    match = pattern.match(text)
    if match:
        if '.' in text:
            return float(text)
        else:
            return int(text)
    else:
        return text.strip('\n')


def collect_result_files(dir_path):
    f = os.listdir(dir_path)
    results = dict()
    for f in f:
        if os.path.isfile(dir_path + '/' + f):
            key = f.split('.')[0]
            if key not in results.keys():
                results[key] = list()
            results[key].append('.' + '.'.join(f.split('.')[1:]))
            pass
    return results


def add_csv_to_sheet(worksheet, csv_file, start_col):
    row_idx = 0
    col_idx = 0
    for line in open(csv_file).readlines():
        col_idx = start_col
        cols = line.split(',')
        for col in cols:
            worksheet.write(row_idx, col_idx, auto_str_number(col))
            col_idx += 1
        row_idx += 1
    return col_idx


def add_sheet_to_workbook(workbook, dir_path, files,share_name,sheets,dbsize):
    count = 0
    for file_name in files.keys():
        if not file_name.startswith('prepare') and 'redolog' not in file_name:
            count += 1
            sht_name = '{0}-{1}'.format(file_name,share_name)
            worksheet = workbook.add_worksheet(sht_name[:31])
            if 'dbsz' in sht_name: # dbsz has the different way to add into summary
                dbszfile=os.path.join(dir_path,'{0}{1}'.format(file_name,'.csv'))
                dbszinfo= pd.read_csv(dbszfile, usecols=['workload']).to_dict(orient='dict')
                for k, v in dbszinfo['workload'].items():
                    dbsize.update({v: k+2})
            else:
                sheets.append(sht_name[:31])
            col = 0
            for ext in sorted(files[file_name], reverse=True):
                sfile=os.path.join(dir_path,'{}{}'.format(file_name,ext))
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
        prefix = 'ycsb-20200202'

    return prefix


def fill_summary(workbook, sheet, row_idx,sheetname,dbsize):
    formula_average = '=AVERAGE(\'{0}\'!{1}2:{1}4000)'
    formula_average_percent = '=100-AVERAGE(\'{0}\'!{1}2:{1}4000)'
    formula_size = '=\'{0}\'!{1}'
    formula_size_sector = '=\'{0}\'!{1}/2/1024/1024'
    formula_storage_saving = '=(C{0}-D{0})/C{0}' # temporary value =(C2-D2)/C2

    columns_ss = [
        ['storage saving', '', formula_storage_saving]
    ]

    columns_sz = [
        ['DB size logical (GB)', 'B', formula_size],
        ['DB size physical (GB)', 'C', formula_size_sector]
    ]

    columns = [
        ('ops/sec', 'D', formula_average),
        ('%99 latency', 'M', formula_average),
        ['Read throughput (MB/s)', 'S', formula_average],
        ['Write throughput (MB/s)', 'T', formula_average],
        ['avgqu-sz', 'V', formula_average],
        ['%util i/o', 'AA', formula_average],
        ['%user cpu', 'AD', formula_average],
        ['%sys cpu', 'AE', formula_average],
        ['%iowait cpu', 'AF', formula_average],
        ['%cpu', 'AG', formula_average_percent]
    ]

    num_format = workbook.add_format()
    num_format.set_num_format('#,##0.00')
    parts_interval=3
    ssl=len(columns_ss)
    szl=len(columns_sz)
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
        dbsz_sheet='{0}-{1}'.format('dbsz', suffixname)
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
        elif 'vanda-none' in wksheet:
            for j in range(0, ssl):
                column = columns_ss[j]
                column_index=i+2 # +2 真正存放dbsize的地方 是从第3列开始 前面2列一个是workload, 另外一个是storage saving
                value = column[2].format(column_index)
                if not value:
                    value = 0
                sheet.write(row_idx + i + 1, j + 1, value, num_format)
        elif 'intel-snappy' in wksheet:
            # 需要先知道intel-none得到的存储size后才能计算 所以放到最后合并summary的时候再计算
            pass
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
    if len(sys.argv) == 1:
        print("Please input the csv folder")
        exit(0)

    result_dir_list = [
        sys.argv[1],
    ]
    for result_dir in result_dir_list:
        excel_dir = result_dir
        dir_list = os.listdir(result_dir)

        workbooks = {}
        for d in dir_list:
            pp = os.path.join(result_dir,d)
            dir_path = os.path.join(pp,'csv')
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                summary_row_idx = 0
                prefix = get_prefix(d)
                if len(d) > len(prefix) + 1:
                    case_name = d[len(prefix):].strip('-').strip('_')
                else:
                    case_name = d
                sheets_list=[]
                dbsize={}
                out_file = os.path.join(excel_dir,'{0}{1}'.format(case_name ,'.xlsx'))

                # get the ssd_name coompression_mode
                ssd = ''
                comp = ''
                dbsz = ''
                maxleafsz = ''
                benchfp = os.path.join(os.path.dirname(dir_path), "bench.info")
                if os.path.isfile(benchfp):
                    with open(benchfp) as fw:
                        rt = fw.readline().split()
                        ssd = rt[0].split('=')[1][:-4]
                        comp = rt[1].split('=')[1]
                        dbsz = rt[2].split('=')[1]
                        maxleafsz = rt[3].split('=')[1]

                share_name = '{}-{}-{}-{}'.format(ssd, comp,dbsz,maxleafsz)
                share_name = share_name.lstrip('.')
                share_name = share_name.rstrip('.')
                summary_name = '{0}-{1}'.format('summary',share_name)
                if out_file in workbooks.keys():
                    workbook = workbooks[out_file]
                else:
                    workbook = xlsxwriter.Workbook(out_file)
                    sfxsheet=workbook.add_worksheet(summary_name)
                    workbooks[out_file] = workbook
                files = collect_result_files(dir_path)
                count = add_sheet_to_workbook(workbook, dir_path, files,share_name,sheets_list,dbsize)
                summary_row_idx = fill_summary(workbook,sfxsheet, summary_row_idx,sheets_list,dbsize)
        for workbook in workbooks:
            workbooks[workbook].close()
