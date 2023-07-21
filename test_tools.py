# coding:utf-8
# @Time     : 2023年06月05日
# @Author   : junxian.geng
# @Email    : junxian.geng@transsion.com
# @description:

# 写一段代码用于openpyxl多线程写入数据到本地表格，并添加线程锁和异常处理

import openpyxl
import threading
import time
import random
import os

# 创建一个线程锁
lock = threading.Lock()

# 创建一个表格
def read_txt():
    with open("result.txt", "r", encoding="utf-8") as f:
        for item in f:
            print(item.rstrip())

if __name__ == '__main__':
    read_txt()
