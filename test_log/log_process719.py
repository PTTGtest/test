# coding:utf-8
# @Time     : 2023年07月19日
# @Author   : junxian.geng
# @Email    : junxian.geng@transsion.com
# @description:
import os
import codecs
import json
from logzero import setup_logger

from test_log.mi_os_exception import MIJiraExp

_log_file = 'run-log.txt'
with open(_log_file, 'w+') as create_file:
    create_file.close()
logger = setup_logger(logfile=_log_file)

def collect_all_exp_from_output(rootdir, output):
    output_paths = []
    for dir_path, dir_names, file_names in os.walk(rootdir):
        for filename in file_names:
            if filename == output:
                output_paths.append(os.path.join(dir_path, filename))

    logger.debug('收集全部的 {} 共计 {}'.format(output, len(output_paths)))
    logger.debug(output_paths)

    all_mi_jira_exps = []
    for output_path in output_paths:
        serial = get_serial_from_output_path(output_path)
        with codecs.open(output_path, encoding='utf-8') as opf:
            lines = opf.read()
            mi_jira_exps = []
            json_dicts_kv = json.loads(lines)
            for json_dict in json_dicts_kv:
                exp = MIJiraExp.from_dict_kv(json_dict)
                exp.id = serial
                apk_version = get_apk_version(serial, exp.Package)
                if apk_version:
                    exp.Package = '{} {}'.format(exp.Package, apk_version)
                exp.Version = get_device_version(serial)
                mi_jira_exps.append(exp)
            all_mi_jira_exps.extend(mi_jira_exps)

    logger.debug('收集全部的exception 共计 {}'.format(len(all_mi_jira_exps)))
    return all_mi_jira_exps

def get_serial_from_output_path(output_path):
    output_dirs = output_path.split(os.path.sep)
    return output_dirs[-2]

def get_apk_version(serial, exppackage):
    info = get_device_info(serial)
    return info.get_app_version_name(exppackage) if info else 'version_default_0'

def get_device_info(serial: str, device=None):
    info: DeviceInfo = registered_device_info.get(serial, None)
    # logger.debug("获取 {} 信息 {}".format(serial, info.valid() if info else False))
    return info