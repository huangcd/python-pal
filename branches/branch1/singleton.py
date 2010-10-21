#!/usr/bin/env python
# -*- coding: UTF-8 -*-
def singleton(cls):
    '''
    singleton 模式的修饰器，保留第一次初始化的值
    例：
    @singleton
    class Class:
        def __init__(self, v):
            self.val = v
    a = Class('a')
    b = Class('b')
    则b.val == 'a'
    a is b返回True
    '''
    instance_container = []
    def get_instance(*arg, **args):
        if not len(instance_container):
            instance_container.append(cls(*arg, **args))
        return instance_container[0]
    return get_instance
