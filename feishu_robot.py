# coding:utf-8
# @Time     : 2023年05月09日
# @Author   : junxian.geng
# @Email    : junxian.geng@transsion.com
# @description: 发送飞书通知
import json
import sys

import requests
import argparse

FEISHU_POST_HEADERS = {'Content-Type': 'application/json'}
FEISHU_ROBOT_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/8a534987-dbdc-402a-9691-b7aba9565919"



def send_msg_by_feishu_robot(msg_title, msg_content):
    msg_dict = {
        "msg_type": "interactive",
        "card": {
            "elements": [
                {
                    "tag": "div",
                    "text":
                        {
                            "content": msg_title,
                            "tag": "plain_text"
                        }
                    },
                {
                    "tag": "div",
                    "text":
                        {
                            "content": msg_content,
                            "tag": "lark_md"
                        }
                }
            ],
            "header": {
                "title": {
                    "content": "OTA自动化实验室-挂测信息通知",
                    "tag": "plain_text"
                }
            }
        }
    }

    try:
        requests.post(url=FEISHU_ROBOT_URL, data=json.dumps(msg_dict), headers=FEISHU_POST_HEADERS, timeout=30)
    except:
        # logger.warn("发送机器人信息时发生异常")
        pass

if __name__ == '__main__':
    """
        解析输入参数，通过 -t 指定测试配置读取关键字
    """
    parser = argparse.ArgumentParser(description='OTA测试工具输入参数')

    # dest: 参数解析目的参数名
    # metavar：help显示时，用于解释 参数名, 不使用为 dest 的大写
    parser.add_argument("-title", "--msg_title", dest="msg_title", metavar="文本头", type=str, default=None, nargs='?',
                        help="发送文本标题")
    parser.add_argument("-content", "--msg_content", dest="msg_content", type=str, default=None, nargs='?',
                        metavar="发送文本内容", help='发送文本内容')

    args = parser.parse_args()

    # 确认传入项目配置关键字
    msg_title = args.msg_title
    msg_content = args.msg_content
    if msg_title is None:
        print("未指定 -title 参数，请确定配置文件标志参数")
        sys.exit()

    if msg_content is None:
        print("未指定 -content 参数，请确定配置文件标志参数")
        sys.exit()

    send_msg_by_feishu_robot(msg_title, msg_content)