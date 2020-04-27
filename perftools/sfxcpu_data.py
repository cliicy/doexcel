#!/usr/bin/env python
# -*- coding:utf-8 -*-
import re
import os
import sys
import csv


def extract_cpulog(file,flag):
    # print("cpu_log=%s", file)
    cpu_dict = {}
    time_info = {}
    # the time value of 11:47:36 in 2020/04/26T11:47:36 -->
    time_list = []
    # the line number of 2020/04/26T11:47:36 -->
    ts_num = []
    init_time_serial = {}
    with open(file, 'r') as f:
        for num, value in enumerate(f, 1):
            if "-->" in value:
                ts = re.findall('\d+:\d+:\d+', value)
                time_list.append(ts[0])
                ts_num.append(num)
                time_info.update({num: ts[0]})
    # get how many lines between every 2020/04/26Txx:xx:xx,
    # which is the same for every time slot
    lines_num = len(ts_num)
    if lines_num <= 0:
        return
    gap_lines = (ts_num[1]-1)-(ts_num[0]+2)+1
    with open(file) as fr:
        flines=fr.readlines()
        for v in ts_num:
            ts = time_info.get(v)
            starts = v+2-1
            ends = starts+gap_lines
            for lines in flines[starts:ends]:
                vv = lines.split()
                pid = vv[0]
                command = vv[11]
                cpu = vv[8]
                vkey = '{0}_{1}'.format(command, pid)
                # print(vkey, "====", cpu)
                linedic = {}
                if vkey in cpu_dict.keys():
                    linedic = cpu_dict.get(vkey)
                else:
                    # for cpu_top15, some processes will show and some will not show on the tracked
                    # time slot, so it's better to set it null instead of 0 (default)
                    if flag == ".cpu_top15":
                        for vts in time_info.values():
                            linedic.update({vts: ' '})
                linedic.update({ts: cpu})
                cpu_dict.update({vkey: linedic})

    # save to csv
    fname = os.path.basename(file)
    o_csv = os.path.join(os.path.dirname(file), fname+'.csv')
    with open(o_csv, 'w', newline='') as f:
        # write head title
        flag = "CPU%"
        time_list.insert(0, flag)
        writer = csv.DictWriter(f, fieldnames=time_list)
        writer.writeheader()
        # write body
        wd = {}
        for key, value in cpu_dict.items():
            wd.update({'CPU%': key})
            wd.update(value)
            writer.writerow(wd)


def getcpulog(path, flag):
    f_list = os.listdir(path)
    for v in f_list:
        pp = os.path.join(path, v)
        if os.path.isdir(pp):
            getcpulog(pp, flag)
        else:
            if os.path.splitext(pp)[1] == flag:
                extract_cpulog(pp, flag)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Please input the output folder")
        exit(0)
    ret_dirs = [
        sys.argv[1],
    ]
    # search *.cpu_thrds
    for dir in ret_dirs:
        getcpulog(dir, ".cpu_thrds")
        getcpulog(dir, ".cpu_top15")

