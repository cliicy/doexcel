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
            count += 1
            sht_name = '{0}-{1}'.format(file_name.replace(wlprefix, ''), share_name)
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


## there are 5 parts for every workloads,
# like: oltp_read_only.iostat.all_part.csv oltp_read_only.iostat.cpu.csv
# oltp_read_only.iostat.csv oltp_read_only.result.csv oltp_read_only.time.csv
wlprefix="oltp_"
pg_fixwls = [
        'dbsz.csv',
        'prepare.result.csv',
        'prepare.time.csv'
    ]
# pg_workloads = [
#         'oltp_read_only',
#         'oltp_update_non_index',
#         'oltp_update_index',
#         'oltp_point_select',
#         'oltp_read_write',
#         'oltp_write_only',
#     ]

pg_workloads = [
        'read_only',
        'update_non_index',
        'update_index',
        'point_select',
        'read_write',
        'write_only',
    ]

pg_workload_suffix = [
    'iostat.all_part.csv',
    'iostat.cpu.csv',
    'iostat.csv',
    'result.csv',
    'time.csv'
]

def collect_result_files(dir_path):
    f = os.listdir(dir_path)
    results = dict()
    # rule = {pg_workloads[0]: 0, pg_workloads[1]: 1, pg_workloads[2]: 6, pg_workloads[3]: 11, pg_workloads[4]: 16,
    #         pg_workloads[5]: 21, pg_workloads[6]: 26}
    rule = {pg_fixwls[0]: 0}
    for wl in pg_workloads:
        for suffix in pg_workload_suffix:
            item='{0}{1}.{2}'.format(wlprefix,wl,suffix)
            rule[item]=len(rule)

    rule[pg_fixwls[1]] = len(rule)
    rule[pg_fixwls[2]] = len(rule)

    wlf = sorted(f, key=lambda x: rule[x])
    for f in wlf:
        if os.path.isfile(os.path.join(dir_path,f)):
            key = f.split('.')[0]
            if key not in results.keys():
                results[key] = list()
            results[key].append('.' + '.'.join(f.split('.')[1:]))
    return results


def fill_summary_postgres(workbook, sheet,row_idx,sheetname,dbsize,dbsize_sheet,suffix):
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
        ['tps', 'E', formula_average],
        ['qps', 'F', formula_average],
        ['%99 latency', 'G', formula_average],
        ['Read throughput (MB/s)', 'O', formula_average],
        ['Write throughput (MB/s)', 'P', formula_average],
        ['avgrq-sz', 'Q', formula_average],
        ['avgqu-sz', 'R', formula_average],
        ['%util i/o', 'W', formula_average],
        ['%user cpu', 'Z', formula_average],
        ['%sys cpu', 'AA', formula_average],
        ['%iowait cpu', 'AB', formula_average],
        ['%cpu', 'AC', formula_average_percent]
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
        prename = '{0}{1}'.format(wlprefix, prename)
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
        # for j in range(0, len(columns_sz)):
        #     column = columns_sz[j]
        #     value = column[2].format(dbsz_sheet, column[1])
        #     if not value:
        #         value = 0
        #     sheet.write(row_idx + i + 1, j + 1+ssl, value, num_format)
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
    # data=search_all_files_return_by_time_reversed("F:\\PostgreSQL\\benchmarks\\4.139\\1029\\pg-20191028_082618_vanda_128.18750000G_ff100\\csv")
    # print(data)
    # ## debug search csv files by modified sequence

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
                        # dbsz = dbszinfo.split('_')
                        # tblist=dbszinfo.split('.')
                        # if len(tblist) == 1:
                        #     table_size =0
                        #     table=0
                        # else:
                        #     table=tblist[0]
                        #     table_size=tblist[1]
                        # tb_size=table_size
                        # if tb_size != 0:
                        #     table_size=tb_size.split('_')[0].rstrip('G')
                        # # dbsz=int(eval(table)*eval(table_size)*200/1024/1024/1024)
                        # dbsz='{0}{1}'.format(int(table*table_size*200/1024/1024/1024),'G')
                        # if dbsz == 0:
                        #     tblist = dbszinfo.split('_')
                        #     if len(tblist) != 1:
                        #         dbsz = tblist[0]
                        # share_name = '{0}-{1}G'.format(ssd, dbsz)
                        share_name = '{0}{1}'.format(ssd, dbsz)
                if dbsz == '2048G':
                    dbsz='2T'
                share_name = share_name.lstrip('.')
                share_name = share_name.rstrip('.')
                files = collect_result_files(dir_path)
                count = add_sheet_to_workbook(workbook, dir_path, files,share_name,sheets_list, dbsize, dbsize_sheet)
                summary_row_idx = fill_summary_postgres(workbook,summary_sheet,summary_row_idx,sheets_list,
                                                       dbsize,dbsize_sheet,'{0}-{1}'.format(kvsize,suffix))
    workbook.close()
