#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''
Created on 2010-7-21
@author: huangcd.thu@gmail.com
'''
from threading import Thread
from time import clock
from mkf import Ball, RGM, Midi, GOPS, Fire, F, ABC, MGO, YJ1Decoder, FBP, RNG,\
    MAP
import os
import pygame
import Image
import ImageDraw

def test(func):
    def __func(*arg, **args):
        start = clock()
        func(*arg, **args)
        print 'total time used: %fs' % (clock() - start)
    return __func


class MidiPlayer(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.midi = Midi()

    def run(self):
        i = 0
        while 1:
            try:
                self.midi.play(i)
                i += 1
            except:
                i = 0

def play_midi_in_loop():
    MidiPlayer().start()

@test
def test_ball():
    b = Ball()
    for i in xrange(b.count):
        img = b.getImage(i, 0)
        img.save(r'.\ball\%d.png' % i, 'PNG')

@test
def test_rgm():
    r = RGM()
    for i in xrange(r.count):
        img = r.getImage(i, 0)
        if img:
            img.save(r'.\rgm\%d.png' % i, 'PNG')

@test
def test_gop():
    g = GOPS()
    path = r'.\gop'
    if not os.path.exists(path): os.mkdir(path)
    for i, gop in enumerate(g.subPlaces):
        if not os.path.exists(r'%s\%d' % (path, i)): os.mkdir(r'%s\%d' % (path, i))
        for j in xrange(gop.count):
            img = gop.getImage(j, 0)
            if img:
                img.save(r'%s\%d\%d.png' % (path, i, j), 'PNG')

@test
def show_image_using_pygame():
    b = Ball()
    pygame.init()
    screen = pygame.display.set_mode((640, 360), 0, 32)
    img = b.getImage(10, 1)
    sth = pygame.image.fromstring(img.tostring(), img.size, img.mode).convert_alpha()
    flag = False
    while True: 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                flag = True
                break
        if flag: break
        screen.fill((255, 255, 255))
        screen.blit(sth, (0, 0))
        pygame.display.update()

@test
def test_fire():
    f = Fire()
    path = r'.\fire'
    if not os.path.exists(path): os.mkdir(path)
    for i, fire in enumerate(f.subPlaces):
        if not os.path.exists(r'%s\%d' % (path, i)): os.mkdir(r'%s\%d' % (path, i))
        for j in xrange(fire.count):
            img = fire.getImage(j, 0)
            if img:
                img.save(r'%s\%d\%d.png' % (path, i, j), 'PNG')
            
@test
def test_f():
    f = F()
    path = r'.\f'
    if not os.path.exists(path): os.mkdir(path)
    for i, _f in enumerate(f.subPlaces):
        if not os.path.exists(r'%s\%d' % (path, i)): os.mkdir(r'%s\%d' % (path, i))
        for j in xrange(_f.count):
            img = _f.getImage(j, 0)
            if img:
                img.save(r'%s\%d\%d.png' % (path, i, j), 'PNG')
                
@test
def test_ABC():
    f = ABC()
    path = r'.\abc'
    if not os.path.exists(path): os.mkdir(path)
    for i, _f in enumerate(f.subPlaces):
        if not os.path.exists(r'%s\%d' % (path, i)): os.mkdir(r'%s\%d' % (path, i))
        for j in xrange(_f.count):
            img = _f.getImage(j, 0)
            if img:
                img.save(r'%s\%d\%d.png' % (path, i, j), 'PNG')
                
@test
def test_MGO():
    f = MGO()
    path = r'.\mgo'
    if not os.path.exists(path): os.mkdir(path)
    for i, _f in enumerate(f.subPlaces):
        if not os.path.exists(r'%s\%d' % (path, i)): os.mkdir(r'%s\%d' % (path, i))
        for j in xrange(_f.count):
            img = _f.getImage(j, 0)
            if img:
                img.save(r'%s\%d\%d.png' % (path, i, j), 'PNG')

@test
def debug_yj1():
    path = "D:\\programming\\pypal\\fire\\11.dat"
    with open(path, 'rb') as f: data = f.read()
    yj1 = YJ1Decoder()
    yj1.vec = []
    try:
        yj1.decode(data)
    except:
        print yj1.vec
    pass

@test
def test_FBP():
    obj = FBP()
    path = r'.\fbp'
    if not os.path.exists(path): os.mkdir(path)
    for i in xrange(obj.count):
        if i == 63:
            img = obj.getImage(i, 9)
            img.save(r'%s\%d.png' % (path, i), 'PNG')

@test
def test_RNG():
    f = RNG()
    path = r'.\rng'
    if not os.path.exists(path): os.mkdir(path)
    for i in xrange(f.count):
        if not os.path.exists(r'%s\%d' % (path, i)): os.mkdir(r'%s\%d' % (path, i))
        f.startVideo(i, 0)
        print f.video.count
        while f.hasNextFrame():
            print f.frameIndex
            img = f.getNextFrame()
            img.save(r'%s\%d\%s.png' % (path, i, str(f.frameIndex).zfill(10)), 'PNG')

@test
def test_imageData():
    obj = FBP()
    data = obj.getImageData(2, 0)

    img = Image.new('RGBA', (320, 200), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    for y in xrange(47):
        for x in xrange(48):
            if data[y][x]:
                dr.point((x, y), data[y][x])
    #img.show()

@test
def test_map():
    obj = MAP()
    path = r'.\map'
    if not os.path.exists(path): os.mkdir(path)
    for i in xrange(obj.count):
        print i
        img = obj.getMap(i, 0)
        img.save(r'%s\%d.png' % (path, i), 'PNG')
        
@test
def test_all(show):
    @test
    def tt_abc(show):     
        print 'test abc'
        obj = ABC()
        img = obj.getImage(1, 0, 0)
        if show: img.show()
    #tt_abc(show)
    
    @test
    def tt_ball(show):
        print 'test ball'
        obj = Ball()
        img = obj.getImage(2, 0)
        if show: img.show()
    tt_ball(show)
    
    @test
    def tt_f(show):
        print 'test f'
        obj = F()
        img = obj.subPlaces[0].getImage(0, 0)
        if show: img.show()
    tt_f(show)
    
    @test
    def tt_fbp(show):
        print 'test fbp'
        obj = FBP()
        img = obj.getImage(0, 0)
        if show: img.show()
    tt_fbp(show)
    
    @test
    def tt_fire(show):
        print 'test fire'
        obj = Fire()
        img = obj.subPlaces[0].getImage(0, 0)
        if show: img.show()
    tt_fire(show)
    
    @test
    def tt_gop(show):
        print 'test gop'
        obj = GOPS()
        img = obj.subPlaces[1].getImage(0, 0)
        if show: img.show()
    tt_gop(show)
    
    @test
    def tt_mgo(show):
        print 'test mgo'
        obj = MGO()
        img = obj.subPlaces[2].getImage(1, 0)
        if show: img.show()
    tt_mgo(show)
    
    @test
    def tt_rgm(show):
        print 'test rgm'
        obj = RGM()
        img = obj.getImage(2, 0)
        if show: img.show()
    tt_rgm(show)
    
    @test
    def tt_rng(show):
        print 'test rng'
        obj = RNG()
        obj.startVideo(1, 0)
        img = obj.getNextFrame()
        if show: img.show()
    tt_rng(show)
    
    @test
    def tt_midi(show):
        print 'test midi'
        obj = Midi()
        if show: obj.play(10, 20)
    tt_midi(show)
        

if __name__ == '__main__':
    os.chdir(r'..\..')
    test_all(False)
