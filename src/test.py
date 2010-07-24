#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''
Created on 2010-7-21
@author: huangcd.thu@gmail.com
'''
from mkf import *
from threading import Thread
from time import clock

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
def test_palette():
    p = Palettes()
    print p.getColor(0, 90)

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
    import pygame
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
    from PIL import Image, ImageDraw
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

if __name__ == '__main__':
    import os
    os.chdir(r'..')
    test_rgm()
