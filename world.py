import struct
from numpy import uint8, zeros
from gzip import GzipFile
from StringIO import StringIO
from constants import Blocks
from random import randint
from math import floor, sin, cos, radians

class World:
    def __init__(self, name):
        self.x, self.y, self.z = 256, 64, 256
        self.blocks = zeros((self.y, self.z, self.x), dtype=uint8)
        try:
            self.load()
        except IOError:
            self.create()
    
    def create(self):
        #offsets = [(randint(-180,180),randint(10,60)) for i in range(8)]
        for x in range(self.x):
            for z in range (self.z):
                #noise = 0
                #for i in offsets:
                #    noise += sin(radians((x+i[0])*i[1]))
                #    noise += cos(radians((z+i[0])*i[1]))
                #noise /= len(offsets)
                #height = int(self.y//2 + self.y//16*noise)
                height = self.y//2
                for y in range(height):
                    btype = Blocks["Dirt"] if y < height-1 else Blocks["Grass"]
                    self.block(x,y,z, btype)
    
    def load(self):
        raise IOError()
    
    def block(self, x, y, z, block=None):
        if block:
            self.blocks[y][z][x] = block
        else:
            return self.blocks[y][z][x]
        
    def gzip(self, numblocks=False):
        out = StringIO()
        gz = GzipFile("level.dat","wb",9,out)
        if numblocks:
            gz.write(struct.pack(">I",self.x*self.y*self.z))
        gz.write(self.blocks.tostring())
        gz.close()
        gzipped = out.getvalue()
        out.close()
        return gzipped
