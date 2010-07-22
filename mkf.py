#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''
Created on 2010-7-19
@author: huangcd.thu@gmail.com
'''

import os, struct, sys, time
import pygame
from singleton import singleton
from struct import unpack
from PIL import Image, ImageDraw

class MKFDecoder:
    '''
    MKF文件解码《仙剑》MKF文件的结构组成，以ABC.MKF为例：
    偏移         数据            含义
    00000000     6C 02 00 00     偏移表的长度，此值 / 4 - 2 = 包含文件个数
    00000004     6C 02 00 00     第1个子文件的偏移
    　     　                    第2-152个子件的偏移
    00000264     C2 6F 0F 00     第153个子文件的偏移
    00000268     64 9A 0F 00     此值指向文件末尾，也就是文件的长度
    0000026C     59 4A 5F 31     第1个子文件从这里开始，"YJ_1"是压缩文件的标志
    00000270     A0 08 00 00     这个值是文件的原始的长度
    00000274     12 07 00 00     这个值是文件压缩后的长度
    00000278     01 00           这个值是文件压缩占64K段的个数，通常为1
    0000027A     00 4A           这个值是数据压缩特征串表的长度
    0000027C     01 02 。。      从这开始是数据压缩特征串表
    000002C4     87 7B 02 4C     从这开始是压缩后的文件数据
    　     　                    其他压缩文件
    000F9A60     0B 12 80 38     文件的末尾
    '''

    def __init__(self, path):
        try:
            
            f = open(path, 'rb')
            self.content = f.read()
            #===================================================================
            # 偏移（索引）表长度，假设文件前4位为6C 02 00 00（little-end的int值为
            # 26CH = 620），说明索引表长度为620字节，即620/4 = 155个整数，由于第一个
            # 整数被用于存储表长度，因此实际上只有后面154个整数存的是偏移量。另一方面，
            # 最后一个整数指向文件末尾，也就是文件的长度，因此实际上MKF内部的文件是由
            # 前后两个偏移量之间的byte表示的。这样由于一共有154个个偏移量，因此共有
            # 153个文件
            # ！！！补充：第一个int（前四位）不仅是偏移表长度，也是第一个文件的开头
            # ABC.MFK中前面两个4位分别相等只是巧合（第一个文件为0）
            #
            #===================================================================
            self.count = unpack('I', self.content[:4])[0] / 4# - 1
            self.indexes = []
            self.cache = {}
            for i in xrange(self.count):
                index = unpack('I', self.content[(i) << 2: (i + 1) << 2])[0]
                self.indexes.append(index)
            # 减去最后一个偏移量，对外而言，count就表示mkf文件中的子文件个数
            self.count -= 1
        except IOError:
            print 'error occurs when try to open file', path
        finally:
            if 'f' in dir():
                f.close()

    def check(self, index):
        assert index <= self.count and index >= 0

    def isYJ1(self, index):
        '''
        判断文件是否为YJ_1压缩
        '''
        self.check(index)
        return self.content[self.indexes[index]:self.indexes[index] + 4] == '\x59\x4A\x5F\x31'

    def read(self, index):
        '''
        读取指定文件
        '''
        #self.check(index)
        self.check(index + 1)
        if not self.cache.has_key(index):
            self.cache[index] = self.content[self.indexes[index]:self.indexes[index + 1]]
        return self.cache[index]

@singleton
class YJ1Decoder:
    '''
    YJ_1文件解析
    YJ_1文件结构：
    0000000: 594a5f31 fe520000 321b0000                02（即data[0xC]) 00 00 57（即data[0xF]）
              Y J _ 1 新文件长 源文件长（包含'YJ_1'头）block数                loop数
    '''
    def __init__(self):
        self.si = 0 #source index
        self.di = 0 #dest index
        self.first = 1
        self.flags = 0
        self.flagnum = 0
        self.key_0x12 = 0
        self.key_0x13 = 0
        self.orgLen = 0
        self.fileLen = 0
        self.tableLen = 0
        self.table = []
        self.assist = []
        self.keywords = [0 for i in xrange(0x14)]
        self.data = ''
        self.finalData = []

    def decode(self, data):
        # TODO YJ_1解析
        self.si = self.di = 0 #; //记录文件位置的指针 记录解开后保存数据所在数组中的指向位置
        self.first = 1
        self.key_0x12 = self.key_0x13 = 0
        self.flags = 0
        self.flagnum = 0        

        pack_length = 0
        ext_length = 0
        if not data:
            return
        self.data = data
        tag = self.readInt()
        print hex(tag)
        if tag != 0x315f4a59:
            return
        self.orgLen = self.readInt()
        self.fileLen = self.readInt()
        self.finalData = [0 for i in xrange(0x10000)]
        prev_src_pos = self.si
        prev_dst_pos = self.di
        blocks = self.readByte(0xC)
        
        self.expand()

        prev_src_pos = self.si
        self.di = prev_dst_pos
        for i in xrange(blocks):
            if self.first == 0:
                prev_src_pos += pack_length
                prev_dst_pos += ext_length
                self.si = prev_src_pos
                self.di = prev_dst_pos
            first = 0
            
            ext_length = self.readShort()
            pack_length = self.readShort()

            if pack_length == 0:
                pack_length = ext_length + 4
                for j in xrange(ext_length):
                    self.finalData[self.di] = self.data[self.si]
                    di += 1
                    si += 1
                ext_length = pack_length - 4
            else:
                d = 0
                for j in xrange(0x14):
                    self.keywords[d] = self.readByte()
                    d += 1
                self.key_0x12 = self.keywords[0x12]
                self.key_0x13 = self.keywords[0x13]
                
                self.flagnum = 0x20
                self.flags = ((self.readShort() << 16) | self.readShort()) & 0xffffffffL
                self.analysis()
            return ''.join([x for x in self.finalData if x != 0])

    def analysis(self):
        loop = 0
        numbytes = 0
        while True:
            loop = self.decodeloop()
            if loop == 0xffff:
                return
            for i in xrange(loop):
                m = 0
                self.update(0x10)
                while True:
                    m = self.trans_topflag_to(m, self.flags, self.flagnum, 1)
                    self.flags = (self.flags << 1) & 0xffffffffL
                    self.flagnum -= 1
                    if self.assist[m] == 0:
                        break
                    m = self.table[m]
                self.finalData[self.di] = chr(self.table[m] & 0xff)
                self.di += 1
            loop = self.decodeloop()
            if loop == 0xffff:
                return
            for i in xrange(loop):
                numbytes = self.decodenumbytes()
                self.update(0x10)
                print m, self.flags, self.flagnum, 2
                m = self.trans_topflag_to(0, self.flags, self.flagnum, 2)
                self.flags = (self.flags << 2) & 0xffffffffL
                print m
                t = self.keywords[m + 8]
                n = self.trans_topflag_to(0, self.flags, self.flagnum, t)
                self.flags = (self.flags << t) & 0xffffffffL
                self.flagnum -= t
                for i in xrange(numbytes):
                    self.finalData[self.di] = self.finalData[self.di - n]
                    self.di += 1

    def readShort(self, si = None):
        if si:
            self.si = si
        result, = unpack('H', self.data[self.si : self.si + 2])
        self.si += 2
        return result

    def readByte(self, si = None):
        if si:
            self.si = si
        result, = unpack('B', self.data[self.si])
        self.si += 1
        return result

    def readInt(self, si = None):
        if si:
            self.si = si
        result, = unpack('I', self.data[self.si : self.si + 4])
        self.si += 4
        return result

    def move_top(self, x):
        t = x >> 15
        return t & 0xffff

    def get_topflag(self, x, y):
        t = x >> 31
        return t & 0xffffffff
    
    def trans_topflag_to(self, x, y, z, n):
        for i in xrange(n):
            x <<= 1
            x |= self.get_topflag(y, z)
            y  = (y << 1) & 0xffffffff
            z -= 1
        return x & 0xffffffff

    def update(self, x):
        if self.flagnum < x:
            self.flags |= self.readShort() << (0x10 - self.flagnum) & 0xffffffffL
            self.flagnum += 0x10
            
    def decodeloop(self):
        self.update(3)
        loop = self.key_0x12
        if self.get_topflag(self.flags, self.flagnum) == 0:
            self.flags = (self.flags << 1) & 0xffffffffL
            self.flagnum -= 1
            t = 0
            t = self.trans_topflag_to(t, self.flags, self.flagnum, 2)
            self.flags = (self.flags << 2) & 0xffffffffL
            self.flagnum -= 2
            loop = self.key_0x13
            if t != 0:
                t = self.keywords[t + 0xE]
                self.update(t)
                loop = self.trans_topflag_to(0, self.flags, self.flagnum, t)
                if loop == 0:
                    self.flags = (self.flags << t) & 0xffffffffL
                    self.flagnum -= t
                    return 0xffff
                else:
                    self.flags = (self.flags << t) & 0xffffffffL
                    self.flagnum -= t
        else:
            self.flags = (self.flags << 1) & 0xffffffffL
            self.flagnum -= 1
        return loop

    def decodenumbytes(self):
        self.update(3)
        numbytes = self.trans_topflag_to(0, self.flags, self.flagnum, 2)
        if numbytes == 0:
            self.flags = (self.flags << 2) & 0xffffffffL
            self.flagnum -= 2
            numbytes = (self.keywords[1] << 8) | self.keywords[0]
        else:
            self.flags = (self.flags << 2) & 0xffffffffL
            self.flagnum -= 2
            if self.get_topflag(self.flags, self.flagnum) == 0:
                self.flags = (self.flags << 1) & 0xffffffffL
                self.flagnum -= 1
                numbytes = (self.keywords[numbytes * 2 + 1] << 8) | self.keywords[numbytes * 2]
            else:
                self.flags = (self.flags << 1) & 0xffffffffL
                self.flagnum -= 1
                t = self.keywords[numbytes + 0xB]
                self.update(t)
                numbytes = 0
                numbytes = self.trans_topflag_to(numbytes, self.flags, self.flagnum, t)
                self.flags = (self.flags << t) & 0xffffffffL
                self.flagnum -= t
        return numbytes
                

    def expand(self):
        loop = self.readByte(0xF)
        offset, flags = 0, 0
        self.di = self.si
        self.si += 2 * loop
        self.table = []
        self.assist = []
        for i in xrange(loop):
            if offset % 16 == 0:
                flags = self.readShort()
            self.table.append(unpack('B', self.data[self.di])[0])
            self.table.append(unpack('B', self.data[self.di + 1])[0])
            self.di += 2
            self.assist.append(self.move_top(flags))
            flags = (flags << 1) & 0xffff
            self.assist.append(self.move_top(flags))
            flags = (flags << 1) & 0xffff
            offset += 2

@singleton
class Midi(MKFDecoder):
    '''
    midi.mkf文件解码和midi音乐播放
    调用pygame实现播放功能
    待改进：测试clock时候能和其它地方的clock兼容
    '''
    def __init__(self):
        MKFDecoder.__init__(self, 'midi.mkf')
        self.clock = pygame.time.Clock()
        pygame.mixer.init()

    def save(self, index, path):
        with open(path, 'wb') as f:
            f.write(self.read(index))

    def play(self, index, ticks = 20):
        '''
        播放midi.mkf文件中的midi音乐
        @param index: midi音乐索引
        @param ticks: clock的tick参数
        '''
        name = 'tmp.mid'
        save(self, index, name)
        pygame.mixer.music.load(name)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            self.clock.tick(ticks)
        os.remove(name)

    def stop(self, index):
        pygame.mixer.music.stop()

class RLEDecoder(MKFDecoder):
    '''
    RLE图片解析
    '''
    def __init__(self, path):
        MKFDecoder.__init__(self, path)        
        self.palette = Palettes()

    def getSize(self, index):
        data = self.read(index)
        if len(data) < 8:
            return (0, 0)
        return unpack('HH', data[4:8])

    def getImage(self, index, pIndex):
        '''
        返回给定调色板之后渲染出来的道具图片
        @param index：图片索引
        @param pIndex: 调色板索引
        '''
        width, height = self.getSize(index)
        if not width or not height: 
            return None
        img = Image.new('RGBA', self.getSize(index), (0, 0, 0, 0))
        dr = ImageDraw.Draw(img)
        # 一次unpack所有数据
        _data = self.read(index)
        data = unpack('B' * len(_data), _data)
        offset = 8
        line = 0
        x = 0
        palette = self.palette.getPalette(pIndex)
        while line < height:
            flag = width
            # 处理一行数据
            while flag > 0:
                num = data[offset]
                # 透明颜色个数
                if num > 0x80:
                    num -= 0x80
                    for i in xrange(num):
                        flag -= 1
                        # 透明就不用画了
                        #dr.point((x, line), (0, 0, 0, 0))
                        x += 1
                    offset += 1
                    # very special case! 
                    if num == 0x7F: continue 
                if flag == 0: break
                num = data[offset] # 不透明颜色个数
                offset += 1
                for k in xrange(num):
                    dr.point((x, line), palette[data[offset + k]])
                    x += 1
                offset += num
                flag -= num
            line += 1
            x = 0
        return img

@singleton
class Ball(RLEDecoder):
    '''
    物品图片档，经过MKF解开后，每个子文件是标准的RLE图片（ball.mfk）
    '''
    def __init__(self):
        RLEDecoder.__init__(self, 'ball.mkf')

@singleton
class RGM(RLEDecoder):
    '''
    人物头像档，经过MKF解开后，每个子文件是标准的RLE图片（RGM.mkf）
    '''
    def __init__(self):
        RLEDecoder.__init__(self, 'RGM.mkf')

class SubPlace(RLEDecoder):
    '''
    图元包，每个图元均为RLE，形状是菱形，而且其大小为32*15像素
    这里RLEDecoder仅仅是为了使用MKFDecoder和RLEDecoder中的方法，
    而不调用RLEDecoder.__init__或者MKFDecoder.__init__方法
    '''
    def __init__(self, data):
        self.content = data
        self.len = len(data)
        if self.len < 2:
            self.count = 0
        else:
            self.count, = unpack('H', data[:2])
        self.indexes = map(lambda x: x or self.len, unpack('H' * self.count, data[ : self.count << 1]))
        self.count -= 1
        self.cache = {}
        self.palette = Palettes()

    def read(self, index):
        '''
        覆盖MKFDecoder的read方法
        '''
        #self.check(index)
        self.check(index + 1)
        if not self.cache.has_key(index):
            data = self.content[self.indexes[index] << 1:self.indexes[index + 1] << 1]
            self.cache[index] = data[:4] + data
        return self.cache[index]

@singleton
class Fire(MKFDecoder):
    '''
    法术效果图，同GOP有着同样的存储方式，但图元包经过YJ_1压缩（FIRE.mkf）
    '''
    def __init__(self):
        # TODO fire.mkf似乎不能用GOPLike解析
        MKFDecoder.__init__(self, 'fire.mkf')
        self.subPlaces = []
        for i in xrange(self.count):
            data = self.read(i)
            self.subPlaces.append(RLEDecoder(data))


class GOPLike(MKFDecoder):
    '''
    类GOP.MKF的存储格式的mkf文件的解码器
    GOP文件结构：（gop.mkf)
    图元集，GOP属于子包结构，其中有226个图元包,其内每个图元均为RLE，形状是菱形，而且其大小为32*15像素
     '''
    def __init__(self, path):
        MKFDecoder.__init__(self, path)
        self.subPlaces = []
        for i in xrange(self.count):
            data = self.read(i)
            self.subPlaces.append(SubPlace(data))

    def getImage(self, fIndex, index, pIndex):
        '''
        @param fIndex：子文件索引
        @param index: 图片索引
        @param pIndex: 调色板索引
        '''
        return self.subPlaces[fIndex].getImage(index, pIndex)

@singleton
class GOPS(GOPLike):
    '''
    图元集，GOP属于子包结构，其中有226个图元包,其内每个图元均为RLE，形状是菱形，而且其大小为32*15像素
    （gop.mkf)
    '''
    def __init__(self):
        GOPLike.__init__(self, 'gop.mkf')

@singleton
class Palettes: 
    '''
    pat.mkf文件不同于其它.mkf文件，其文件的组织结构为从0x28开始，每768字节构成一个子文件，
    共有11个子文件，在这768字节中，其按照Red、 Green、Blue颜色分量进行存储，共有256组颜色
    分量，正好构成游戏中所需要的256色的调色板。不过有一点需要注意的是，由于仙剑在开发的年
    代比较早，因此那是的颜色数量远没有现在的24位色这么多，当时是每一个字节的低6位表示颜色，
    高2位没有使用，所以我们在进行转换的过程中，必须将颜色分量须右移2位。如下：
    color = [Red << 2] | [Green << 2] | [Blue << 2]; 
    '''
    def __init__(self):
        try:
            f = open('pat.mkf', 'rb')
            self.content = f.read()
            self.offset = 0x28
            self.maxIndex = 11
            self.fileSize = 0x300
            self.alpha = 0
            # 新建一个数组保存11个调色板文件（每个调色板256种颜色）
            self.palettes = [[None for j in xrange(self.fileSize / 3)] for i in xrange(self.maxIndex)]
            for i in xrange(self.maxIndex):
                offset = self.offset + i * self.fileSize
                for j in xrange(self.fileSize / 3):
                    # RGB
                    self.palettes[i][j] = tuple(map(lambda x: x << 2, unpack('BBB', self.content[offset:offset + 3])))
                    offset += 3
        except IOError:
            print 'error occurs when try to open file', path
        finally:
            f.close()

    def check(self, pIndex, cIndex = 0):
        assert pIndex < self.maxIndex and pIndex >= 0
        assert cIndex < self.fileSize / 3 and cIndex >= 0

    def getPalette(self, index):
        self.check(index)
        return self.palettes[index]

    def getColor(self, pIndex, cIndex):
        self.check(pIndex, cIndex)
        return self.palettes[pIndex][cIndex]

