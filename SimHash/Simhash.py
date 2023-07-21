# coding:utf-8
# @Time     : 2023年06月05日
# @Author   : junxian.geng
# @Email    : junxian.geng@transsion.com
# @description:
import jieba
import numpy as np
from jieba import analyse


class Simhash:
    """经过测试和查找资料发现，Simhash更加适合文档去重，文本越短，精度缺失越厉害"""

    def __init__(self, content):
        self.simhash = self.simhash(content)

    def __str__(self):
        return str(self.simhash)

    def simhash(self, content):
        jieba.load_userdict('userdict.text')
        seg = jieba.cut(content)
        jieba.analyse.set_stop_words('testtimi.text')
        key_word = jieba.analyse.extract_tags(
            '|'.join(seg), topK=20, withWeight=True, allowPOS=())  # 在这里对jieba的tfidf.py进行了修改
        # 将tags = sorted(freq.items(), key=itemgetter(1), reverse=True)修改成tags = sorted(freq.items(), key=itemgetter(
        # 1,0), reverse=True) 即先按照权重排序，再按照词排序
        key_list = []
        # print(key_word)
        for feature, weight in key_word:
            weight = int(weight * 20)
            feature = self.string_hash(feature)
            temp = []
            for i in feature:
                if i == '1':
                    temp.append(weight)
                else:
                    temp.append(-weight)
            # print(temp)
            key_list.append(temp)
        list1 = np.sum(np.array(key_list), axis=0)
        # print(list1)
        if not key_list:  # 编码读不出来
            return '00'
        simhash = ''
        for i in list1:
            if i > 0:
                simhash = simhash + '1'
            else:
                simhash = simhash + '0'
        return simhash

    @staticmethod
    def string_hash(source):
        if source == "":
            return 0
        else:
            x = ord(source[0]) << 7
            m = 1000003
            mask = 2 ** 128 - 1
            for c in source:
                x = ((x * m) ^ ord(c)) & mask
            x ^= len(source)
            if x == -1:
                x = -2
            x = bin(x).replace('0b', '').zfill(64)[-64:]
            # print(source, x)

            return str(x)

        # 以下是使用系统自带hash生成，虽然每次相同的会生成的一样，
        # 不过，对于不同的汉子产生的二进制，在计算海明码的距离会不一样，
        # 即每次产生的海明距离不一致
        # 所以不建议使用。

        # x=str(bin(hash(source)).replace('0b','').replace('-','').zfill(64)[-64:])
        # print(source,x,len(x))
        # return x

    def hammingDis(self, com):
        t1 = '0b' + self.simhash
        t2 = '0b' + com.simhash
        n = int(t1, 2) ^ int(t2, 2)
        i = 0
        while n:
            n &= (n - 1)
            i += 1
        return i


def bubblesort(arr):
    n =len(arr)
    for i in range(n):
            for j in range(0, n-i-1):
                if arr[j] > arr[j+1]:
                    arr[j],arr[j+1] = arr[j+1],arr[j]
    return arr
