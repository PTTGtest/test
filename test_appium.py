# coding:utf-8
# @Time     : 2023年06月06日
# @Author   : junxian.geng
# @Email    : junxian.geng@transsion.com
# @description:

# 使用python+apppium实现手机UI界面自动化，主要操作是进入设置中连接wifi，并检查是否正常连接wifi
# 安装appium：pip install appium
# 安装appium-python-client：pip install appium-python-client

from appium import webdriver
from time import sleep


# server 后台进行
# 前置代码
desired_caps = {}
# 讓appium server啟動一個debug server
desired_caps['automationName'] = 'UiAutomator2'
# 讓appium server啟動一個debug server
desired_caps['platformName'] = 'Android'
# 讓appium server啟動一個debug server
desired_caps['platformVersion'] = '5.1'
# 讓appium server啟動一個debug server
desired_caps['deviceName'] = '00000000000000:5555'
# 讓appium server啟動一個debug server
desired_caps['appPackage'] = 'com.android.settings'
# 讓appium server啟動一個debug server
desired_caps['appActivity'] = '.Settings'
# 讓appium server啟動一個debug server
driver = webdriver.Remote('http://localhost:4723/wd/hub', desired_caps)
