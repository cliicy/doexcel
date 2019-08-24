import xlrd, xlsxwriter

# 设置要合并的所有文件
allxls = ["F:\\mongodb\\code_debug\\case3\\t6.xlsx", "F:\\mongodb\\code_debug\\case3\\t8.xlsx"]
# allxls = ["F:\\mongodb\\code_debug\\case3\\t6.xlsx"]
# 设置合并到的文件
endxls = "F:\\mongodb\\code_debug\\case3\\endxls.xlsx"

def crexcel():
    ff='F:\\mongodb\\code_debug\\case2\\hello_world.xlsx'
    with xlsxwriter.Workbook(ff) as workbook:
        worksheet = workbook.add_worksheet()
        worksheet.write('A1', 'Hello world')
    table = workbook.get_worksheet_by_name('Sheet1')
    print(table)

# 打开表格
def open_xls(file):
    try:
        fh = xlrd.open_workbook(file)
        return fh
    except Exception as e:
        print(str("打开出错，错误为：" + e))

# def open_xls(file):
#     # 打开excel文件
#     data = xlrd.open_workbook(file)
#     # 获取第一张工作表（通过索引的方式）
#     table = data.sheets()[0]
#     # data_list用来存放数据
#     data_list = []
#     # 将table中第一行的数据读取并添加到data_list中
#     data_list.extend(table.row_values(0))
#     # 打印出第一行的全部数据
#     for item in data_list:
#         print(item)

# 获取所有sheet
def getsheet(fh):
    return fh.sheets()

# 读取某个sheet的行数
def getnrows(fh, sheet):
    table = fh.sheets()[sheet]
    content = table.nrows
    return content



# 读取某个文件的内容并返回所有行的值
def getfilect(fh,fl, shnum):
    fh = open_xls(fl)
    table = fh.sheet_by_name(shname[shnum])
    num = getnrows(fh, shnum)
    lenrvalue = len(rvalue)
    for row in range(0, num):
        rdata = table.row_values(row)
        rvalue.append(rdata)
    print(rvalue[lenrvalue:])
    filevalue.append(rvalue[lenrvalue:])
    return filevalue


# 存储所有读取的结果
filevalue = []
# 存储一个标签的结果
svalue = []
# 存储一行结果
rvalue = []
# 存储各sheet名
# shname = []
shname=['SUM-intel-snappy-2048G-lf16KB','SUM-intel-snappy-600G-lf8K']
# 读取第一个待读文件，获得sheet数
crexcel()
fh = open_xls(allxls[0])
sh = getsheet(fh)
x = 0
for sheet in sh:
    shname.append(sheet.name)
    svalue.append([])
    x += 1
# 依次读取各sheet的内容
# 依次读取各文件当前sheet的内容
for shnum in range(0, 1):
    for fl in allxls:
        print("正在读取文件：" + str(fl) + "的第" + str(shnum) + "个标签的…")
        filevalue = getfilect(fh,fl, shnum)
    svalue[shnum].append(filevalue)
    # print(svalue[0])
    # print(svalue[1])
# 由于apped具有叠加关系，分析可得所有信息均在svalue[0][0]中存储
# svalue[0][0]元素数量为sheet标签数(sn)*文件数(fn)
sn = x
fn = len(allxls)
endvalue = []


# 设置一个函数专门获取svalue里面的数据，即获取各项标签的数据
def getsvalue(k):
    for z in range(k, k + fn):
        endvalue.append(svalue[0][0][z])
    return endvalue


# 打开最终写入的文件
wb1 = xlsxwriter.Workbook(endxls)
# 创建一个sheet工作对象
ws = wb1.add_worksheet()
polit = 0
linenum = 0
# 依次遍历每个sheet中的数据
for s in range(0, sn * fn, fn):
    thisvalue = getsvalue(s)
    tvalue = thisvalue[polit:]
    # 将一个标签的内容写入新文件中
    for a in range(0, len(tvalue)):
        for b in range(0, len(tvalue[a])):
            for c in range(0, len(tvalue[a][b])):
                # print(linenum)
                # print(c)
                data = tvalue[a][b][c]
                ws.write(linenum, c, data)
            linenum += 1
    # 叠加关系，需要设置分割点
    polit = len(thisvalue)
wb1.close()