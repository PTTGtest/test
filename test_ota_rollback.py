# coding:utf-8
# @Time     : 2023年07月12日
# @Author   : junxian.geng
# @Email    : junxian.geng@transsion.com
# @description:

import time


def do_ota_rollback(rollback_count=1):
    """
    执行ota升级
    :return:
    """
    """
    调用 ota 升级脚本，进行ota升级后，触发回滚
    """
    step_group = "test"
    step_index = "test_index"
    current_build = "123456"
    target_build = current_build
    package_path = "test_path"

    print(
        f"【第test轮】【第{step_group}组】【第{step_index}步】开始执行ota升级回滚测试，当前版本：{current_build}，目标版本：{target_build}，计划回滚次数：{rollback_count}")
    print(f"版本包路径：{package_path}")

    # 根据手机内安装包放置路径，区分内置ROM、sdcard

    result_list = []
    detail_list = []
    rollback_num = 0  # 真实的回滚次数
    for count in range(rollback_count):
        if False:
            time.sleep(5)
        else:
            print("推送升级包到手机")
        # 执行ota升级
        ota_rollback_result, ota_rollback_detail = False, "None"
        if False:
            ota_rollback_result, ota_rollback_detail = True, "None"
        else:
            print(f"第{count+1}次执行ota回滚升级")
            if count != 4:
                ota_rollback_result, ota_rollback_detail = True, "test结果"
            else:
                ota_rollback_result, ota_rollback_detail = False, "test结果"
            result_list.append(ota_rollback_result)
            detail_list.append(ota_rollback_detail)
            if count == 4:
                build_after_update = "123"
            else:
                build_after_update = "123456"
            rollback_num = count + 1
            if target_build != build_after_update:
                print(f"OTA本地回滚升级失败，当前回滚次数{count + 1}")
                break
    print(result_list)
    if len(result_list) == rollback_count and result_list[-1] is True:
        ota_rollback_result = True
    else:
        ota_rollback_result = False
    ota_rollback_detail = str(detail_list) + "\n回滚次数" + str(rollback_num)
    print(f"已完成ota回滚测试")
    return ota_rollback_result, ota_rollback_detail

if __name__ == '__main__':
    result, detail = do_ota_rollback(5)
    print(result, detail)