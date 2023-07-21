#!/bin/bash
# 获取当前连接的所有手机
devices=$(adb devices | awk 'NR>1 {print $1}')
# 遍历每个手机
for device in $devices; do
  # 使用adb shell命令查看是否存在monkey进程
  result=$(adb -s $device shell ps | grep monkey)
   # 将结果追加写入test.txt文件
  echo "$device:$result" >> test.txt
done