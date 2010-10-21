#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''
Created on 2010-10-21
@author: huangcd.thu@gmail.com
'''

from struct import unpack, pack
"""
处理SETUP.DAT文件中的配置信息
"""
class Setup:
    def decode(self):
        with open('SETUP.DAT', 'r') as f:
            content = f.read()
            self.key_leftup,    self.key_rightup,  self.key_rightdown, \
            self.key_leftdown,  self.music,        self.sound,         \
            self.IRQ,           self.IOPort,       self.MIDI,          \
            self.use_files_on_CD                                       \
            = unpack(r'H' * 7 + 'H' * 3, content)

    def encode(self):
        with open('SETUP.DAT', 'w') as f:
            content = pack(r'H' * 7 + 'H' * 3,                         \
            self.key_leftup,    self.key_rightup,  self.key_rightdown, \
            self.key_leftdown,  self.music,        self.sound,         \
            self.IRQ,           self.IOPort,       self.MIDI,          \
            self.use_files_on_CD                                       )
            f.write(content)
