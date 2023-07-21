# -*- coding: utf-8 -*-
# @Time     : 2023/2/9 16:27
# @Author   : yunqing.gui
# @Email    : yunqing.gui@transsion.com
# @File     : exec_cmd.py


import tempfile
import subprocess
import traceback

from modules.common.test_logger import logger


def exec_cmd(cmdline, timeout=15, cwd=None):
    """
    在超时时间内，执行指定命令
    :param cmdline: 执行命令
    :param timeout: 超时时间
    :param cwd: 命令执行目录
    :return:
    """
    exec_successfully = True  # 命令执行是否成功
    out_temp = tempfile.SpooledTemporaryFile(10 * 1000)
    fileno = out_temp.fileno()

    try:
        process = subprocess.Popen(cmdline, stdout=fileno, stderr=fileno, shell=False, cwd=cwd)
        process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        logger.error("执行命令：" + str(cmdline) + " 超时！！", tag="exec_cmd")
        exec_successfully = False
    except:
        logger.error("执行命令：" + str(cmdline) + " 出现异常：\n{}".format(traceback.format_exc()), tag="exec_cmd")
        exec_successfully = False
    finally:
        try:
            process.kill()
        except:
            pass

    out_temp.seek(0)
    exec_out = out_temp.readlines()
    out_temp.close()

    return exec_successfully, exec_out


def execute_cmd_retry(cmdline, timeout=15, maxTry=2, curTry=1, cwd=None):
    """
    执行命令，如失败则重试
    :param cmdline:
    :param timeout:
    :param maxTry:
    :param curTry:
    :param cwd:
    :return:
    """
    exec_successfully = True  # 命令执行是否成功
    out_temp = tempfile.SpooledTemporaryFile(10 * 1000)
    fileno = out_temp.fileno()

    try:
        process = subprocess.Popen(cmdline, stdout=fileno, stderr=fileno, shell=False, cwd=cwd)
        process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        logger.error("执行命令：" + str(cmdline) + " 超时！！", tag="execute_cmd_retry")
        exec_successfully = False
    except:
        logger.error("执行命令：" + str(cmdline) + " 出现异常：\n{}".format(traceback.format_exc()), tag="execute_cmd_retry")
        exec_successfully = False
    finally:
        try:
            process.kill()
        except:
            pass

    out_temp.seek(0)
    exec_out = out_temp.readlines()
    out_temp.close()

    # 如果执行失败，且执行次数小于最大重试次数，则重试一次
    if not exec_successfully:
        if curTry < maxTry:
            curTry = curTry + 1
            logger.error("执行命令：" + str(cmdline) + " 未达最大值，尝试执行第[{}]次！".format(curTry), tag="execute_cmd_retry")
            for line in exec_out:
                try:
                    line = line.decode().strip()
                    logger.error(line, tag="execute_cmd_retry")
                except:
                    pass
            exec_successfully, exec_out = execute_cmd_retry(cmdline, timeout=timeout, maxTry=maxTry, curTry=curTry, cwd=cwd)
        else:
            logger.error("执行命令：" + str(cmdline) + " 已达最大失败次数:[{}]，退出执行！".format(maxTry), tag="execute_cmd_retry")

    return exec_successfully, exec_out


def cmd_exec_and_save(cmdline, result_file, timeout=30, cwd=None):
    """
    执行命令，并将命令输出内容保存在文件
    :param cmdline:
    :param result_file:
    :param timeout:
    :param cwd:
    :return:
    """
    exec_successfully = True  # 命令执行是否成功
    o_file = open(result_file, "w")

    try:
        process = subprocess.Popen(cmdline, stdout=o_file, stderr=o_file, shell=False, cwd=cwd)
        process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        logger.error("执行命令：" + str(cmdline) + " 超时！！", tag="exec_cmd")
        exec_successfully = False
    except:
        logger.error("执行命令：" + str(cmdline) + " 出现异常：\n{}".format(traceback.format_exc()), tag="exec_cmd")
        exec_successfully = False
    finally:
        try:
            process.kill()
        except:
            pass
    o_file.close()

    return exec_successfully


def rlt_contains(cmd, key_words):
    """
    执行命令，并判断关键字是否在返回值中
    :param cmd: 对应命令
    :param key_words: 关键字
    :return: 返回判断结果
    """
    rlt = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()[0].decode()
    for line in rlt.splitlines():
        if key_words in line:
            print("Fine key_words:\n" + key_words + "\nIn result line:\n" + line)
            return True
    return False


def execute_instrument(cmd):
    """
    执行命令，并判断命令是否执行成功
    :param cmd: 对应命令
    :return: 返回判断结果和命令执行返回值中标志字符串
    """
    rlt = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()[0].decode()
    for line in rlt.splitlines():
        print(line)
        if "FAILURES" in line:
            print("Find 'FAILURES' in result line:\n" + line)
            return False, "'FAILURES' in result"
        if "(0 tests)" in line:
            print("Find '(0 tests)' in result line:\n" + line)
            return False, "'(0 tests)' in result"
    return True, None
