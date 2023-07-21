# coding:utf-8

# @File: test.py
# @Author: 含光
# @description:
# @Time: 2022年07月19日
import os
import time
from PyQt5.QtWidgets import *
import sys
import hashlib
import base64
import uiautomator2 as u2


def click(num,x,y,time_1):

    for i in range(num):
        os.system("adb shell input tap " + x + " "+ y)
        time.sleep(time_1)
        print(f"第{i+1}次点击")


class GetMd5Content(object):

    def __init__(self):
        self.d = u2.connect()
        self.d.click()
        self.d().gestureM((100, 200))

    def get_md5(self, body):
        # md5
        get_md5_data = hashlib.md5()
        get_md5_data.update(body.encode("utf-8"))
        # base64
        base64_md5_data = str(base64.b64encode(get_md5_data.digest()), "utf-8")
        return base64_md5_data

class MainWindow(QMainWindow):

    def __init__(self):
        # 初始化 继承父类QMainWindow
        super(MainWindow, self).__init__()
        # 设置窗口大小
        self.resize(1050, 650)
        self.setWindowTitle("miniTools")

        # 定义按钮的frame框架
        self.frame = QFrame(self)
        self.frame.resize(200, 650)
        self.frame.move(0, 0)
        self.verticalLayout = QVBoxLayout(self.frame)

        # 定义btn1的frame业务框架
        self.frame_btn1 = QFrame(self)
        self.frame_btn1.resize(850, 650)
        self.frame_btn1.move(200, 0)
        self.frame_btn1_verticalLayout = QVBoxLayout(self.frame_btn1)

        # 定义btn2的frame业务框架
        self.frame_btn2 = QFrame(self)
        self.frame_btn2.resize(850, 650)
        self.frame_btn2.move(200, 0)
        self.frame_btn2_verticalLayout = QVBoxLayout(self.frame_btn2)

        # 默认仅展示按钮frame
        self.frame.setVisible(True)
        self.frame_btn1.setVisible(False)
        self.frame_btn2.setVisible(False)

        # btn1
        self.btn1 = QPushButton("md5加密", self)
        self.verticalLayout.addWidget(self.btn1)
        # btn2
        self.btn2 = QPushButton("btn2", self)
        self.verticalLayout.addWidget(self.btn2)

        # business1 btn1业务布局
        # label说明
        self.business1_label = QLabel(self)
        self.business1_label.setText("请输入需加密的文本")
        # 输入框
        self.business1_lineEdit = QLineEdit(self)
        # 点击按钮
        self.business1_btn = QPushButton("加密", self)
        # 控制台output
        self.business1_output = QTextBrowser(self)
        self.frame_btn1_verticalLayout.addWidget(self.business1_label)
        self.frame_btn1_verticalLayout.addWidget(self.business1_lineEdit)
        self.frame_btn1_verticalLayout.addWidget(self.business1_btn)
        self.frame_btn1_verticalLayout.addWidget(self.business1_output)

        # 给左侧按钮添加点击属性
        self.btn1.clicked.connect(self.frame_btn1_click)
        self.btn2.clicked.connect(self.frame_btn2_click)
        self.business1_btn.clicked.connect(self.business1_btn_click)

    def frame_btn1_click(self):
        self.frame_btn1.setVisible(True)
        self.frame_btn2.setVisible(False)

    def frame_btn2_click(self):
        self.frame_btn1.setVisible(False)
        self.frame_btn2.setVisible(True)

    def business1_btn_click(self):
        text = self.business1_lineEdit.text()
        try:
            result = GetMd5Content().get_md5(text)
            self.business1_output.setText("MD5: {}".format(result))
        except:
            self.business1_output.setText("加密失败！")

def count_data():
    path = r"E:\Python_Learning\2022-10-17 hprofconvert\hprofconvert\logs\HprofConvert_2022_12_09.log"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        content_list = content.split("hprof_convert：v1.1.0_20221020，开始恢复Hprof文件：")
        result_list = []
        for item in content_list[:-1]:
            # print(item)
            # break
            seconds = item.split("start 执行时间：")[1].split("\n")[0]
            count_times = item.split("2869358，切分")[-1].split("次后")[0]
            length = item.split("切分后每段长度：")[-1].split("\n")[0]
            result_list.append([count_times, length, seconds])
            # print(seconds)
            # print(count_times)
            # print(length)
        result_list.reverse()
        with open("result.txt", "w", encoding="utf-8") as f:
            for item in result_list:
                content = item[0] + "\t" + item[1] + "\t" + item[2] + "\n"
                f.write(content)
def count_name():
    path = r"E:\Python_Learning\ai_voice_assistant_new\script"
    kangkang_num = -1
    junxian_num = 0
    wangzhen_num = 0
    other_name = -2
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".py"):
                py_file = os.path.join(root, file)
                with open(py_file, "r", encoding="utf-8") as f:
                    contents = f.read()
                    if contents.find("含光") != -1:
                        junxian_num = junxian_num + 1
                    elif contents.find("kangkang.zheng") != -1:
                        kangkang_num = kangkang_num + 1
                    elif contents.find("zhen.wang") != -1:
                        wangzhen_num = wangzhen_num + 1
                    else:
                        other_name = other_name + 1

    print(f"康康脚本数量{kangkang_num}, 君先脚本数量{junxian_num}, 王振脚本数量{wangzhen_num}, 其他脚本数量{other_name}")

# 数一下软sar对应开发的脚本数量
def count_name_sar():
    path = r"E:\Python_Learning\2022-10-20sar\script"
    kaiyuan_num = -1
    junxian_num = 0
    other_name = 0
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".py"):
                py_file = os.path.join(root, file)
                with open(py_file, "r", encoding="utf-8") as f:
                    contents = f.read()
                    if contents.find("junxian.geng") != -1:
                        junxian_num = junxian_num + 1
                    elif contents.find("kaiyuan.xie") != -1:
                        kaiyuan_num = kaiyuan_num + 1
                    else:
                        other_name = other_name + 1
    print(f"凯园脚本数量{kaiyuan_num}, 君先脚本数量{junxian_num} 其他脚本数量{other_name}")


def bubblesort(arr):
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n-i-1):
                if arr[j] > arr[j+1]:
                    arr[j], arr[j+1] = arr[j+1], arr[j]
                swapped = True
        if not swapped:
            break
    return arr

















if __name__ == "__main__":
    # # 每一个pyqt程序中都需要有一个QApplication对象，sys.argv是一个命令行参数列表
    # app = QApplication(sys.argv)
    # # 实例化窗口
    # form = MainWindow()
    # # 窗口展示
    # form.show()
    # # 遇到退出情况，终止程序
    # sys.exit(app.exec_())
    # count_data()
    count_name_sar()
# if __name__ == '__main__':
#     time.sleep(20)
#     num = int(input("请输入点击次数:"))
#     x = input("请输入坐标x:")
#     y = input("请输入坐标y:")
#     time_1 = int(input("请输入点击间隔时间:"))
#     click(num, x, y, time_1)

