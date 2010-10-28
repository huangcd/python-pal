#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''
Created on 2010-10-21
@author: huangcd.thu@gmail.com
'''

from struct import unpack, pack

class Setup:
    """
    处理SETUP.DAT文件中的配置信息
    """
    def __init__(self):
        '''
        init
        '''
        self.key_leftup      = None
        self.key_rightup     = None
        self.key_rightdown   = None
        self.key_leftdown    = None
        self.music           = None
        self.sound           = None
        self.irq             = None
        self.io_port         = None
        self.midi            = None
        self.use_files_on_cd = None

    def decode(self):
        '''
        decode information from file SETUP.DAT
        '''
        with open('SETUP.DAT', 'r') as handle:
            content = handle.read()
            self.key_leftup,    self.key_rightup,  self.key_rightdown, \
            self.key_leftdown,  self.music,        self.sound,         \
            self.irq,           self.io_port,      self.midi,          \
            self.use_files_on_cd                                       \
            = unpack(r'H' * 7 + 'H' * 3, content)

    def encode(self):
        '''
        encode information to file SETUP.DAT
        '''
        with open('SETUP.DAT', 'w') as handle:
            content = pack(r'H' * 7 + 'H' * 3,                         \
            self.key_leftup,    self.key_rightup,  self.key_rightdown, \
            self.key_leftdown,  self.music,        self.sound,         \
            self.irq,           self.io_port,      self.midi,          \
            self.use_files_on_cd                                       )
            handle.write(content)
