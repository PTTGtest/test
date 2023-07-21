# -*- coding: utf-8 -*-
# @Time     : 2023/2/9 17:37
# @Author   : yunqing.gui
# @Email    : yunqing.gui@transsion.com
# @File     : android_devices.py

import re
import random
import time
import traceback
from datetime import datetime

from modules.common.decorators import func_timer

from modules.common.global_attrs import *
from modules.common.exec_cmd import exec_cmd, execute_java_case
from modules.common.test_logger import logger
from modules.common.utils import get_Screen_on, pre_random, change_random, check_reboot_status, connect_u2, click_Tcard, \
    find_object_text_match, enter_local_update, \
    find_object_text_match_click, check_activity, get_devices_list, check_sys_boot_completed, enter_online_update, \
    click_Tcard_online, reboot_for_rollback, find_object_text_click, get_project_version, get_OS_version, \
    get_device_is_root, get_ip_address, check_device_status, connect_wifi_case, connect_google_case, u2_init, test_init, \
    set_screen_time

from modules.ota_steps.main_process.ota_config import ota_global_config
from modules.ota_steps.more_steps.erase_test import EraseTest
from modules.ota_steps.more_steps.ke_test import KETest
from modules.ota_steps.more_steps.more_tests import MoreTest
from modules.ota_steps.more_steps.reboot_test import RebootTest
from modules.ota_steps.steps_for_init.resource_operate import start_service_copydb


def get_battery_info(sn, adb_wifi=False):
    batteryLevel = -1
    batteryTemperature = -1
    ac_powered = None
    splitRe = re.compile(r"\s+")
    cmdline = [adb, "-s", sn, "shell", "dumpsys battery"]

    retry_count = 0
    while batteryLevel == -1 and retry_count<5:
        exec_successfully, exec_out = exec_cmd(cmdline)
        for line in exec_out:
            try:
                line = line.decode().strip()
                if "level" in line:
                    batteryLevel = int(re.split(splitRe, line)[1])
                if "temperature:" in line:
                    batteryTemperature = float(re.split(splitRe, line)[1]) / 10
                if "AC" in line:
                    if "true" in line:
                        ac_powered = True
                    elif "false" in line:
                        ac_powered = False
            except:
                pass
        if batteryLevel == -1:
            logger.debug("获取测试手机电量异常，等待10秒后重试！", tag=sn)
            if adb_wifi:
                logger.debug("adb wifi 连接手机，尝试重连", tag=sn)
                adb_wifi_disconnect(sn)
                time.sleep(1)
                adb_wifi_connect(sn)
            time.sleep(10)
            retry_count += 1
    return batteryLevel, batteryTemperature, ac_powered


def is_screen_on(sn):
    cmdline = [adb, "-s", sn, "shell", "dumpsys window policy | grep screenState"]
    try:
        rlt, encode_line_list = exec_cmd(cmdline)
        if "off" in encode_line_list[0].decode().lower():
            return False
        else:
            return True
    except:
        traceback.print_exc()
        return True


def press_power(sn):
    cmdline = [adb, "-s", sn, "shell", "input keyevent 26"]
    exec_cmd(cmdline)


def check_adb_devices(sn):
    status = None
    cmdline = [adb, "devices"]
    _, exec_out = exec_cmd(cmdline)
    for line in exec_out:
        line = line.decode().strip()
        if line.startswith(sn):
            try:
                status = line.split()[1].strip()
            except:
                pass
            if status == "device":
                return True, status
            else:
                return False, status
    return False, status


def check_file_exits(sn, file, path):
    """
    检查手机中是否有指定文件
    :return:
    """
    cmd = [adb,"-s", sn, "shell", "ls", path]
    rlt, content = exec_cmd(cmd)
    for item in content:
        if file in item.decode().strip():
            return True
    else:
        return False


def push_local_tcard(sn, file, package_path, sdcard_path):
    """
    检查手机中是否有升级包，若无升级包，导入本地升级包
    :return:
    """
    if not check_file_exits(sn, file, sdcard_path):
        logger.info(f"本地未找到升级包【{file}】,尝试重新导入", sn=sn)
        adb_push(sn, package_path, sdcard_path)
    else:
        logger.info(f"本地找到升级包【{file}】,不需要重新导入", sn=sn)

def reset_online_tcard(sn):
    """
    连接网络、谷歌版本升级等
    :return:
    """
    if ota_global_config.connect_wifi:
        logger.info("执行连接wifi操作", sn=sn)
        connect_wifi_case(sn, ota_global_config.ssid, ota_global_config.ssid_password)
    else:
        logger.info("不执行连接wifi操作", sn=sn)
        # mainline 升级
    if ota_global_config.do_mainline_update:
        logger.info("执行mainline升级操作", sn=sn)
        connect_google_case(sn, ota_global_config.account, ota_global_config.google_password, ota_global_config.settings)
    else:
        logger.info("不执行mainline升级操作", sn=sn)


def get_wifi_ip(sn):
    pattern_ip = re.compile("inet\s+(\d+\.\d+\.\d+\.\d+)/")
    cmdline = [adb, "-s", sn, "shell", "ip addr show wlan0"]
    logger.info(f"开始执行命令：{cmdline}", tag=sn)
    _, exec_out = exec_cmd(cmdline)
    for line in exec_out:
        line = line.decode().strip()
        regex_rlt = re.match(pattern_ip, line)
        if regex_rlt:
            return regex_rlt.group(1)
    return None


def adb_tcpip(sn, wifi_port):
    cmdline = [adb, "-s", sn, "tcpip", f"{wifi_port}"]
    logger.info(f"开始执行命令：{cmdline}", tag=sn)
    _, exec_out = exec_cmd(cmdline)
    for line in exec_out:
        line = line.decode().strip()
        logger.info(line, tag=sn)


def adb_wifi_connect(adb_wifi_port, sn=None):
    cmdline = [adb, "connect", adb_wifi_port]
    logger.info(f"开始执行命令：{cmdline}", tag=sn)
    exec_cmd(cmdline)
    _, exec_out = exec_cmd(cmdline)
    for line in exec_out:
        line = line.decode().strip()
        logger.info(line, tag=sn)


def adb_wifi_disconnect(adb_wifi_port, sn=None):
    cmdline = [adb, "disconnect", adb_wifi_port]
    logger.debug(f"开始执行命令：{cmdline}", tag=sn)
    exec_cmd(cmdline)
    _, exec_out = exec_cmd(cmdline)


def is_mtk(sn):
    cmdline = [adb, "-s", sn, "shell", "getprop ro.hardware"]
    logger.info(f"开始执行命令：{cmdline}", tag=sn)
    exec_cmd(cmdline)
    _, exec_out = exec_cmd(cmdline)
    for line in exec_out:
        line = line.decode().strip()
        logger.info(f"判断mtk输出内容：{line}", tag=sn)
        if line.startswith("mt"):
            logger.info(f"当前手机芯片为：{line}", tag=sn)
            return True
    return False


def pull_logs(sn, local_log_dir, wait_time=0):
    try:
        os.makedirs(local_log_dir, exist_ok=True)
    except:
        traceback.print_exc()

    if wait_time > 0:
        logger.info(f"wait_time>0, 等待 {wait_time} 后执行日志拉取.", tag=sn)
        time.sleep(wait_time)

    if is_mtk(sn):
        cmdline = [adb, "-s", sn, "pull", "/data/debuglogger/mobilelog", local_log_dir]
    else:
        cmdline = [adb, "-s", sn, "pull", "/data/ylog", local_log_dir]
    logger.info(f"开始执行命令：{cmdline}", tag=sn)
    _, exec_out = exec_cmd(cmdline, timeout=15*60)


def do_screencap(sn, png_in_device, png_local):
    cmdline = [adb, "-s", sn, "shell", f"screencap {png_in_device}"]
    exec_cmd(cmdline)
    time.sleep(1)
    cmdline = [adb, "-s", sn, "pull", png_in_device, png_local]
    exec_cmd(cmdline, timeout=60)


def reset_mtk_log(sn):
    cmdline = [adb, "-s", sn, "shell", "am broadcast -a com.debug.loggerui.ADB_CMD -e cmd_name stop --ei cmd_target 127 --receiver-foreground --receiver-include-background"]
    exec_cmd(cmdline)
    time.sleep(1)
    cmdline = [adb, "-s", sn, "shell", "rm -rf /sdcard/debuglogger/*"]
    exec_cmd(cmdline)
    time.sleep(1)
    cmdline = [adb, "-s", sn, "shell", "am broadcast -a com.debug.loggerui.ADB_CMD -e cmd_name start --ei cmd_target 1 --receiver-foreground --receiver-include-background"]
    exec_cmd(cmdline)
    time.sleep(1)


def get_connected_device():
    """
    通过命令：adb devices，获取连接的手机列表
    :return:
    """
    regex_device_line = re.compile(r"([A-Za-z0-9]+)\s+([A-Za-z]+)")

    device_status_dict = {}
    cmdline = [adb, "devices"]
    exec_successfully, exec_out = exec_cmd(cmdline)
    if exec_successfully:
        for line in exec_out:
            try:
                line = line.decode().strip()
                # 过滤掉adb信息
                if line.startswith("* daemon") or line.startswith("List of devices attached"):
                    continue

                # 匹配手机状态
                regex_rlt = re.match(regex_device_line, line)
                if regex_rlt:
                    sn = regex_rlt.group(1)
                    sn_status = regex_rlt.group(2)

                    # 检查是否存在SN重复的手机
                    if sn in device_status_dict:
                        device_status_dict[sn] = DEVICE_STATUS_DUPLICATED
                    else:
                        if sn_status == "device":
                            device_status_dict[sn] = DEVICE_STATUS_ONLINE
                        elif sn_status == "offline":
                            device_status_dict[sn] = DEVICE_STATUS_OFFLINE
                        elif sn_status == "recovery":
                            device_status_dict[sn] = DEVICE_STATUS_RECOVERY
                        elif sn_status == "unauthorized":
                            device_status_dict[sn] = DEVICE_STATUS_UNAUTHORIZED
                        else:
                            device_status_dict[sn] = DEVICE_STATUS_OTHER
            except:
                logger.warn("获取手机状态时发生异常：\n{}".format(traceback.format_exc()))

    return device_status_dict


def adb_push(sn, local_path, device_path):
    cmdline = [adb, "-s", sn, "push", local_path, device_path]
    logger.info(f"执行推送文件：{local_path} 到手机内路径：{device_path}，执行命令：{cmdline}", sn=sn)
    exec_cmd(cmdline, timeout=60*60)


def adb_pull(sn, device_path, local_path):
    cmdline = [adb, "-s", sn, "pull", device_path, local_path]
    logger.info(f"执行导出，手机内路径：{device_path} 到：{local_path}，执行命令：{cmdline}", sn=sn)
    exec_cmd(cmdline, timeout=60*60)


@func_timer
def export_logs(sn, mtk_tag, local_path):
    dbf_file_count = -1

    if mtk_tag == "mtk":
        if get_OS_version(sn) >=12 and not get_device_is_root(sn):
            logger.info("非root版本，Android S+，修正手机内aee目录为/sdcard/transsion_log", sn=sn)
            tool_path = os.path.join(PathManager.tool_folder, "repair")
            rlt, error_msg = start_service_copydb(sn, tool_path)
            if rlt:
                logger.info("手机内部日志复制完成，重组导出内容", sn=sn)
            else:
                logger.info("手机内部日志复制异常：{}".format(error_msg), sn=sn)
            adb_pull(sn, "/sdcard/transsion_log/data/aee_exp", local_path)
            adb_pull(sn, "/sdcard/transsion_log/data/vendor", local_path)
        else:
            adb_pull(sn, "/data/aee_exp", local_path)
            cmd = [adb, "-s", sn, "shell", "cp -R /data/vendor/aee_exp/  /sdcard/data_vendor_aee_exp/"]
            exec_cmd(cmd)
            cmd = [adb, "-s", sn, "shell", "cp -R /data/vendor/mtklog/aee_exp/  /sdcard/data_vendor_aee_exp/"]
            exec_cmd(cmd)
            adb_pull(sn, "/sdcard/data_vendor_aee_exp", local_path)
            cmd = [adb, "-s", sn, "shell", "rm -rf /sdcard/data_vendor_aee_exp"]
            exec_cmd(cmd)
        adb_pull(sn, "/data/debuglogger", local_path)
        adb_pull(sn, "/sdcard/Auto/testlog.txt", local_path)
        adb_pull(sn, "/sdcard/screencap", local_path)
        reset_mtk_log_by_device(sn)

        # 遍历 local_path 目录，查找是否存在 dbg 文件，并将文件全路径存入一个list中
        dbg_files = []
        for root, dirs, files in os.walk(local_path):
            for file in files:
                if file.endswith(".dbg"):
                    dbg_files.append(os.path.join(root, file))
        dbf_file_count = len(dbg_files)
        logger.info(f"找到 {dbf_file_count} 个dbg文件", sn=sn)
    else:
        adb_pull(sn, "/sdcard/ylog", local_path)
        adb_pull(sn, "/data/ylog", local_path)
        adb_pull(sn, "/data/corefile", local_path)
        adb_pull(sn, "/sdcard/minidump", local_path)
        adb_pull(sn, "/sdcard/Auto/testlog.txt", local_path)
        adb_pull(sn, "/sdcard/screencap", local_path)
        reset_sprd_log_by_device(sn)

    return dbf_file_count


def reset_mtk_log_by_device(sn):
    logger.info("开始重置手机MTK Log", sn=sn)

    # 关闭所有mtklog
    cmdline = [adb, "-s", sn, "shell", "am broadcast -a com.debug.loggerui.ADB_CMD -e cmd_name stop --ei cmd_target 127 --receiver-foreground  --receiver-include-background"]
    logger.info(f"关闭所有MTK Log，执行命令：{cmdline}", sn=sn)
    exec_cmd(cmdline)

    # 等待5秒左右
    logger.info("等待5秒", sn=sn)
    time.sleep(5)

    # 删除debuglogger和db文件
    cmdline = [adb, "-s", sn, "shell", "rm -rf /data/debuglogger/*"]
    exec_cmd(cmdline)
    cmdline = [adb, "-s", sn, "shell", "rm -rf /data/aee_exp/*"]
    exec_cmd(cmdline)
    cmdline = [adb, "-s", sn, "shell", "rm -rf /data/vendor/aee_exp/*"]
    exec_cmd(cmdline)
    cmdline = [adb, "-s", sn, "shell", "rm -rf /data/vendor/mtklog/aee_exp/*"]
    exec_cmd(cmdline)

    cmdline = [adb, "-s", sn, "shell", "am broadcast -a com.debug.loggerui.ADB_CMD -e cmd_name start --ei cmd_target 127 --receiver-foreground  --receiver-include-background"]
    logger.info(f"启动指定MTK Log，执行命令：{cmdline}", sn=sn)
    exec_cmd(cmdline)

    # 等待30秒左右
    logger.info("等待30秒", sn=sn)
    time.sleep(30)
    logger.info("重置MTK Log 完成", sn=sn)


def reset_sprd_log_by_device(sn):

    logger.info("开始重置手机sprd Log", sn=sn)

    # 展讯安卓T关闭所有log
    cmdline = [adb, "-s", sn, "shell", "am broadcast -a  transsion.action.ControlDumpCorefile -n com.sprd.logmanager/.LogManagerReceiver --es  from adb  -ei magic 902 --ei fulldump 0 --ei corefile 0 -f 0x01000000 -p  com.sprd.logmanager"]
    logger.info(f"关闭所有sprd Log，执行命令：{cmdline}", sn=sn)
    exec_cmd(cmdline)

    cmdline = [adb, "-s", sn, "shell", "am startservice -n com.reallytek.wg/com.reallytek.wg.utils.LogControlService -e from adb -p com.reallytek.wg  --ei magic 902 -e android 0 -e kernel 0 -e uboot 0 -e lastkmsg 0 -e thermal 0 -e bthci 0 -e apcap 0"]
    logger.info(f"关闭所有sprd Log，执行命令：{cmdline}", sn=sn)
    exec_cmd(cmdline)

    # 展讯安卓S及以下关闭所有log
    cmdline = [adb, "-s", sn, "shell", "ylogctl disable"]
    logger.info(f"关闭所有sprd Log，执行命令：{cmdline}", sn=sn)
    exec_cmd(cmdline)

    cmdline = [adb, "-s", sn, "shell", "persist.sys.ylog.enabled 0"]
    logger.info(f"关闭所有sprd Log，执行命令：{cmdline}", sn=sn)
    exec_cmd(cmdline)

    cmdline = [adb, "-s", sn, "shell", "setprop debug.sysdump.enabled false"]
    logger.info(f"关闭所有sprd Log，执行命令：{cmdline}", sn=sn)
    exec_cmd(cmdline)

    cmdline = [adb, "-s", sn, "shell", "setprop debug.corefile.enabled false"]
    logger.info(f"关闭所有sprd Log，执行命令：{cmdline}", sn=sn)
    exec_cmd(cmdline)

    cmdline = [adb, "-s", sn, "shell", "echo 'off' > /proc/sprd_sysdump"]
    logger.info(f"关闭所有sprd Log，执行命令：{cmdline}", sn=sn)
    exec_cmd(cmdline)

    # 等待5秒左右
    logger.info("等待5秒", sn=sn)
    time.sleep(5)

    # 删除ylog文件
    cmdline = [adb, "-s", sn, "shell", "rm -rf /data/ylog/*"]
    exec_cmd(cmdline)
    cmdline = [adb, "-s", sn, "shell", "rm -rf /sdcard/ylog/*"]
    exec_cmd(cmdline)
    cmdline = [adb, "-s", sn, "shell", "rm -rf /data/corefile/*"]
    exec_cmd(cmdline)
    cmdline = [adb, "-s", sn, "shell", "rm -rf /sdcard/minidump/*"]
    exec_cmd(cmdline)

    # 安卓T开启dump和日志
    cmdline = [adb, "-s", sn, "shell", "am broadcast -a  transsion.action.ControlDumpCorefile -n com.sprd.logmanager/.LogManagerReceiver --es  from adb  -ei magic 902 --ei fulldump 1 --ei corefile 1 -f 0x01000000 -p  com.sprd.logmanager"]
    logger.info(f"开启dump，执行命令：{cmdline}", sn=sn)
    exec_cmd(cmdline)
    time.sleep(2)

    cmdline = [adb, "-s", sn, "shell", "am startservice -n com.reallytek.wg/com.reallytek.wg.utils.LogControlService -e from adb -p com.reallytek.wg  --ei magic 902 -e android 1 -e kernel 1 -e uboot 1 -e lastkmsg 1 -e thermal 1 -e bthci 1 -e apcap 1"]
    logger.info(f"启动指定sprd Log，执行命令：{cmdline}", sn=sn)
    exec_cmd(cmdline)
    time.sleep(2)

    # 安卓展讯安卓S及以下开启所有日志
    cmdline = [adb, "-s", sn, "shell", "ylogctl resetsettings"]
    logger.info(f"启动指定sprd Log，执行命令：{cmdline}", sn=sn)
    exec_cmd(cmdline)
    time.sleep(2)
    cmdline = [adb, "-s", sn, "shell", "ylogctl enable"]
    logger.info(f"启动指定sprd Log，执行命令：{cmdline}", sn=sn)
    exec_cmd(cmdline)
    time.sleep(2)
    cmdline = [adb, "-s", sn, "shell", "ylogctl op android"]
    logger.info(f"启动指定sprd Log，执行命令：{cmdline}", sn=sn)
    exec_cmd(cmdline)
    time.sleep(2)
    cmdline = [adb, "-s", sn, "shell", "ylogctl op kernel"]
    logger.info(f"启动指定sprd Log，执行命令：{cmdline}", sn=sn)
    exec_cmd(cmdline)
    time.sleep(2)
    cmdline = [adb, "-s", sn, "shell", "ylogctl op uboot"]
    logger.info(f"启动指定sprd Log，执行命令：{cmdline}", sn=sn)
    exec_cmd(cmdline)
    time.sleep(2)
    cmdline = [adb, "-s", sn, "shell", "setprop debug.corefile.enabled true"]
    logger.info(f"启动指定sprd Log，执行命令：{cmdline}", sn=sn)
    exec_cmd(cmdline)
    time.sleep(2)
    cmdline = [adb, "-s", sn, "shell", "setprop debug.sysdump.enabled true"]
    logger.info(f"启动指定sprd Log，执行命令：{cmdline}", sn=sn)
    exec_cmd(cmdline)

    # 等待30秒左右
    logger.info("等待30秒", sn=sn)
    time.sleep(30)
    logger.info("重置sprd Log 完成", sn=sn)


def do_device_update(sn, scatter_file_path):
    device_update_exe = PathManager.device_update
    device_update_folder = PathManager.device_update_folder
    cmdline = [device_update_exe, "-s", sn, "-p", scatter_file_path]
    logger.info(f"开始调用device_update 执行刷机，调用命令：{cmdline}", sn=sn)
    exec_successfully, exec_out = exec_cmd(cmdline, timeout=60*60, cwd=device_update_folder)
    for line in exec_out:
        try:
            line = line.decode().strip()
            logger.debug(line, sn=sn)
            if "deviceUpdate successfully" in line:
                return True
        except:
            pass

    return False


def process_device_update(sn, scatter_file_path, target_build):
    ip = get_ip_address()
    fail_time = PathManager.current_time_stamp
    fail_file_name = f"{ip}_{sn}_刷机失败.txt"
    fail_file = os.path.join(PathManager.flash_error_folder, fail_file_name)
    with open(fail_file, 'a', encoding="utf-8") as f:
        f.write(f"设备{sn}刷机失败， 失败时间：{fail_time}\n")
    logger.info("等待5分钟等待设备恢复", sn=sn)
    if check_device_status(sn):
        build_after_update = get_project_version(sn)
        if target_build == build_after_update:
            logger.info(f"当前版本为指定版本：{target_build},不再重试", sn=sn)
            os.remove(fail_file)
            return True
        else:
            device_update_rlt = do_device_update(sn, scatter_file_path)
    else:
        device_update_rlt = do_device_update(sn, scatter_file_path)
    if device_update_rlt:
        logger.info(f"刷机成功, 不再重试", sn=sn)
        os.remove(fail_file)
        return True
    else:
        return False


def wait_for_device(serial_number, device_times=3000, boot_times=200):
    k = 0
    logger.info("等待手动刷机后重连设备", sn=serial_number)
    while True:
        device_list = get_devices_list()
        if serial_number in device_list:
            logger.info(f"发现设备：{serial_number}")
            break
        if k > device_times:
            logger.error(f"超过等待次数，未发现设备：{serial_number}")
            return False
        if k % 60 == 0:
            logger.info(f"第{str(k/60+1)}min等待设备", sn=serial_number)
            k = k + 1
        else:
            time.sleep(1)
            k = k + 1
    k = 0
    logger.info("等待boot animation结束")
    while True:
        if check_sys_boot_completed(serial_number):
            logger.info("System reboot completed")
            break
        if k > boot_times:
            logger.error("超过等待时间，设备boot失败")
            return False
        else:
            time.sleep(5)
            k = k + 1
    time.sleep(5)
    cmdline = [adb, "-s", serial_number, "shell", "input keyevent 82"]
    exec_cmd(cmdline)
    cmdline = [adb, "-s", serial_number, "shell", "input keyevent 82"]
    exec_cmd(cmdline)


def click_local_tcard(sn, tcard_name):
    """
    点击本地升级包
    :param sn:手机sn号
    :param tcard_name:tcard包名称
    :return:
    """
    get_Screen_on(sn, ota_global_config.settings)
    for i in range(1, 4):
        logger.info(f"设备{sn}第{i}次搜索升级包：{tcard_name}", sn=sn)
        cmdInstall = [adb, "-s", sn, "shell",
                      f"am instrument -w -m    -e debug false -e tcardName {tcard_name} -e class 'com.transsion.testcaserepository.ota.TestLocalUpdateOta#testLocalUpdate' com.transsion.otastep.test/androidx.test.runner.AndroidJUnitRunner"]
        if execute_java_case(cmdInstall):
            logger.info(f"设备{sn}第{i}次搜索升级包成功", sn=sn)
            return True
        logger.info("等待3min",sn=sn)
        time.sleep(180)
    else:
        logger.info(f"设备{sn}连续3次搜索升级包失败", sn=sn)
        info = "搜素升级包失败" + datetime.strftime(datetime.now(), "_%Y%m%d_%H%M%S")
        screencap(sn, info)
        return False


def click_online_tcard(sn, ssid, password):
    """
    点击在线升级包
    :param sn: 手机sn号
    :param ssid: wifi账号
    :param password: wifi密码
    :return:
    """
    get_Screen_on(sn, ota_global_config.settings)
    for i in range(1, 3):
        logger.info(f"设备{sn}第{i}次搜索在线升级包", sn=sn)
        cmdInstall = [adb, "-s", sn, "shell",
                      f"am instrument -w -m    -e debug false -e wifiName '{ssid}' -e wifiPassword {password} -e class 'com.transsion.testcaserepository.ota.TestImportOnlineUpdateResumeOta#testImportOnlineUpdateResume' com.transsion.otastep.test/androidx.test.runner.AndroidJUnitRunner"]
        if execute_java_case(cmdInstall):
            logger.info(f"设备{sn}第{i}次搜索在线升级包成功", sn=sn)
            return True
        logger.info("等待3min",sn=sn)
        time.sleep(180)
    else:
        logger.info(f"设备{sn}连续2次搜索在线升级包失败", sn=sn)
        info = "搜素在线升级包失败" + datetime.strftime(datetime.now(), "_%Y%m%d_%H%M%S")
        screencap(sn, info)
        return False


def do_ota_update_local(sn, package_path, target_build, debug_mode, log_path, mode=""):
    """
    本地升级主流程，含回滚、重启、恢厂测试操作
    :param sn: 手机sn号
    :param tcard_name: 升级包
    :param target_build: 目标版本
    :param debug_mode: 调试模式
    :param mode: 升级模式
    :return:
    """
    cmd = [adb, "-s", sn, "shell", "appops set --uid com.transsion.otastep MANAGE_EXTERNAL_STORAGE allow"]
    exec_cmd(cmd)
    time.sleep(2)
    earse_result_list = []
    ke_result_list = []
    reboot_result_list = []

    tcard_name = os.path.basename(package_path)
    logger.info(f"设备{sn}执行OTA本地{mode}OTA升级主流程", sn=sn)
    if debug_mode:
        time.sleep(2)
        return True, f"本地{mode}OTA升级成功"

    if ota_global_config.reboot and (mode or (not mode and not ota_global_config.rollback_test)):
        logger.info(f"设备{sn}执行本地{mode}OTA升级流程中重启测试", sn=sn)
        reboot_list = [int(i) for i in ota_global_config.reboot_progress]
        reboot_list = sorted(reboot_list)  # ota升级，重启后第二次点击install会继续上次进度升级，这里从小到大排个序
        logger.info(f"设备{sn}本地{mode}OTA升级重启进度列表：{reboot_list}", sn=sn)
        roboot_num = 0
        reboot_result_list = []
        for progress in reboot_list:
            check_reboot_status(sn, setting=ota_global_config.settings)
            time.sleep(20)
            build_after_update = get_project_version(sn)
            if target_build == build_after_update:
                return True, f"重启后手机版本为目标版本，结束本地{mode}OTA升级流程，重启次数{roboot_num}"
            roboot_num = roboot_num + 1
            logger.info(f"设备{sn}本地{mode}OTA升级到【{progress}%】后进行重启", sn=sn)
            push_local_tcard(sn, tcard_name, package_path, ota_global_config.sdcard_path)
            if click_local_tcard(sn, tcard_name):
                logger.info(f"设备{sn}本地{mode}OTA升级，点击install成功, 成功进入升级流程", sn=sn)
                cmdProgress = [adb, "-s", sn, "shell",
                               "am instrument -w -m -e debug false -e updateprogress " + str(
                                   progress) + " -e class 'com.transsion.testcaserepository.ota.TestLocalUpdateOtaRebootPercent#testLocalUpdateOTARebootPercent' com.transsion.otastep.test/androidx.test.runner.AndroidJUnitRunner"]
                if execute_java_case(cmdProgress, ota_global_config.ota_update_time*60):
                    logger.info(f"设备{sn}在本地{mode}OTA升级进度为{progress}%时，进行重启成功", sn=sn)
                    time.sleep(20)  # 睡眠20秒，因手机重启后会短暂几秒内可以查找到设备，防止下一轮找到设备后直接开始
                else:
                    detail = f"设备{sn}在本地{mode}OTA升级进度为{progress}%时，进行重启失败"
                    logger.info(f"设备{sn}在本地{mode}OTA升级进度为{progress}%时，进行重启失败", sn=sn)
                    reboot_result_list.append(detail)
                    screencap(sn, f"进度为{progress}%时，进行重启失败" + datetime.strftime(datetime.now(), "_%Y%m%d_%H%M%S"))
                    continue
            else:
                detail = f"本地{mode}OTA升级进度{progress}%，点击install失败"
                logger.info(detail, sn=sn)
                reboot_result_list.append(detail)
                screencap(sn, f"进度{progress}%，点击install失败" + datetime.strftime(datetime.now(), "_%Y%m%d_%H%M%S"))
                continue
    if ota_global_config.erase_test:
        logger.info(f"设备{sn}执行本地{mode}OTA升级流程中恢复出厂设置测试", sn=sn)
        erase_list = [int(i) for i in ota_global_config.erase_progress]
        erase_list = sorted(erase_list)
        logger.info(f"设备{sn}本地{mode}OTA升级恢复出厂设置进度列表：{erase_list}", sn=sn)
        earse_num = 0
        earse_result_list = []
        for progress in erase_list:
            check_reboot_status(sn, setting=ota_global_config.settings)
            time.sleep(20)
            set_screen_time(sn)
            build_after_update = get_project_version(sn)
            if target_build == build_after_update:
                return True, f"重启后手机版本为目标版本，结束本地{mode}OTA升级流程，恢复出厂设置次数{earse_num}"
            earse_num = earse_num + 1
            path = os.path.join(log_path, str(earse_num))
            os.makedirs(path, exist_ok=True)
            export_logs(sn, ota_global_config.mtk_or_sprd, path)
            logger.info(f"设备{sn}本地{mode}OTA升级到【{progress}%】后进行恢复出厂设置", sn=sn)
            test_init(sn, ota_global_config.config_tag, ota_global_config.resource_dir)
            push_local_tcard(sn, tcard_name, package_path, ota_global_config.sdcard_path)
            if click_local_tcard(sn, tcard_name):
                logger.info(f"设备{sn}本地{mode}OTA升级，点击install成功, 成功进入升级流程", sn=sn)
                cmdProgress = [adb, "-s", sn, "shell",
                               "am instrument -w -m -e debug false -e updateprogress " + str(
                                   progress) + " -e screenPassword 123456 -e class 'com.transsion.testcaserepository.ota.TestLocalUpdateOtaResetPercent#testLocalUpdateOTAResetPercent' com.transsion.otastep.test/androidx.test.runner.AndroidJUnitRunner"]
                if execute_java_case(cmdProgress, ota_global_config.ota_update_time * 60):
                    logger.info(f"设备{sn}在本地{mode}OTA升级进度为{progress}%时，进行恢复出厂设置成功", sn=sn)
                    time.sleep(20)  # 睡眠20秒，因手机重启后会短暂几秒内可以查找到设备，防止下一轮找到设备后直接开始
                else:
                    detail = f"设备{sn}在本地{mode}OTA升级进度为{progress}%时，进行恢复出厂设置失败"
                    logger.info(f"设备{sn}在本地{mode}OTA升级进度为{progress}%时，进行恢复出厂设置失败", sn=sn)
                    cmd = [adb, "-s", sn, "reboot"]
                    exec_cmd(cmd)
                    check_reboot_status(sn, setting=ota_global_config.settings)
                    earse_result_list.append(detail)
                    screencap(sn, f"进度为{progress}%时，进行恢厂失败" + datetime.strftime(datetime.now(), "_%Y%m%d_%H%M%S"))
                    continue
            else:
                detail = f"本地{mode}OTA升级进度{progress}%，点击install恢厂失败"
                logger.info(detail, sn=sn)
                earse_result_list.append(detail)
                screencap(sn, f"进度{progress}%，点击install恢厂失败" + datetime.strftime(datetime.now(), "_%Y%m%d_%H%M%S"))
                continue
        if ota_global_config.mtk_or_sprd == "mtk":
            reset_mtk_log_by_device(sn)
        else:
            reset_sprd_log_by_device(sn)
    check_reboot_status(sn, setting=ota_global_config.settings)
    if ota_global_config.ke_test:
        logger.info(f"设备{sn}执行本地{mode}OTA升级流程中KE打断", sn=sn)
        ke_list = [int(i) for i in ota_global_config.ke_progress]
        ke_list = sorted(ke_list)
        logger.info(f"设备{sn}本地{mode}OTA升级KE打断进度列表：{ke_list}", sn=sn)
        ke_num = 0
        ke_result_list = []
        for progress in ke_list:
            check_reboot_status(sn, setting=ota_global_config.settings)
            time.sleep(20)
            build_after_update = get_project_version(sn)
            if target_build == build_after_update:
                return True, f"重启后手机版本为目标版本，结束本地{mode}OTA升级流程，KE打断次数{ke_num}"
            ke_num = ke_num + 1
            logger.info(f"设备{sn}本地{mode}OTA升级到【{progress}%】后进行KE打断", sn=sn)
            push_local_tcard(sn, tcard_name, package_path, ota_global_config.sdcard_path)
            if click_online_tcard(sn, ota_global_config.ssid, ota_global_config.ssid_password):
                logger.info(f"设备{sn}本地{mode}OTA升级, 成功进入升级流程", sn=sn)
                cmdProgress = [adb, "-s", sn, "shell",
                               "am instrument -w -m -e debug false -e updateprogress " + str(
                                   progress) + " -e screenPassword 123456 -e class 'com.transsion.testcaserepository.ota.TestLocalUpdateOtaKePercent#testLocalUpdateOtaKePercent' com.transsion.otastep.test/androidx.test.runner.AndroidJUnitRunner"]
                if execute_java_case(cmdProgress, ota_global_config.ota_update_time * 60):
                    logger.info(f"设备{sn}本地{mode}OTA升级进度为{progress}分钟时，进行KE打断", sn=sn)
                    ke = KETest(sn)
                    ke.ke_test()
                else:
                    detail = f"设备{sn}在本地{mode}OTA升级进度为{progress}分钟时，进行KE打断失败"
                    logger.info(f"设备{sn}在本地{mode}OTA升级进度为{progress}分钟时，进行KE打断失败", sn=sn)
                    cmd = [adb, "-s", sn, "reboot"]
                    exec_cmd(cmd)
                    check_reboot_status(sn, setting=ota_global_config.settings)
                    ke_result_list.append(detail)
                    screencap(sn, f"进度为{progress}分钟时，进行KE打断失败" + datetime.strftime(datetime.now(), "_%Y%m%d_%H%M%S"))
                    continue
            else:
                detail = f"本地{mode}OTA升级进度{progress}分钟，进入升级流程时KE打断"
                logger.info(detail, sn=sn)
                ke_result_list.append(detail)
                screencap(sn, f"进度{progress}分钟，进入升级流程时KE打断失败" + datetime.strftime(datetime.now(), "_%Y%m%d_%H%M%S"))
                continue
    check_reboot_status(sn, setting=ota_global_config.settings)
    logger.info(f"设备{sn}执行本地{mode}OTA升级流程，进行正常OTA升级", sn=sn)
    push_local_tcard(sn, tcard_name, package_path, ota_global_config.sdcard_path)
    if click_local_tcard(sn, tcard_name) or get_ota_satate(sn):
        logger.info(f"设备{sn}本地{mode}OTA升级，点击install成功, 成功进入升级流程", sn=sn)
        cmdReboot = [adb, "-s", sn, "shell",
                     f"am instrument -w -m    -e debug false -e otaUpdateTime {str(ota_global_config.ota_update_time)} -e class 'com.transsion.testcaserepository.ota.TestLocalUpdateOtaReboot#testLocalUpdate' com.transsion.otastep.test/androidx.test.runner.AndroidJUnitRunner"]
        if execute_java_case(cmdReboot, ota_global_config.ota_update_time*60):
            logger.info(f"本地{mode}OTA升级完成,点击reboot成功", sn=sn)
            cmd =[adb, "-s", sn, "reboot"]
            logger.info(f"本地{mode}OTA升级完成,直接重启", sn=sn)
            exec_cmd(cmd)
            time.sleep(5)
        else:
            if not ota_global_config.rollback_test:
                logger.info(f"本地{mode}OTA升级执行用例失败,直接重启", sn=sn)
                cmd =[adb, "-s", sn, "reboot"]
                exec_cmd(cmd)
                time.sleep(5)
                check_reboot_status(sn, setting=ota_global_config.settings)
                build_after_update = get_project_version(sn)
                if target_build == build_after_update:
                    logger.info(f"本地{mode}OTA升级完成,直接重启", sn=sn)
                    exec_cmd(cmd)
                    time.sleep(5)
                else:
                    detail = f"升级用例执行失败，本地{mode}OTA升级失败"
                    logger.info(detail, sn=sn)
                    screencap(sn, detail + datetime.strftime(datetime.now(), "_%Y%m%d_%H%M%S"))
                    return False, detail + "\n" + str(earse_result_list) + "\n" + str(ke_result_list) + "\n" + str(reboot_result_list)
            else:
                detail = f"升级用例执行失败，本地{mode}OTA升级失败"
                logger.info(detail, sn=sn)
                screencap(sn, detail + datetime.strftime(datetime.now(), "_%Y%m%d_%H%M%S"))
                return False, detail + "\n" + str(earse_result_list) + "\n" + str(ke_result_list) + "\n" + str(reboot_result_list)
    else:
        detail = f"本地{mode}OTA升级时，点击install失败"
        logger.info(detail, sn=sn)
        screencap(sn, detail + datetime.strftime(datetime.now(), "_%Y%m%d_%H%M%S"))
        return False, detail + "\n" + str(earse_result_list) + "\n" + str(ke_result_list) + "\n" + str(reboot_result_list)
    if ota_global_config.ke_test:
        ke = KETest(sn)
        ke.ke_test()
    if mode:
        reboot_for_rollback(sn, rollback_times=ota_global_config.rollback_reboot_round, setting=ota_global_config.settings)
    check_reboot_status(sn, setting=ota_global_config.settings)
    get_Screen_on(sn, ota_global_config.settings)
    cmdline = [adb, "-s", sn, "shell", "input keyevent 82"]
    exec_cmd(cmdline)
    build_after_update = get_project_version(sn)
    if target_build == build_after_update:
        return True, f"本地{mode}OTA升级成功" + "\n" + str(earse_result_list) + "\n" + str(ke_result_list) + "\n" + str(reboot_result_list)
    else:
        return False, f"当前版本为{build_after_update},本地{mode}OTA升级失败" + "\n" + str(earse_result_list) + "\n" + str(ke_result_list) + "\n" + str(reboot_result_list)


def do_ota_update_online(sn, target_build, debug_mode, log_path, mode=""):
    """
    在线升级主流程，含回滚、重启、恢厂测试操作
    :param sn: 手机sn号
    :param target_build: 目标版本
    :param debug_mode: 调试模式
    :param mode: 升级模式
    :return:
    """
    cmd = [adb, "-s", sn, "shell", "appops set --uid com.transsion.otastep MANAGE_EXTERNAL_STORAGE allow"]
    exec_cmd(cmd)
    time.sleep(2)
    logger.info(f"设备{sn}执行在线{mode}OTA升级主流程", sn=sn)
    if debug_mode:
        time.sleep(2)
        return True, f"在线{mode}OTA升级成功"

    earse_result_list = []
    ke_result_list = []
    reboot_result_list = []

    if ota_global_config.reboot and (mode or (not mode and not ota_global_config.rollback_test)):
        logger.info(f"设备{sn}执行在线{mode}OTA升级流程中重启测试", sn=sn)
        reboot_list = [int(i) for i in ota_global_config.reboot_progress]
        reboot_list = sorted(reboot_list)  # ota升级，重启后第二次点击install会继续上次进度升级，这里从小到大排个序
        logger.info(f"设备{sn}在线{mode}OTA升级重启进度列表：{reboot_list}", sn=sn)
        roboot_num = 0
        reboot_result_list = []
        for progress in reboot_list:
            check_reboot_status(sn, setting=ota_global_config.settings)
            time.sleep(20)
            build_after_update = get_project_version(sn)
            if target_build == build_after_update:
                return True, f"重启后手机版本为目标版本，结束在线{mode}OTA升级流程，重启次数{roboot_num}"
            roboot_num = roboot_num + 1
            logger.info(f"设备{sn}在线{mode}OTA升级到【{progress}分钟】后进行重启", sn=sn)
            if click_online_tcard(sn, ota_global_config.ssid, ota_global_config.ssid_password):
                logger.info(f"设备{sn}在线{mode}OTA升级，成功进入升级流程", sn=sn)
                cmdProgress = [adb, "-s", sn, "shell",
                               "am instrument -w -m -e debug false -e updateprogress " + str(
                                   progress) + " -e class 'com.transsion.testcaserepository.ota.TestImportOnlineUpdatePercentOta#testImportOnlineUpdatePercent' com.transsion.otastep.test/androidx.test.runner.AndroidJUnitRunner"]
                if execute_java_case(cmdProgress, ota_global_config.ota_update_time*60):
                    logger.info(f"设备{sn}在在线{mode}OTA升级进度为{progress}分钟时，进行重启成功", sn=sn)
                    time.sleep(20)  # 睡眠20秒，因手机重启后会短暂几秒内可以查找到设备，防止下一轮找到设备后直接开始
                else:
                    detail = f"设备{sn}在在线{mode}OTA升级进度为{progress}分钟时，进行重启失败"
                    logger.info(f"设备{sn}在在线{mode}OTA升级进度为{progress}分钟时，进行重启失败", sn=sn)
                    reboot_result_list.append(detail)
                    screencap(sn, f"进度为{progress}分钟时，进行重启失败" + datetime.strftime(datetime.now(), "_%Y%m%d_%H%M%S"))
                    continue
            else:
                detail = f"在线{mode}OTA升级进度{progress}分钟，未能进入升级流程"
                logger.info(detail, sn=sn)
                reboot_result_list.append(detail)
                screencap(sn, f"进度{progress}分钟，未能进入升级流程" + datetime.strftime(datetime.now(), "_%Y%m%d_%H%M%S"))
                continue
    check_reboot_status(sn, setting=ota_global_config.settings)
    if ota_global_config.erase_test:
        logger.info(f"设备{sn}执行在线{mode}OTA升级流程中恢复出厂设置测试", sn=sn)
        erase_list = [int(i) for i in ota_global_config.erase_progress]
        erase_list = sorted(erase_list)
        logger.info(f"设备{sn}在线{mode}OTA升级恢复出厂设置进度列表：{erase_list}", sn=sn)
        earse_num = 0
        earse_result_list = []
        for progress in erase_list:
            check_reboot_status(sn, setting=ota_global_config.settings)
            time.sleep(20)
            set_screen_time(sn)
            build_after_update = get_project_version(sn)
            if target_build == build_after_update:
                return True, f"恢复出厂设置后手机版本为目标版本，结束在线{mode}OTA升级流程，恢复出厂设置次数{earse_num}"
            earse_num = earse_num + 1
            path = os.path.join(log_path, str(earse_num))
            os.makedirs(path, exist_ok=True)
            export_logs(sn, ota_global_config.mtk_or_sprd, path)
            logger.info(f"设备{sn}在线{mode}OTA升级到【{progress}%】后进行恢复出厂设置", sn=sn)
            test_init(sn, ota_global_config.config_tag, ota_global_config.resource_dir)
            reset_online_tcard(sn)
            if click_online_tcard(sn, ota_global_config.ssid, ota_global_config.ssid_password):
                logger.info(f"设备{sn}在线{mode}OTA升级, 成功进入升级流程", sn=sn)
                cmdProgress = [adb, "-s", sn, "shell",
                               "am instrument -w -m -e debug false -e updateprogress " + str(
                                   progress) + " -e screenPassword 123456 -e class 'com.transsion.testcaserepository.ota.TestImportOnlineUpdateResetPercentOta#testImportOnlineUpdateResetPercent' com.transsion.otastep.test/androidx.test.runner.AndroidJUnitRunner"]
                if execute_java_case(cmdProgress, ota_global_config.ota_update_time * 60):
                    logger.info(f"设备{sn}在线{mode}OTA升级进度为{progress}分钟时，进行恢复出厂设置成功", sn=sn)
                    time.sleep(20)  # 睡眠20秒，因手机重启后会短暂几秒内可以查找到设备，防止下一轮找到设备后直接开始
                else:
                    detail = f"设备{sn}在在线{mode}OTA升级进度为{progress}分钟时，进行恢复出厂设置失败"
                    logger.info(f"设备{sn}在在线{mode}OTA升级进度为{progress}分钟时，进行恢复出厂设置失败", sn=sn)
                    cmd = [adb, "-s", sn, "reboot"]
                    exec_cmd(cmd)
                    check_reboot_status(sn, setting=ota_global_config.settings)
                    earse_result_list.append(detail)
                    screencap(sn, f"进度为{progress}分钟时，进行恢厂失败" + datetime.strftime(datetime.now(), "_%Y%m%d_%H%M%S"))
                    continue
            else:
                detail = f"在线{mode}OTA升级进度{progress}分钟，进入升级流程时恢厂失败"
                logger.info(detail, sn=sn)
                earse_result_list.append(detail)
                screencap(sn, f"进度{progress}分钟，进入升级流程时恢厂失败" + datetime.strftime(datetime.now(), "_%Y%m%d_%H%M%S"))
                continue
        if ota_global_config.mtk_or_sprd == "mtk":
            reset_mtk_log_by_device(sn)
        else:
            reset_sprd_log_by_device(sn)
    check_reboot_status(sn, setting=ota_global_config.settings)
    if ota_global_config.ke_test:
        logger.info(f"设备{sn}执行在线{mode}OTA升级流程中KE打断", sn=sn)
        ke_list = [int(i) for i in ota_global_config.ke_progress]
        ke_list = sorted(ke_list)
        logger.info(f"设备{sn}在线{mode}OTA升级KE打断进度列表：{ke_list}", sn=sn)
        ke_num = 0
        ke_result_list = []
        for progress in ke_list:
            check_reboot_status(sn, setting=ota_global_config.settings)
            time.sleep(20)
            build_after_update = get_project_version(sn)
            if target_build == build_after_update:
                return True, f"重启后手机版本为目标版本，结束在线{mode}OTA升级流程，KE打断次数{ke_num}"
            ke_num = ke_num + 1
            logger.info(f"设备{sn}在线{mode}OTA升级到【{progress}%】后进行KE打断", sn=sn)
            if click_online_tcard(sn, ota_global_config.ssid, ota_global_config.ssid_password):
                logger.info(f"设备{sn}在线{mode}OTA升级, 成功进入升级流程", sn=sn)
                cmdProgress = [adb, "-s", sn, "shell",
                               "am instrument -w -m -e debug false -e updateprogress " + str(
                                   progress) + " -e screenPassword 123456 -e class 'com.transsion.testcaserepository.ota.TestImportOnlineUpdateKePercentOta#testImportOnlineUpdateKePercent' com.transsion.otastep.test/androidx.test.runner.AndroidJUnitRunner"]
                if execute_java_case(cmdProgress, ota_global_config.ota_update_time * 60):
                    logger.info(f"设备{sn}在线{mode}OTA升级进度为{progress}分钟时，进行KE打断", sn=sn)
                    ke = KETest(sn)
                    ke.ke_test()
                else:
                    detail = f"设备{sn}在在线{mode}OTA升级进度为{progress}分钟时，进行KE打断失败"
                    logger.info(f"设备{sn}在在线{mode}OTA升级进度为{progress}分钟时，进行KE打断失败", sn=sn)
                    cmd = [adb, "-s", sn, "reboot"]
                    exec_cmd(cmd)
                    check_reboot_status(sn, setting=ota_global_config.settings)
                    ke_result_list.append(detail)
                    screencap(sn, f"进度为{progress}分钟时，进行KE打断失败" + datetime.strftime(datetime.now(), "_%Y%m%d_%H%M%S"))
                    continue
            else:
                detail = f"在线{mode}OTA升级进度{progress}分钟，进入升级流程时KE打断"
                logger.info(detail, sn=sn)
                ke_result_list.append(detail)
                screencap(sn, f"进度{progress}分钟，进入升级流程时KE打断失败" + datetime.strftime(datetime.now(), "_%Y%m%d_%H%M%S"))
                continue
    logger.info(f"设备{sn}执行在线{mode}OTA升级流程，进行正常OTA升级", sn=sn)
    if click_online_tcard(sn, ota_global_config.ssid, ota_global_config.ssid_password):
        logger.info(f"设备{sn}在线{mode}OTA升级, 成功进入升级流程", sn=sn)
        cmdReboot = [adb, "-s", sn, "shell",
                     f"am instrument -w -m    -e debug false -e otaUpdateTime {str(ota_global_config.ota_update_time)} -e class 'com.transsion.testcaserepository.ota.TestImportOnlineUpdateOta#testImportOnlineUpdate' com.transsion.otastep.test/androidx.test.runner.AndroidJUnitRunner"]
        if execute_java_case(cmdReboot, ota_global_config.ota_update_time*60):
            logger.info(f"在线{mode}OTA升级完成,点击reboot成功", sn=sn)
            cmd =[adb, "-s", sn, "reboot"]
            logger.info(f"在线{mode}OTA升级完成,直接重启", sn=sn)
            exec_cmd(cmd)
            time.sleep(5)
        else:
            if not ota_global_config.rollback_test:
                logger.info(f"在线{mode}OTA升级执行用例失败,直接重启", sn=sn)
                cmd = [adb, "-s", sn, "reboot"]
                exec_cmd(cmd)
                time.sleep(5)
                check_reboot_status(sn, setting=ota_global_config.settings)
                build_after_update = get_project_version(sn)
                if target_build == build_after_update:
                    logger.info(f"在线{mode}OTA升级完成,直接重启", sn=sn)
                    exec_cmd(cmd)
                    time.sleep(5)
                else:
                    detail = f"升级用例执行失败，在线{mode}OTA升级失败"
                    logger.info(detail, sn=sn)
                    screencap(sn, detail + datetime.strftime(datetime.now(), "_%Y%m%d_%H%M%S"))
                    return False, detail + "\n" + str(earse_result_list) + "\n" + str(ke_result_list) + "\n" + str(reboot_result_list)
            else:
                detail = f"升级用例执行失败，在线{mode}OTA升级失败"
                logger.info(detail, sn=sn)
                screencap(sn, detail + datetime.strftime(datetime.now(), "_%Y%m%d_%H%M%S"))
                return False, detail + "\n" + str(earse_result_list) + "\n" + str(ke_result_list) + "\n" + str(reboot_result_list)
    else:
        detail = f"在线{mode}OTA升级时，未能进入升级流程"
        logger.info(detail, sn=sn)
        screencap(sn, detail + datetime.strftime(datetime.now(), "_%Y%m%d_%H%M%S"))
        return False, detail + "\n" + str(earse_result_list) + "\n" + str(ke_result_list) + "\n" + str(reboot_result_list)
    if ota_global_config.ke_test:
        ke = KETest(sn)
        ke.ke_test()
    if mode:
        reboot_for_rollback(sn, rollback_times=ota_global_config.rollback_reboot_round, setting=ota_global_config.settings)
    check_reboot_status(sn, setting=ota_global_config.settings)
    get_Screen_on(sn, ota_global_config.settings)
    cmdline = [adb, "-s", sn, "shell", "input keyevent 82"]
    exec_cmd(cmdline)
    build_after_update = get_project_version(sn)
    if target_build == build_after_update:
        return True, f"在线{mode}OTA升级成功" + "\n" + str(earse_result_list) + "\n" + str(ke_result_list) + "\n" + str(reboot_result_list)
    else:
        return False, f"当前版本为{build_after_update},在线{mode}OTA升级失败" + "\n" + str(earse_result_list) + "\n" + str(ke_result_list) + "\n" + str(reboot_result_list)


def ota_rollback(sn, tcardname, target_build, debug_mode):
    logger.info(f"设备{sn}执行本地升级回滚主流程", sn=sn)
    if debug_mode:
        time.sleep(2)
        return True, f"回滚成功"
    radom_list, radom_flag = pre_random()
    for i in range(1, 3):
        d = connect_u2(sn)
        try:
            logger.info("手机亮屏解锁", sn=sn)
            get_Screen_on(d, sn)
            time.sleep(2)
            d.press("home")
            time.sleep(1)
            if d(text="ALLOW").exists:
                d(text="ALLOW").click()
                time.sleep(2)
            if d(description="Phone").exists or check_activity(sn):
                if not click_Tcard(d, sn, tcardname, ota_global_config.sdcard_path):
                    screencap(sn, f"回滚未找到升级包_{PathManager.current_time_stamp}")
                    return False, f"五次次搜索后，未找到升级包并点击，回滚失败，失败时间：{PathManager.current_time_stamp}"
                enter_local_update(sn)
                k = 0
                logger.info("T卡包升级中", sn=sn)
                while True:
                    get_Screen_on(d, sn)
                    enter_local_update(sn)
                    find_object_text_click(d, "SKIP")
                    reboot = find_object_text_match(d, "REBOOT")
                    if reboot:
                        logger.info("找到Reboot相关控件，点击", sn=sn)
                        reboot.click()
                        time.sleep(5)
                        device_list = get_devices_list()
                        if sn in device_list:
                            logger.info(f"点击控件重启失败,强制重启", sn=sn)
                            cmdline = [adb, "-s", sn, "reboot"]
                            exec_cmd(cmdline)
                            time.sleep(5)
                        break
                    elif find_object_text_match(d, "LOCAL UPDATE"):
                        logger.info("点击升级失败，回滚失败", sn=sn)
                        screencap(sn, f"回滚点击升级失败_{PathManager.current_time_stamp}")
                        return False, f"未找到升级包并点击，回滚失败，失败时间：{PathManager.current_time_stamp}"
                    else:
                        time.sleep(60)
                        k += 1
                        logger.info(f"第{k}分钟进行回滚前升级检查~", sn=sn)
                        if k == 3 and ota_global_config.more_test:
                            more = MoreTest(sn)
                            more.run()
                        if ota_global_config.reboot and radom_flag < 2:
                            if random.choice(radom_list):
                                logger.info("进行重启测试", sn=sn)
                                reboot = RebootTest(sn, tcardname)
                                reboot.run()
                                radom_flag = radom_flag + 1
                            # 超过21分钟还未判定到重启就增加判定概率，增加至2/5
                            if k >= 21 and radom_list.count(True) <= 5:
                                logger.info("修改重启事件概率", sn=sn)
                                radom_list = change_random(radom_list)
                        if k == 5 and ota_global_config.erase_test:
                            logger.info("进行恢厂测试", sn=sn)
                            erase = EraseTest(sn)
                            result = erase.run()
                            if result:
                                detail = f"恢厂测试成功，跳过回滚，时间：{PathManager.current_time_stamp}"
                            else:
                                detail = f"恢厂测试失败，回滚失败, 时间：{PathManager.current_time_stamp}"
                            return result, detail
                        if k > ota_global_config.ota_update_time:
                            logger.info("回滚超时", sn=sn)
                            get_Screen_on(d, sn)
                            now = datetime.now()
                            curr_time = datetime.strftime(now, '%Y-%m-%d_%H:%M:%S')
                            cmdline = [adb, "-s", sn, "shell", f"screencap -p /sdcard/Auto/screencap/update_overtime_{curr_time}.png"]
                            exec_cmd(cmdline)
                            time.sleep(5)
                            logger.error("回滚超时",sn=sn)
                            screencap(sn, f"回滚超时_{PathManager.current_time_stamp}")
                            return False, f"回滚超时，失败时间：{PathManager.current_time_stamp}"
            else:
                logger.error(f"第{i}次找不到桌面", sn=sn)
                if i == 3:
                    screencap(sn, f"找不到桌面_{PathManager.current_time_stamp}")
                    return False, "找不到桌面，回滚失败"
                continue
        except Exception as e:
            if i==1 and "uiautomator" in str(e):
                logger.info(f"设备{sn}回滚过程中出现异常:{str(e)},重试")
                continue
            else:
                logger.info(f"设备{sn}回滚过程中出现异常:{str(e)},退出当前回滚流程", sn=sn)
                screencap(sn, f"回滚异常_{PathManager.current_time_stamp}")
                return False, f"回滚出现异常,异常时间：{PathManager.current_time_stamp}"
        try:
            logger.info("T卡包升级成功", sn=sn)
            time.sleep(5)
            if ota_global_config.ke_test:
                ke = KETest(sn)
                ke.ke_test()
            reboot_for_rollback(sn, rollback_times=ota_global_config.rollback_reboot_round, setting=ota_global_config.settings)
            get_Screen_on(d, sn)
            if d(text="ALLOW").exists:
                d(text="ALLOW").click()
                time.sleep(2)
            cmdline = [adb, "-s", sn, "shell", "input keyevent 82"]
            exec_cmd(cmdline)
            build_after_rollback = get_project_version(sn)
            if target_build == build_after_rollback:
                return True, f"回滚成功"
            else:
                return False, "回滚失败"
        except Exception as e:
            logger.error(f"回滚过程中出现异常:{str(e)}", sn=sn)
            return False, f"回滚失败"


def ota_rollback_online(sn, ssid, password, target_build, debug_mode):
    logger.info(f"设备{sn}执行在线回滚主流程", sn=sn)
    if debug_mode:
        time.sleep(2)
        return True, f"在线回滚成功"
    radom_list, radom_flag = pre_random()
    for i in range(1, 3):
        d = connect_u2(sn)
        try:
            logger.info("手机亮屏解锁", sn=sn)
            get_Screen_on(d, sn)
            time.sleep(2)
            d.press("home")
            time.sleep(1)
            if d(text="ALLOW").exists:
                d(text="ALLOW").click()
                time.sleep(2)
            if d(text="OK").exists:
                d(text="OK").click()
                time.sleep(2)
            if d(description="Phone").exists or check_activity(sn):
                if not click_Tcard_online(d, sn, ssid, password):
                    screencap(sn, f"回滚未找到在线升级包_{PathManager.current_time_stamp}")
                    return False, f"30次搜索后，未找到在线升级包并点击，在线回滚失败，失败时间：{PathManager.current_time_stamp}"
                enter_online_update(sn)
                k = 0
                logger.info("在线升级中", sn=sn)
                while True:
                    get_Screen_on(d, sn)
                    enter_online_update(sn)
                    find_object_text_click(d, "SKIP")
                    find_object_text_click(d, "OK")
                    reboot = find_object_text_match(d, "Restart now")
                    if reboot:
                        logger.info("找到Restart now相关控件，点击", sn=sn)
                        reboot.click()
                        time.sleep(5)
                        device_list = get_devices_list()
                        if sn in device_list:
                            logger.info(f"点击控件重启失败,强制重启", sn=sn)
                            cmdline = [adb, "-s", sn, "reboot"]
                            exec_cmd(cmdline)
                            time.sleep(5)
                        break
                    elif find_object_text_match(d, "ONELINE UPDATE"):
                        logger.info("点击升级失败，在线回滚失败", sn=sn)
                        screencap(sn, f"在线回滚点击升级失败_{PathManager.current_time_stamp}")
                        return False, f"未找到升级包并点击，在线回滚失败，失败时间：{PathManager.current_time_stamp}"
                    else:
                        time.sleep(60)
                        k += 1
                        logger.info(f"第{k}分钟进行在线回滚检查~", sn=sn)
                        if k == 3 and ota_global_config.more_test:
                            more = MoreTest(sn)
                            more.run()
                        if ota_global_config.reboot and radom_flag < 2:
                            if random.choice(radom_list):
                                logger.info("进行重启测试", sn=sn)
                                reboot = RebootTest(sn)
                                reboot.run()
                                radom_flag = radom_flag + 1
                            # 超过21分钟还未判定到重启就增加判定概率，增加至2/5
                            if k >= 21 and radom_list.count(True) <= 5:
                                logger.info("修改重启事件概率", sn=sn)
                                radom_list = change_random(radom_list)
                        if k == 5 and ota_global_config.erase_test:
                            logger.info("进行恢厂测试", sn=sn)
                            erase = EraseTest(sn)
                            result = erase.run()
                            if result:
                                detail = f"恢厂测试成功，跳过在线回滚，时间：{PathManager.current_time_stamp}"
                            else:
                                detail = f"恢厂测试失败，在线回滚失败, 时间：{PathManager.current_time_stamp}"
                            return result, detail
                        if k > ota_global_config.ota_update_time:
                            logger.info("在线回滚超时", sn=sn)
                            get_Screen_on(d, sn)
                            now = datetime.now()
                            curr_time = datetime.strftime(now, '%Y-%m-%d_%H:%M:%S')
                            cmdline = [adb, "-s", sn, "shell", f"screencap -p /sdcard/Auto/screencap/update_overtime_{curr_time}.png"]
                            exec_cmd(cmdline)
                            time.sleep(5)
                            logger.error("在线回滚超时", sn=sn)
                            screencap(sn, f"在线回滚超时_{PathManager.current_time_stamp}")
                            return False, f"在线回滚超时，失败时间：{PathManager.current_time_stamp}"
            else:
                logger.error(f"第{i}次找不到桌面", sn=sn)
                if i == 2:
                    screencap(sn, f"找不到桌面_{PathManager.current_time_stamp}")
                    return False, "找不到桌面，在线回滚失败"
                continue
        except Exception as e:
            if i==1 and "uiautomator" in str(e):
                logger.info(f"设备{sn}在线回滚过程中出现异常:{str(e)},重试")
                continue
            else:
                logger.info(f"设备{sn}在线回滚过程中出现异常:{str(e)},退出当前在线回滚流程", sn=sn)
                screencap(sn, f"在线回滚异常_{PathManager.current_time_stamp}")
                return False, f"在线回滚出现异常,异常时间：{PathManager.current_time_stamp}"
        try:
            logger.info("在线升级成功", sn=sn)
            time.sleep(5)
            if ota_global_config.ke_test:
                ke = KETest(sn)
                ke.ke_test()
            reboot_for_rollback(sn, rollback_times=ota_global_config.rollback_reboot_round, setting=ota_global_config.settings)
            get_Screen_on(d, sn)
            connect_u2(sn)
            if d(text="ALLOW").exists:
                d(text="ALLOW").click()
                time.sleep(2)
            if d(text="OK").exists:
                d(text="OK").click()
                time.sleep(2)
            cmdline = [adb, "-s", sn, "shell", "input keyevent 82"]
            exec_cmd(cmdline)
            build_after_online_rollback = get_project_version(sn)
            if target_build == build_after_online_rollback:
                return True, f"在线回滚成功"
            else:
                return False, "在线回滚失败"
        except Exception as e:
            logger.error(f"在线回滚过程中出现异常:{str(e)}", sn=sn)
            return False, f"在线回滚失败"


def ota_update(sn, tcardname, target_build, debug_mode):
    logger.info(f"设备{sn}执行OTA本地升级主流程", sn=sn)
    if debug_mode:
        time.sleep(2)
        return True, f"OTA升级成功"
    radom_list, radom_flag = pre_random()
    for i in range(1, 3):
        d = connect_u2(sn)
        try:
            logger.info("手机亮屏解锁", sn=sn)
            get_Screen_on(d, sn)
            time.sleep(2)
            d.press("home")
            time.sleep(1)
            if d(text="ALLOW").exists:
                d(text="ALLOW").click()
                time.sleep(2)
            if d(description="Phone").exists or check_activity(sn):
                if not click_Tcard(d, sn, tcardname, ota_global_config.sdcard_path):
                    screencap(sn, f"未找到升级包_{PathManager.current_time_stamp}")
                    return False, f"五次次搜索后，未找到升级包并点击，OTA升级失败，失败时间：{PathManager.current_time_stamp}"
                enter_local_update(sn)
                k = 0
                logger.info("T卡包升级中", sn=sn)
                while True:
                    get_Screen_on(d, sn)
                    enter_local_update(sn)
                    find_object_text_click(d, "SKIP")
                    reboot = find_object_text_match(d, "REBOOT")
                    if reboot:
                        logger.info("找到Reboot相关控件，点击", sn=sn)
                        reboot.click()
                        time.sleep(5)
                        device_list = get_devices_list()
                        if sn in device_list:
                            logger.info(f"点击控件重启失败,强制重启", sn=sn)
                            cmdline = [adb, "-s", sn, "reboot"]
                            exec_cmd(cmdline)
                            time.sleep(5)
                        break
                    elif find_object_text_match(d, "LOCAL UPDATE"):
                        logger.info("点击升级失败，OTA升级失败", sn=sn)
                        screencap(sn, f"点击升级失败_{PathManager.current_time_stamp}")
                        return False, f"未找到升级包并点击，OTA升级失败，失败时间：{PathManager.current_time_stamp}"
                    else:
                        time.sleep(60)
                        k += 1
                        logger.info(f"第{k}分钟进行OTA升级检查~", sn=sn)
                        if k == 3 and ota_global_config.more_test:
                            more = MoreTest(sn)
                            more.run()
                        if ota_global_config.reboot and radom_flag < 2:
                            if random.choice(radom_list):
                                logger.info("进行重启测试", sn=sn)
                                reboot = RebootTest(sn, tcardname)
                                reboot.run()
                                radom_flag = radom_flag + 1
                            # 超过21分钟还未判定到重启就增加判定概率，增加至2/5
                            if k >= 21 and radom_list.count(True) <= 5:
                                logger.info("修改重启事件概率", sn=sn)
                                radom_list = change_random(radom_list)
                        if k == 5 and ota_global_config.erase_test:
                            logger.info("进行恢厂测试", sn=sn)
                            erase = EraseTest(sn)
                            result = erase.run()
                            if result:
                                detail = f"恢厂测试成功，跳过OTA升级，时间：{PathManager.current_time_stamp}"
                            else:
                                detail = f"恢厂测试失败，OTA升级失败, 时间：{PathManager.current_time_stamp}"
                            return result, detail
                        if k > ota_global_config.ota_update_time:
                            logger.info("T卡包升级超时", sn=sn)
                            get_Screen_on(d, sn)
                            now = datetime.now()
                            curr_time = datetime.strftime(now, '%Y-%m-%d_%H:%M:%S')
                            cmdline = [adb, "-s", sn, "shell", f"screencap -p /sdcard/Auto/screencap/update_overtime_{curr_time}.png"]
                            exec_cmd(cmdline)
                            time.sleep(5)
                            logger.error("OTA升级超时",sn=sn)
                            screencap(sn, f"OTA升级超时_{PathManager.current_time_stamp}")
                            return False, f"OTA升级超时，失败时间：{PathManager.current_time_stamp}"
            else:
                logger.error(f"第{i}次找不到桌面", sn=sn)
                if i == 2:
                    screencap(sn, f"找不到桌面_{PathManager.current_time_stamp}")
                    return False, "找不到桌面，升级失败"
                continue
        except Exception as e:
            if i==1 and "uiautomator" in str(e):
                logger.info(f"设备{sn}升级过程中出现异常:{str(e)},重试")
                continue
            else:
                logger.info(f"设备{sn}升级过程中出现异常:{str(e)},退出当前OTA升级流程", sn=sn)
                screencap(sn, f"升级异常_{PathManager.current_time_stamp}")
                return False, f"OTA升级出现异常,异常时间：{PathManager.current_time_stamp}"
        try:
            logger.info("T卡包升级成功", sn=sn)
            time.sleep(5)
            if ota_global_config.ke_test:
                ke = KETest(sn)
                ke.ke_test()
            check_reboot_status(sn, setting=ota_global_config.settings)
            get_Screen_on(d, sn)
            if d(text="ALLOW").exists:
                d(text="ALLOW").click()
                time.sleep(2)
            cmdline = [adb, "-s", sn, "shell", "input keyevent 82"]
            exec_cmd(cmdline)
            build_after_update = get_project_version(sn)
            if target_build == build_after_update:
                return True, f"本地OTA升级成功"
            else:
                return False, "本地OTA升级失败"
        except Exception as e:
            logger.error(f"OTA升级过程中出现异常:{str(e)}", sn=sn)
            return False, f"本地OTA升级失败"


def ota_update_online(sn, ssid, password, target_build,debug_mode):
    logger.info(f"设备{sn}执行OTA在线升级主流程", sn=sn)
    if debug_mode:
        time.sleep(2)
        return True, f"OTA在线升级成功"
    radom_list, radom_flag = pre_random()
    for i in range(1, 3):
        d = connect_u2(sn)
        try:
            logger.info("手机亮屏解锁", sn=sn)
            get_Screen_on(d, sn)
            time.sleep(2)
            d.press("home")
            time.sleep(1)
            if d(text="ALLOW").exists:
                d(text="ALLOW").click()
                time.sleep(2)
            if d(text="OK").exists:
                d(text="OK").click()
                time.sleep(2)
            if d(description="Phone").exists or check_activity(sn):
                if not click_Tcard_online(d, sn, ssid, password):
                    screencap(sn, f"未找到升级包_{PathManager.current_time_stamp}")
                    return False, f"30次搜索后，未找到在线升级包并点击，OTA升级失败，失败时间：{PathManager.current_time_stamp}"
                enter_online_update(sn)
                k = 0
                logger.info("在线升级中", sn=sn)
                while True:
                    get_Screen_on(d, sn)
                    enter_online_update(sn)
                    find_object_text_click(d, "SKIP")
                    find_object_text_click(d, "OK")
                    reboot = find_object_text_match(d, "Restart now")
                    if reboot:
                        logger.info("找到Restart now相关控件，点击", sn=sn)
                        reboot.click()
                        time.sleep(5)
                        device_list = get_devices_list()
                        if sn in device_list:
                            logger.info(f"点击控件重启失败,强制重启", sn=sn)
                            cmdline = [adb, "-s", sn, "reboot"]
                            exec_cmd(cmdline)
                            time.sleep(5)
                        break
                    elif find_object_text_match(d, "ONELINE UPDATE"):
                        logger.info("点击升级失败，OTA升级失败", sn=sn)
                        screencap(sn, f"点击升级失败_{PathManager.current_time_stamp}")
                        return False, f"未找到升级包并点击，OTA升级失败，失败时间：{PathManager.current_time_stamp}"
                    else:
                        time.sleep(60)
                        k += 1
                        logger.info(f"第{k}分钟进行OTA升级检查~", sn=sn)
                        if k == 3 and ota_global_config.more_test:
                            more = MoreTest(sn)
                            more.run()
                        if ota_global_config.reboot and radom_flag < 2:
                            if random.choice(radom_list):
                                logger.info("进行重启测试", sn=sn)
                                reboot = RebootTest(sn)
                                reboot.run()
                                radom_flag = radom_flag + 1
                            # 超过21分钟还未判定到重启就增加判定概率，增加至2/5
                            if k >= 21 and radom_list.count(True) <= 5:
                                logger.info("修改重启事件概率", sn=sn)
                                radom_list = change_random(radom_list)
                        if k == 5 and ota_global_config.erase_test:
                            logger.info("进行恢厂测试", sn=sn)
                            erase = EraseTest(sn)
                            result = erase.run()
                            if result:
                                detail = f"恢厂测试成功，跳过在线OTA升级，时间：{PathManager.current_time_stamp}"
                            else:
                                detail = f"恢厂测试失败，在线OTA升级失败, 时间：{PathManager.current_time_stamp}"
                            return result, detail
                        if k > ota_global_config.ota_update_time:
                            logger.info("在线升级超时", sn=sn)
                            get_Screen_on(d, sn)
                            now = datetime.now()
                            curr_time = datetime.strftime(now, '%Y-%m-%d_%H:%M:%S')
                            cmdline = [adb, "-s", sn, "shell", f"screencap -p /sdcard/Auto/screencap/update_overtime_{curr_time}.png"]
                            time.sleep(5)
                            exec_cmd(cmdline)
                            logger.error("在线OTA升级超时", sn=sn)
                            time.sleep(10)
                            screencap(sn, f"在线OTA升级超时_{PathManager.current_time_stamp}")
                            return False, f"在线OTA升级超时，失败时间：{PathManager.current_time_stamp}"
            else:
                logger.error(f"第{i}次找不到桌面", sn=sn)
                if i == 2:
                    screencap(sn, f"找不到桌面_{PathManager.current_time_stamp}")
                    return False, "找不到桌面，在线升级失败"
                continue
        except Exception as e:
            if i==1 and "uiautomator" in str(e):
                logger.info(f"设备{sn}在线升级过程中出现异常:{str(e)},重试")
                continue
            else:
                logger.info(f"设备{sn}在线升级过程中出现异常:{str(e)},退出当前OTA升级流程", sn=sn)
                screencap(sn, f"升级异常_{PathManager.current_time_stamp}")
                return False, f"在线OTA升级出现异常,异常时间：{PathManager.current_time_stamp}"
        try:
            logger.info("在线升级成功", sn=sn)
            time.sleep(5)
            if ota_global_config.ke_test:
                ke = KETest(sn)
                ke.ke_test()
            check_reboot_status(sn, setting=ota_global_config.settings)
            get_Screen_on(d, sn)
            connect_u2(sn)
            if d(text="ALLOW").exists:
                d(text="ALLOW").click()
                time.sleep(2)
            if d(text="OK").exists:
                d(text="OK").click()
                time.sleep(2)
            cmdline = [adb, "-s", sn, "shell", "input keyevent 82"]
            exec_cmd(cmdline)
            build_after_online_update = get_project_version(sn)
            if target_build == build_after_online_update:
                return True, f"在线OTA升级成功"
            else:
                return False, "在线OTA升级失败"
        except Exception as e:
            logger.error(f"OTA升级过程中出现异常:{str(e)}", sn=sn)
            return False, f"在线OTA升级失败"

def get_ota_satate(sn):
    cmd = [adb, "-s", sn,  "logcat", "-b all | findstr update_engine"]
    rlt, content = exec_cmd(cmd, 10)
    for item in content:
        if "update_engine" in item.decode().strip():
            return True
    else:
        return False

def screencap(sn, info):
    """
    截图保存相关信息
    :param sn: 手机设备sn号
    :param info: 截图名称
    :return:
    """
    if ota_global_config.ota_update_mode == "local":
        enter_local_update(sn)
    elif ota_global_config.ota_update_mode == "online":
        enter_online_update(sn)
    time.sleep(2)
    cmd = [adb, "-s", sn, "shell", f"screencap /sdcard/screencap/{info}.png"]
    exec_cmd(cmd)


if __name__ == '__main__':
    # ota_global_config.load_config("CG6S")
    sn = "067062513C101821"
    progress = 15
    # scatter_file_path = "123"
    # target_build = "CG6-H696UVWBc-S-OP-221107V32367"
    # logger.error("版本回刷失败, 尝试重新进行刷机, 失败次数1", tag=sn)
    path = "F:/test"
    log_path = os.path.join(path, str(progress))
    os.makedirs(log_path)
