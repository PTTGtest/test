# coding:utf-8

# @File: HelloWorld.py
# @Author: 含光
# @description:
# @Time: 2022年08月31日


class HelloWorld():

    def __init__(self, string):
        self.string = string

    def hello_world(self):
        print(self.string)

    Numbers = 65
    String = "a"
    List = [1, 2, 3]
    Tuple = (1, 2, 3)
    Dictionary = {"a": 65, "b": 66}



if __name__ == '__main__':

    demo = HelloWorld("hello world")
    demo.hello_world()




