#!/usr/bin/python3
# -*- coding: utf-8 -*-

f = open("db.txt", "r")
txt = ''
while True:
    line = f.readline().strip('\n')  # 按行读取且处理掉换行符，效果:"\'\n'变为了''
    if line:
        txt += line
    else:
        split = txt.strip().split('#end')
        print(split)
        for line in split:
            if line:
                print(line)
            else:
                print('空行')
        break
