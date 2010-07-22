#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''
Created on 2010-7-21
@author: huangcd.thu@gmail.com
'''
from mkf import *

if __name__ == '__main__':
    f = MKFDecoder('fire.mkf')
    yj1 = YJ1Decoder()
    if not os.path.exists(r'.\fire'): os.makedirs(r'.\fire')
    for i in xrange(f.count):
        data = f.read(i)
        print len(data)
        if data:
            with open(r'.\fire\%d.dat' % i, 'wb') as fi: fi.write(yj1.decode(f.read(i))) 
    #sys.exit(0)
    #print dir()
    #g = GOPS()
    #path = r'.\gop'
    #if not os.path.exists(path): os.mkdir(path)
    #for i, gop in enumerate(g.subPlaces):
    #    if not os.path.exists(r'%s\%d' % (path, i)): os.mkdir(r'%s\%d' % (path, i))
    #    for j in xrange(gop.count):
    #        img = gop.getImage(j, 0)
    #        if img:
    #            img.save(r'%s\%d\%d.png' % (path, i, j), 'PNG')
    #midi = Midi()
    #for i in xrange(midi.count):
    #    midi.save(i, r'.\midi\%d.mid' % i)
    #if len(sys.argv) > 1:
    #    midi.play(int(sys.argv[1]))
    #else:
    #    midi.play(1)
    #time.clock()
    #r = RGM()
    #for i in xrange(r.count):
    #    img = r.getImage(i, 0)
    #    if img:
    #        img.save(r'.\rgm\%d.png' % i, 'PNG')
    #g = RGM()
    #for i in xrange(g.count):
    #    with open(r'.\rgm\%d.dat' % i, 'wb') as f:
    #        f.write(g.read(i))
    sys.exit()
    #b = Ball()

    #for i in xrange(b.decoder.count):
    #    img = b.getImage(i, 0)
    #    img.save(r'.\rle\%d.png' % i, 'PNG')
    #print time.clock()
    class T(Thread):
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

    T().start()
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
    #for i in xrange(b.decoder.count - 1):
    #    with open(r'.\rle\%d.rle' % i, 'wb') as f: f.write(b.decoder.read(i))
    #p = Palettes()
    #print p.getColor(0, 90)
    pass
