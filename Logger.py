# -*- coding: utf-8 -*-
# @Time     : 2020/1/3 11:30
# @Author   : yunqing.gui
# @Email    : yunqing.gui@transsion.com
# @File     : Logger.py

import os
import logging
import datetime
import traceback

# from modules.common.GlobalAttrs import *


class Logger(object):

    def __init__(self, path, cmd_level=logging.DEBUG, file_level=logging.DEBUG):
        self.logger = logging.getLogger(path)
        self.logger.setLevel(logging.DEBUG)
        fmt = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')

        # 设置CMD日志
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        sh.setLevel(cmd_level)

        # 设置文件日志
        fh = logging.FileHandler(path)
        fh.setFormatter(fmt)
        fh.setLevel(file_level)
        self.logger.addHandler(sh)
        self.logger.addHandler(fh)

    def debug(self, message, tag="UsbHubController", sn=None):
        try:
            if sn is not None:
                self.logger.debug(tag + " --- [{}] --- {}".format(sn, message))
            else:
                self.logger.debug(tag + " --- {}".format(message))
        except:
            traceback.print_exc()

    def info(self, message, tag="UsbHubController", sn=None):
        try:
            if sn is not None:
                self.logger.info(tag + " --- [{}] --- {}".format(sn, message))
            else:
                self.logger.info(tag + " --- {}".format(message))
        except:
            traceback.print_exc()

    def warn(self, message, tag="UsbHubController", sn=None):
        try:
            if sn is not None:
                self.logger.warning(tag + " --- [{}] --- {}".format(sn, message))
            else:
                self.logger.warning(tag + " --- {}".format(message))
        except:
            traceback.print_exc()

    def error(self, message, tag="UsbHubController", sn=None):
        try:
            if sn is not None:
                self.logger.error(tag + " --- [{}] --- {}".format(sn, message))
            else:
                self.logger.error(tag + " --- {}".format(message))
        except:
            traceback.print_exc()

    def critical(self, message, tag="UsbHubController", sn=None):
        try:
            if sn is not None:
                self.logger.critical(tag + " --- [{}] --- {}".format(sn, message))
            else:
                self.logger.critical(tag + " --- {}".format(message))
        except:
            traceback.print_exc()


# if not os.path.isdir(LOG_ROOT_DIR):
#     os.makedirs(LOG_ROOT_DIR)
# loggerName = datetime.datetime.now().strftime("UsbHubController_%Y_%m_%d.log")
# loggerPath = os.path.join(LOG_ROOT_DIR, loggerName)
# logger = Logger(loggerPath)