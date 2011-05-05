#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''
Created on 2010-7-19
@author: huangcd.thu@gmail.com
'''

import os
import pygame
#from singleton import singleton
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

    def __init__(self, path = None, data = None):
        # path和data不能同时是None
        assert path or data
        self.yj1 = YJ1Decoder()
        try:
            # 优先使用path（优先从文件读取）
            if path:
                f = open(path, 'rb')
                self.content = f.read()
            else:
                self.content = data
            #===================================================================
            # 偏移（索引）表长度，假设文件前4位为6C 02 00 00（little-end的int值为
            # 26CH = 620），说明索引表长度为620字节，即620/4 = 155个整数，由于第一个
            # 整数被用于存储表长度，因此实际上只有后面154个整数存的是偏移量。另一方面，
            # 最后一个整数指向文件末尾，也就是文件的长度，因此实际上MKF内部的文件是由
            # 前后两个偏移量之间的byte表示的。这样由于一共有154个个偏移量，因此共有
            # 153个文件
            #
            # ！！！补充：第一个int（前四位）不仅是偏移表长度，也是第一个文件的开头
            # ABC.MFK中前面两个4位分别相等只是巧合（第一个文件为0）
            #===================================================================
            self.count = unpack('I', self.content[:4])[0] / 4# - 1
            self.indexes = []
            self.cache = {}
            for i in xrange(self.count):
                index = unpack('I', self.content[i << 2: (i + 1) << 2])[0]
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
            
    def getFileCount(self):
        return self.count

    def isYJ1(self, index):
        '''
        判断文件是否为YJ_1压缩
        '''
        self.check(index)
        return self.content[self.indexes[index]:self.indexes[index] + 4] == '\x59\x4A\x5F\x31'

    def read(self, index):
        '''
        读取并返回指定文件，如果文件是经过YJ_1压缩的话，返回解压以后的内容
        '''
        self.check(index + 1)
        if not self.cache.has_key(index):
            data = self.content[self.indexes[index]:self.indexes[index + 1]]
            if self.isYJ1(index):
                data = self.yj1.decode(data)
            self.cache[index] = data
        return self.cache[index]

#@singleton
class YJ1Decoder:
    '''
    YJ_1文件解析
    YJ_1文件结构：
    0000000: 594a5f31 fe520000 321b0000                02（即data[0xC]) 00 00 57（即data[0xF]）
              Y J _ 1 新文件长 源文件长（包含'YJ_1'头）block数                loop数
    '''
    def __init__(self):
        pass

    def decode(self, data):
        '''
        解析YJ_1格式的压缩文件，如果文件不是YJ_1格式或者文件为空，则直接返回原始数据
        '''
        self.si = self.di = 0 #记录文件位置的指针 记录解开后保存数据所在数组中的指向位置
        self.first = 1
        self.key_0x12 = self.key_0x13 = 0
        self.flags = 0
        self.flagnum = 0

        pack_length = 0
        ext_length = 0
        if not data:
            print 'no data to decode'
            return ''
        self.data = data
        self.dataLen = len(data)
        if self.readInt() != 0x315f4a59: # '1' '_' 'J' 'Y'
            print 'not YJ_1 data'
            return data
        self.orgLen = self.readInt()
        self.fileLen = self.readInt()
        self.finalData = ['\x00' for _ in xrange(self.orgLen)]
        self.keywords = [0 for _ in xrange(0x14)]

        prev_src_pos = self.si
        prev_dst_pos = self.di

        blocks = self.readByte(0xC)
        
        self.expand()

        prev_src_pos = self.si
        self.di = prev_dst_pos
        for _ in xrange(blocks):
            if self.first == 0:
                prev_src_pos += pack_length
                prev_dst_pos += ext_length
                self.si = prev_src_pos
                self.di = prev_dst_pos
            self.first = 0
            
            ext_length = self.readShort()
            pack_length = self.readShort()

            if not pack_length:
                pack_length = ext_length + 4
                for _ in xrange(ext_length):
                    self.finalData[self.di] = self.data[self.si]
                    self.di += 1
                    self.si += 1
                ext_length = pack_length - 4
            else:
                d = 0
                for _ in xrange(0x14):
                    self.keywords[d] = self.readByte()
                    d += 1
                self.key_0x12 = self.keywords[0x12]
                self.key_0x13 = self.keywords[0x13]
                self.flagnum = 0x20
                self.flags = ((self.readShort() << 16) | self.readShort()) & 0xffffffff
                self.analysis()

        return ''.join([x for x in self.finalData if x != 0])

    def analysis(self):
        loop = 0
        numbytes = 0
        while True:
            loop = self.decodeloop()
            if loop == 0xffff:
                return
            for _ in xrange(loop):
                m = 0
                self.update(0x10)
                while True:
                    m = self.trans_topflag_to(m, self.flags, self.flagnum, 1)
                    self.flags = (self.flags << 1) & 0xffffffff
                    self.flagnum -= 1
                    if self.assist[m] == 0:
                        break
                    m = self.table[m]
                self.finalData[self.di] = chr(self.table[m] & 0xff)
                self.di += 1
            loop = self.decodeloop()
            if loop == 0xffff:
                return
            for _ in xrange(loop):
                numbytes = self.decodenumbytes()
                self.update(0x10)
                m = self.trans_topflag_to(0, self.flags, self.flagnum, 2)
                self.flags = (self.flags << 2) & 0xffffffff
                self.flagnum -= 2
                t = self.keywords[m + 8]
                n = self.trans_topflag_to(0, self.flags, self.flagnum, t)
                self.flags = (self.flags << t) & 0xffffffff
                self.flagnum -= t
                for _ in xrange(numbytes):
                    self.finalData[self.di] = self.finalData[self.di - n]
                    self.di += 1

    def readShort(self, si = None):
        if si:
            self.si = si
        if self.si >= self.dataLen:
            result = 0
        else:
            result, = unpack('H', self.data[self.si : self.si + 2])
        self.si += 2
        return result

    def readByte(self, si = None):
        if si:
            self.si = si
        if self.si >= self.dataLen:
            result = 0
        else:
            result, = unpack('B', self.data[self.si])
        self.si += 1
        return result

    def readInt(self, si = None):
        if si:
            self.si = si
        if self.si >= self.dataLen:
            result = 0
        else:
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
        for _ in xrange(n):
            x <<= 1
            x |= self.get_topflag(y, z)
            y  = (y << 1) & 0xffffffff
            z -= 1
        return x & 0xffffffff

    def update(self, x):
        if self.flagnum < x:
            self.flags |= self.readShort() << (0x10 - self.flagnum) & 0xffffffff
            self.flagnum += 0x10
            
    def decodeloop(self):
        self.update(3)
        loop = self.key_0x12
        if self.get_topflag(self.flags, self.flagnum) == 0:
            self.flags = (self.flags << 1) & 0xffffffff
            self.flagnum -= 1
            t = 0
            t = self.trans_topflag_to(t, self.flags, self.flagnum, 2)
            self.flags = (self.flags << 2) & 0xffffffff
            self.flagnum -= 2
            loop = self.key_0x13
            if t != 0:
                t = self.keywords[t + 0xE]
                self.update(t)
                loop = self.trans_topflag_to(0, self.flags, self.flagnum, t)
                if loop == 0:
                    self.flags = (self.flags << t) & 0xffffffff
                    self.flagnum -= t
                    return 0xffff
                else:
                    self.flags = (self.flags << t) & 0xffffffff
                    self.flagnum -= t
        else:
            self.flags = (self.flags << 1) & 0xffffffff
            self.flagnum -= 1
        return loop

    def decodenumbytes(self):
        self.update(3)
        numbytes = self.trans_topflag_to(0, self.flags, self.flagnum, 2)
        if numbytes == 0:
            self.flags = (self.flags << 2) & 0xffffffff
            self.flagnum -= 2
            numbytes = (self.keywords[1] << 8) | self.keywords[0]
        else:
            self.flags = (self.flags << 2) & 0xffffffff
            self.flagnum -= 2
            if self.get_topflag(self.flags, self.flagnum) == 0:
                self.flags = (self.flags << 1) & 0xffffffff
                self.flagnum -= 1
                numbytes = (self.keywords[numbytes * 2 + 1] << 8) | self.keywords[numbytes * 2]
            else:
                self.flags = (self.flags << 1) & 0xffffffff
                self.flagnum -= 1
                t = self.keywords[numbytes + 0xB]
                self.update(t)
                numbytes = 0
                numbytes = self.trans_topflag_to(numbytes, self.flags, self.flagnum, t)
                self.flags = (self.flags << t) & 0xffffffff
                self.flagnum -= t
        return numbytes
                

    def expand(self):
        loop = self.readByte(0xF)
        offset, flags = 0, 0
        self.di = self.si
        self.si += 2 * loop
        self.table = []
        self.assist = []
        for _ in xrange(loop):
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

class RLEDecoder(MKFDecoder):
    '''
    RLE图片解析
    '''
    def __init__(self, path = None, data = None):
        MKFDecoder.__init__(self, path, data)
        self.palette = Palettes()

    def getSize(self, index):
        data = self.read(index)
        if len(data) < 8:
            return (0, 0)
        return unpack('HH', data[4:8])

    def getImageData(self, index, pIndex):
        '''
        返回给定调色板之后渲染出来的图片数据（每个点上要么是None，要么是一个三维RGB值）
        @param index：图片索引
        @param pIndex: 调色板索引
        '''
        width, height = self.getSize(index)
        if not width or not height:
            return None
        img = [[None for _ in xrange(width)] for _ in xrange(height)]
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
                    x += num
                    flag -= num
                    offset += 1
                    # very special case! 
                    if num == 0x7F: continue 
                if flag == 0: break
                num = data[offset] # 不透明颜色个数
                offset += 1
                for k in xrange(num):
                    img[line][x] = palette[data[offset + k]]
                    #dr.point((x, line), palette[data[offset + k]])
                    x += 1
                offset += num
                flag -= num
            line += 1
            x = 0
        return img

    def getImage(self, index, pIndex):
        '''
        返回给定调色板之后渲染出来的图片
        @param index：图片索引
        @param pIndex: 调色板索引
        '''
        width, height = self.getSize(index)
        if not width or not height: 
            return None
        data = self.getImageData(index, pIndex)
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        dr = ImageDraw.Draw(img)
        for x in xrange(width):
            for y in xrange(height):
                if data[y][x]: dr.point((x, y), data[y][x])
        return img
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
                    x += num
                    flag -= num
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

#@singleton
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
        f = open(path, 'wb')
        #with open(path, 'wb') as f:
        f.write(self.read(index))
        f.close()

    def play(self, index, ticks = 20):
        '''
        播放midi.mkf文件中的midi音乐
        @param index: midi音乐索引
        @param ticks: clock的tick参数
        '''
        name = 'tmp.mid'
        self.save(index, name)
        pygame.mixer.music.load(name)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            self.clock.tick(ticks)
        os.remove(name)

    def stop(self, index):
        pygame.mixer.music.stop()

#@singleton
class Ball(RLEDecoder):
    '''
    物品图片档，经过MKF解开后，每个子文件是标准的RLE图片（ball.mfk）
    '''
    def __init__(self):
        RLEDecoder.__init__(self, 'ball.mkf')

#@singleton
class RGM(RLEDecoder):
    '''
    人物头像档，经过MKF解开后，每个子文件是标准的RLE图片（RGM.mkf）
    '''
    def __init__(self):
        RLEDecoder.__init__(self, 'RGM.mkf')

class SubPlace(RLEDecoder):
    '''
    图元包，每个图元均为RLE，形状是菱形，而且其大小为32*15像素
    这里继承RLEDecoder仅仅是为了使用MKFDecoder和RLEDecoder中的方法，
    而不调用RLEDecoder.__init__或者MKFDecoder.__init__方法

    另外SubPlace里面不进行YJ_1的解码
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
        # TODO 考虑是否增加YJ_1解码
        self.check(index + 1)
        if not self.cache.has_key(index):
            data = self.content[self.indexes[index] << 1:self.indexes[index + 1] << 1]
            self.cache[index] = data[:4] + data
        return self.cache[index]

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

    def getImageData(self, fIndex, index, pIndex):
        '''
        @param fIndex：子文件索引
        @param index: 图片索引
        @param pIndex: 调色板索引
        '''
        return self.subPlaces[fIndex].getImageData(index, pIndex)


#@singleton
class GOPS(GOPLike):
    '''
    图元集，GOP属于子包结构，其中有226个图元包,其内每个图元均为RLE，形状是菱形，而且其大小为32*15像素
    （gop.mkf)
    '''
    def __init__(self):
        GOPLike.__init__(self, 'gop.mkf')

#@singleton
class Fire(GOPLike):
    '''
    法术效果图，同GOP有着同样的存储方式，但图元包经过YJ_1压缩（FIRE.mkf）
    '''
    def __init__(self):
        GOPLike.__init__(self, 'fire.mkf')

#@singleton
class F(GOPLike):
    '''
    我战斗形象，同GOP有着同样的存储方式，但图元包经过YJ_1压缩（F.mkf）
    '''
    def __init__(self):
        GOPLike.__init__(self, 'f.mkf')
        
#@singleton
class ABC(GOPLike):
    '''
    敌战斗形象，同GOP有着同样的存储方式，但图元包经过YJ_1压缩（ABC.mkf）
    '''
    def __init__(self):
        GOPLike.__init__(self, 'abc.mkf')
        
#@singleton
class MGO(GOPLike):
    '''
    各种人物形象，同GOP有着同样的存储方式，但图元包经过YJ_1压缩（MGO.mkf）
    '''
    def __init__(self):
        GOPLike.__init__(self, 'mgo.mkf')
        
#@singleton
class FBP(MKFDecoder):
    '''
    背景图，经过MKF解开后，每个子文件必须经过DEYJ1解压，
    解开后的大小是64000字节，用来描述战斗时的背景（320*200），
    其数据是调色板的索引。（FBP.mkf）
    '''
    def __init__(self):
        MKFDecoder.__init__(self, 'fbp.mkf')
        self.palette = Palettes()

    def getImageData(self, index, pIndex):
        palette = self.palette.getPalette(pIndex)
        data = self.read(index)
        data = unpack('B' * len(data), data)
        width, height = 320, 200
        img = [[None for _ in xrange(width)] for _ in xrange(height)]
        for y in xrange(height):
            for x in xrange(width):
                img[y][x] = palette[data[x + y * width]]
        return img

    def getImage(self, index, pIndex):
        palette = self.palette.getPalette(pIndex)
        data = self.read(index)
        data = unpack('B' * len(data), data) 
        width, height = 320, 200
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        dr = ImageDraw.Draw(img)
        for y in xrange(height):
            for x in xrange(width):
                dr.point((x, y), palette[data[x + y * width]])
        return img

#@singleton
class RNG(MKFDecoder):
    '''
    过场动画（RNG.mkf）
    RNG文件经过MKF解开后，每个子文件仍然是一个经过MKF压缩的文件，
    然后再次经过MKF解开后，其子文件是一个YJ1压缩的文件（够复杂吧，
    大量的解压缩需要高的CPU资源，仙剑在386时代就能很好的完成，呵呵，厉害）。

    以第一次解开的MKF文件为例子，假如该文件为1.RNG，
    对该文件再次进行MKF解压后，会得到若干个小的文件
    （1_01，1_02，1_03……），这些小文件中（需要再次经过DEYJ1解压），
    第一个文件通过比较大，而其后的文件比较小，这是由于其第一个文件是描述动画的第一帧，
    而以后的文件只描述在第一帧上进行变化的数据。

    在描述变化信息的文件中，由于不包含变化位置的坐标信息，
    因此也总是从动画位置的左上角（0，0）开始的，依次描述变化，
    直至无变化可描述以止则结束（因此如果当前帧和前一帧变化较大，
    则描述文件会比较大）。

    RNG图片也是320×200的
    '''
    def __init__(self):
        MKFDecoder.__init__(self, 'rng.mkf')
        self.palette = Palettes()

    def startVideo(self, index, pIndex):
        '''
        开始一段录像，返回录像的帧数
        '''
        videodata = self.read(index)
        self.video = MKFDecoder(data = videodata)
        self.frameIndex = 0
        self.pIndex = pIndex
        width, height = 320, 200
        self.image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        self.info = [0 for _ in xrange(64000)] # 320 * 200的图片
        return self.video.count

    def finishCurrentVideo(self):
        del self.video
        del self.frameIndex
        del self.image

    def getFrameCount(self):
        assert self.video
        return self.video.count

    def hasNextFrame(self):
        return self.frameIndex < self.video.count

    def readByte(self):
        v, = unpack('B', self.data[self.pos])
        self.pos += 1
        return v

    def readShort(self):
        v, = unpack('H', self.data[self.pos : self.pos + 2])
        self.pos += 2
        return v

    def setByte(self):
        self.info[self.dst_ptr] = self.readByte()
        self.dst_ptr += 1

    def blit(self):
        '''
        解开帧动画
        @param data: 字符串形式的数据
        '''
        self.dst_ptr = 0
        bdata = wdata = ddata = 0
        self.pos = 0

        while True:
            bdata = self.readByte()
            if bdata == 0x00 or bdata == 0x13:
                return self.info
            elif bdata == 0x01 or bdata == 0x05:
                pass
            elif bdata == 0x02:
                self.dst_ptr += 2
            elif bdata == 0x03:
                bdata = self.readByte()
                self.dst_ptr += (bdata + 1) << 1
            elif bdata == 0x04:
                wdata = self.readShort()
                self.dst_ptr += (wdata + 1) << 1
            elif 0x06 <= bdata <= 0x0a:
                while bdata >= 0x06:
                    self.setByte()
                    self.setByte()
                    bdata -= 1
            elif bdata == 0x0b:
                bdata = self.readByte()
                for _ in xrange(bdata + 1):
                    self.setByte()
                    self.setByte()
            elif bdata == 0x0c:
                ddata = self.readShort()
                for _ in xrange(ddata + 1):
                    self.setByte()
                    self.setByte()
            elif bdata == 0x0d:
                self.setByte()
                self.setByte()
                self.pos -= 2
                self.setByte()
                self.setByte()
            elif bdata == 0x0e:
                self.setByte()
                self.setByte()
                self.pos -= 2
                self.setByte()
                self.setByte()
                self.pos -= 2
                self.setByte()
                self.setByte()
            elif bdata == 0x0f:
                self.setByte()
                self.setByte()
                self.pos -= 2
                self.setByte()
                self.setByte()
                self.pos -= 2
                self.setByte()
                self.setByte()
                self.pos -= 2
                self.setByte()
                self.setByte()
            elif bdata == 0x10:
                self.setByte()
                self.setByte()
                self.pos -= 2
                self.setByte()
                self.setByte()
                self.pos -= 2
                self.setByte()
                self.setByte()
                self.pos -= 2
                self.setByte()
                self.setByte()
                self.pos -= 2
                self.setByte()
                self.setByte()
            elif bdata == 0x11:
                bdata = self.readByte()
                for _ in xrange(bdata + 1):
                    self.setByte()
                    self.setByte()
                    self.pos -= 2
                self.pos += 2
            elif bdata == 0x12:
                ddata = self.readShort()
                for _ in xrange(ddata + 1):
                    self.setByte()
                    self.setByte()
                    self.pos -= 2
                self.pos += 2
        return self.info

    def getNextFrame(self):
        '''
        @member data: 两次MKFDecoder加上YJ_1Decoder解析之后得到的帧信息（字符串）
        @member info: self.data经过blit处理以后的数据（Byte数组）
        '''
        self.data = self.video.read(self.frameIndex)
        # error handler
        if not self.data or not self.hasNextFrame():
            self.frameIndex += 1
            return self.image
        self.blit()
        self.frameIndex += 1
        width, height = 320, 200
        dr = ImageDraw.Draw(self.image)
        for y in xrange(height):
            for x in xrange(width):
                idx = x + y * width
                dr.point((x, y), self.palette.getColor(self.pIndex, self.info[idx]))
        return self.image

    def getCurrentFrame(self):
        return self.image

#@singleton
class MAP(MKFDecoder):
    '''
    地图档（MAP.mkf）
    
    MAP和GOP有着相同的子文件数，因此，MAP和GOP是一一对应的关系。
    MAP经过MKF解开后，其子文件采用DEYJ1方式压缩。经过DEYJ1解开后
    的文件都应该具有65536字节的大小，其具体格式如下：

    每512字节描述一行，共有128行（512*128=65536字节）。其中第一
    行中，每4个字节描述一个图元。这 4个字节中，头两个字节用来描
    述底层图片的索引，后两字节描述在该底层图片上覆盖图片的信息。
    其中图片在GOP中的索引的计算为：将高位字节的第5位移到低位字节
    的前面，形成一个9字节描述的索引，如下面的代码：

    fel = readByte(); //低字节
    felp = readByte(); //高字节
    felp >>= 4;
    felp &= 1; //取高字节的第5位的值
    elem1 = ( felp << 8) | fel; //图元在GOP中的索引

    对于覆盖层信息，索引的计算方式同上，只不过仅当索引大于0的时
    候才进行覆盖（因此并非所有地方都需要覆盖），并且覆盖的索引需
    要减去1才是覆盖层在GOP中的真正索引。

    另外需要注意的是，在同一行中，第偶数张图片的上角会与前一张图
    片的右角进行拼接，因此其显示位置为前一张图片的(x+16, y+8)的地
    方，以下是示例：

    第一行：(0, 0)(16, 8)(32, 0)(48, 8)(64, 0)......
    第二行：(0, 16)(16, 24)(32, 16)(48, 24)(64, 16)...... 
    
    地图大小是2064×2064
    '''
    def __init__(self):
        MKFDecoder.__init__(self, 'map.mkf')
        self.gop = GOPS()
        # TODO
        pass

    def getMap(self, index, pIndex):
        data = self.getMapData(index, pIndex)
        img = Image.new('RGBA', (2064, 2064), (0, 0, 0, 0))
        dr = ImageDraw.Draw(img)
        for y in xrange(2064):
            for x in xrange(2064):
                if data[y][x]:
                    dr.point((x, y), data[y][x])
        return img

    def getMapData(self, index, pIndex):
        data = self.read(index)
        img = [[None for _ in xrange(2064)] for _ in xrange(2064)]
        subPlace = self.gop.subPlaces[index]
        if not data:
            return img
        assert len(data) == 65536
        for line in xrange(128):
            for column in xrange(0, 512, 4):
                idx = line * 512 + column
                low, high = unpack('BB', data[idx:idx + 2])
                high = (high >> 4) & 0x1
                rIndex = (high << 8) | low                
                bg = subPlace.getImageData(rIndex, pIndex) 
                low, high = unpack('BB', data[idx + 2: idx + 4])
                high = (high >> 4) & 0x1
                rIndex = ((high << 8) | low) - 1
                fg = subPlace.getImageData(rIndex, pIndex) if rIndex >= 0 else None
                shiftX = column << 2
                shiftY = (line << 4) + (0 if column % 8 == 0 else 8)
                for y in xrange(15):
                    for x in xrange(32):
                        if bg[y][x]:
                            img[y + shiftY][x + shiftX] = bg[y][x]
                if fg:
                    for y in xrange(15):
                        for x in xrange(32):
                            if fg[y][x]:
                                img[y + shiftY][x + shiftX] = fg[y][x]
        return img

#@singleton
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
            print 'error occurs when try to open file pat.mkf'
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

if __name__ == '__main__':
    pass
