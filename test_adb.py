# coding:utf-8
# @Time     : 2023年02月19日
# @Author   : junxian.geng
# @Email    : junxian.geng@transsion.com
# @description:
import datetime
import os
import sys
import time

from Logger import Logger


def test_adb():
    if getattr(sys, 'frozen', False):
        script_name = sys.executable
    else:
        script_name = __file__
    log_path = os.path.dirname(script_name) + os.sep + "logs.log"
    log_obj = Logger(log_path)
    while True:
        try:
            connect_file = os.popen('adb devices')
            time.sleep(2)
            list = connect_file.readlines()
            date_time = datetime.datetime.now()
            log_obj.info(f"当前时间：{date_time},打印内容如下")
            for line in list:
                log_obj.info(line)
            log_obj.info(f"当前时间：{date_time},打印结束")
            time.sleep(60)
        except Exception as e:
            log_obj.info(f"运行过程中出现异常：{str(e)}")

if __name__ == '__main__':
    # test_adb()
    serial_number = "085552522P028560"
    res = "music"
    apk = "com.zsorg.piyell.filemanager"
    apk_act = "com.zsorg.piyell.filemanager.activities.MainActivity"
    path = "\\\\10.150.98.90\\01_软件工程部\\软件测试部\\1.公共\\4.测试资源\\12.OTA Lab资源\\apk\\ACEVPN.apk"
    process_id = "18836"
    cmd = [adb, "-s", serial_number, "shell", "svc wifi enable"]
    print(cmd)
    rlt, encode_line_list = exec_cmd(cmd, 30)
    print(encode_line_list)

