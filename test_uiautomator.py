# coding:utf-8
# @Time     : 2023年06月06日
# @Author   : junxian.geng
# @Email    : junxian.geng@transsion.com
# @description:

# 使用python+uiautomator2实现手机UI界面自动化，主要操作是进入设置中连接wifi，并检查是否正常连接wifi
# 安装uiautomator2：pip install uiautomator2

import uiautomator2 as u2

d = u2.connect('0000000000000')
d.app_start('com.android.settings')
d(text='Wi-Fi').click()
d(resourceId='com.android.settings:id/switch_widget').click()
d(resourceId='com.android.settings:id/wifi_settings_button').click()
d(resourceId='com.android.settings:id/edit').set_text('test')
d(resourceId='com.android.settings:id/password').set_text('test')
d(resourceId='com.android.settings:id/action_bar_root').click()
d(resourceId='com.android.settings:id/next_button').click()

