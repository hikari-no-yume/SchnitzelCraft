import struct
from numpy import uint8, zeros, fromstring, reshape
from gzip import GzipFile
from StringIO import StringIO
from constants import Blocks
from random import randint
from math import floor, sin, cos, radians

class World:
    def __init__(self, name):
        self.filename = name
        try:
            self.load()
        except IOError:
            self.create()
            self.save()
    
    def create(self):
        self.x, self.y, self.z = 256, 64, 256
        self.blocks = zeros((self.y, self.z, self.x), dtype=uint8)
        for x in range(self.x):
            for z in range (self.z):
                height = self.y//2
                for y in range(height):
                    btype = Blocks["Dirt"] if y < height-1 else Blocks["Grass"]
                    self.block(x,y,z, btype)
        print "Created World (%sx%sx%s)" % (self.x, self.y, self.z)
    
    def load(self):
        with open(self.filename, "r") as fp:
            format = ">HHH"
            size = struct.calcsize(format)
            self.x, self.y, self.z = struct.unpack(format, fp.read(size))
            blockslen = self.x * self.y * self.z * struct.calcsize(">B")
            self.blocks = fromstring(fp.read(blockslen), uint8).reshape((self.y, self.z, self.x))
        print "Loaded World from \"%s\"" % self.filename
        
    def save(self):
        with open(self.filename, "w") as fp:
            fp.write(struct.pack(">HHH", self.x, self.y, self.z))
            fp.write(self.blocks.tostring())
        print "Saved World to \"%s\"" % self.filename
    
    def block(self, x, y, z, block=None):
        if block:
            self.blocks[y][z][x] = block
        else:
            try:
                return self.blocks[y][z][x]
            except IndexError:
                return None
        
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
