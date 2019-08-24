#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import xlsxwriter
import sys
import csv
import pandas as pd
import datetime
import xlrd
import time
from pandas import ExcelWriter
from pandas import ExcelFile


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


def add_sheet_to_workbook(workbook, dir_path, files,share_name,sheets,dbsize,dbsize_sheet):
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
                dbsize_sheet.append(sht_name)
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


def open_xls(file):
    try:
        fh = xlrd.open_workbook(file)
        fh.release_resources()
        return fh
    except Exception as e:
        print(str("open exception，error：" + e))

#存储所有读取的结果
filevalue=[]
#存储一个标签的结果
svalue=[]
#存储一行结果
rvalue=[]
# #存储各sheet名
# shname=[]

cmpvalue=[]
#设置要合并的所有文件
summary_xls={}
#设置合并到的文件


# 获取所有sheet
def getsheet(fh):
    return fh.sheets()[0]

# 读取某个sheet的行数
def getnrows(fh, sheet):
    table = fh.sheets()[sheet]
    content = table.nrows
    return content

sn=1
def getsvalue(k):
    fn=len(summary_xls)
    for z in range(k,k+fn):
        cmpvalue.append(svalue[0][0][z])
    return cmpvalue

def open_excel(file= 'file.xls'):
    try:
        data = xlrd.open_workbook(file)
        return data
    except Exception as e:
        print(str("open exception，error：" + e))

def excel_table_byname(file='file.xls', colnameindex=0, by_name=u'Sheet1'):
    data = open_excel(file)
    table = data.sheet_by_name(by_name)
    nrows = table.nrows  # 行数
    colnames = table.row_values(colnameindex)  # 某一行数据
    list = []
    for rownum in range(1, nrows):
        row = table.row_values(rownum)
        if row:
            app = {}
            for i in range(len(colnames)):
                app[colnames[i]] = row[i]
            list.append(app)
    return list

#读取某个文件的内容并返回所有行的值
def getfilect(fl,sum_shname,shnum):
    fh = xlrd.open_workbook(fl, on_demand = True)
    table=fh.sheet_by_index(0)  #.sheet_by_name(sum_shname)
    num=getnrows(fh,shnum)
    lenrvalue=len(rvalue)
    for row in range(0,num):
        rdata=table.row_values(row)
        rvalue.append(rdata)
    print(rvalue[lenrvalue:])
    filevalue.append(rvalue[lenrvalue:])
    return filevalue


def fill_comparison(comparison_file):
    svalue.append([])
    for shnum in range(0, 1):
        for key,value in summary_xls.items():
            print('reading file：{}{}{}{}'.format(key, "... ..." , value ,"…"))
            filevalue = getfilect(key, value, shnum)

            svalue[shnum].append(filevalue)

    sn = 1  # 只读一个sheet
    fn = len(summary_xls)
    cpwkbook=xlsxwriter.Workbook(comparison_file)
    compsheet = cpwkbook.add_worksheet('comparison')
    num_format = cpwkbook.add_format()
    num_format.set_num_format('#,##0.00')
    polit=0
    linenum=0
    #依次遍历每个sheet中的数据
    for s in range(0,sn*fn,fn):
        thisvalue=getsvalue(s)
        tvalue=thisvalue[polit:]
        #将一个标签的内容写入新文件中
        for a in range(0,len(tvalue)):
            for b in range(0,len(tvalue[a])):
                for c in range(0,len(tvalue[a][b])):
                    data=tvalue[a][b][c]
                    compsheet.write(linenum,c,data)
                linenum+=1
        #叠加关系，需要设置分割点
        polit=len(thisvalue)
    cpwkbook.close()


def fill_summary(workbook, sheet,row_idx,sheetname,dbsize,dbsize_sheet):
    num_format = workbook.add_format()
    num_format.set_num_format('#,##0.00')

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

    ssl=len(columns_ss)
    szl=len(columns_sz)
    # add the first colum of head tt
    # sheet.write(row_idx, 0, 'Vanda vs Intel-Snappy')

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


def crComparison(result_dir_list):
    # comparison excel file
    st = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    comparison_file = os.path.join(result_dir_list[0], '{0}_{1}{2}'.format(st, 'comparison', '.xlsx'))

    for result_dir in result_dir_list:
        excel_dir = result_dir
        dir_list = os.listdir(result_dir)
        workbooks = {}
        for d in dir_list:
            pp = os.path.join(result_dir, d)
            file_ext = os.path.splitext(pp)[1]
            if os.path.isfile(pp) and file_ext == '.xlsx' :
                summary_xls[pp]=0
                with open(pp, 'a+') as f:
                    f.writelines('aaa')
                    f.close()
                    print('aaa')

        fill_comparison(comparison_file)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Please input the csv folder")
        exit(0)

    result_dir_list = [
        sys.argv[1],
    ]
    if len(sys.argv) == 3:
        if sys.argv[2] == 'docompare':
            crComparison(result_dir_list)
            exit(0)

    # comparison excel file
    # st=datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    # comparison_file = os.path.join(result_dir_list[0], '{0}_{1}{2}'.format(st,'comparison', '.xlsx'))

    for result_dir in result_dir_list:
        excel_dir = result_dir
        dir_list = os.listdir(result_dir)
        workbooks = {}
        for d in dir_list:
            pp = os.path.join(result_dir,d)
            dir_path = os.path.join(pp,'csv')
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                summary_row_idx = 0
                comparison_row_idx = 0
                prefix = get_prefix(d)
                if len(d) > len(prefix) + 1:
                    case_name = d[len(prefix):].strip('-').strip('_')
                else:
                    case_name = d
                dbsize_sheet=[]
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
                summary_name = '{0}-{1}'.format('SUM',share_name)
                if out_file in workbooks.keys():
                    workbook = workbooks[out_file]
                else:
                    workbook = xlsxwriter.Workbook(out_file)
                    summary_sheet=workbook.add_worksheet(summary_name)
                    workbooks[out_file] = workbook
                files = collect_result_files(dir_path)
                count = add_sheet_to_workbook(workbook, dir_path, files,share_name,sheets_list,dbsize,dbsize_sheet)
                summary_row_idx = fill_summary(workbook,summary_sheet,summary_row_idx,sheets_list,dbsize,dbsize_sheet)
                summary_xls[out_file]=summary_name
        for workbook in workbooks:
            workbooks[workbook].close()

    # create comparison xlsx
    # fill_comparison(comparison_file)
