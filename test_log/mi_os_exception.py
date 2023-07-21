# -*- coding: utf-8 -*-

import codecs
import json

"""
 * sprd jira 系统字段信息
 * id id信息，无特殊含义
 * Path 日志路径
 * Version apk版本号， 无法从日志中读取
 * ExpTime 异常发生时间
 * ExpClass 异常类 {"ANR, Java(JE)"}
 * ExpType 异常型 {" data_app_anr", "data_app_crash"}
 * CurProcess 进程
 * Package 包名
 * Detail 报错详情
 * Count 报错总数
 * Other 无含义，必须存在
"""


class JsonSerializableMixin:
    @classmethod
    def from_dict_kv(cls, kv_dict: dict):
        obj = cls()
        for key in obj.__dict__.keys():
            if kv_dict.get(key):
                setattr(obj, key, kv_dict.get(key))
        return obj

    @classmethod
    def from_json_string(cls, json_string: str):
        obj = cls()
        data: dict = json.loads(json_string)

        for key in obj.__dict__.keys():
            if data.get(key):
                setattr(obj, key, data.get(key))
        return obj

    def to_json_string(self):
        return json.dumps(self, default=lambda obj: obj.__dict__)


class MIJiraExp(JsonSerializableMixin):
    def __init__(self):
        self.id = 0
        self.Path = None
        self.Version = None
        self.ExpTime = None
        self.ExpClass: str = ''
        self.ExpType: str = ''
        self.CurProcess: str = ''
        self.Package: str = ''
        self.Detail = None
        self.Count = 1
        self.Other = 0

    def __eq__(self, other):
        if isinstance(other, MIJiraExp):
            return self.Package == other.Package \
                   and self.ExpType == other.ExpType \
                   and self.Version == other.Version \
                   and self.ExpClass == other.ExpClass
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.ExpType + self.CurProcess + self.Package + self.ExpClass + self.Version)

    def __repr__(self):
        exp = {'id': self.id, 'Path': self.Path, 'Version': self.Version, 'ExpTime': self.ExpTime,
               'ExpClass': self.ExpClass, 'ExpType': self.ExpType, 'CurProcess': self.CurProcess,
               'Package': self.Package, 'Detail': self.Detail, 'Count': self.Count, 'Other': self.Other}
        return json.dumps(exp)

    def __str__(self):
        return self.__repr__()


if __name__ == '__main__':
    with codecs.open('mi_jira_exceptions.json') as f:
        lines = f.read()

    exps = json.loads(lines)

    distinct_exp = set()

    for exp in exps:
        jira_exp = MIJiraExp.from_json_string(json.dumps(exp))
        print(jira_exp)
        print(distinct_exp.add(jira_exp))
