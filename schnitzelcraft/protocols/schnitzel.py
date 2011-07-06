import struct
import timeit
from constants import PacketIDs, PacketSizes, PacketFormats, Blocks, TransparentBlocks, TreeShape
from math import floor
from util import notch_to_string, string_to_notch
from twisted.internet.protocol import Protocol

def unpack_byte(byte):
    return struct.unpack("B",byte[0])[0]

class SchnitzelProtocol(Protocol):
    def __init__(self):
        self.buf = b""
        self.packetsize = None

        self.handlers = {
            PacketIDs["Identification"]: self.identify,
            PacketIDs["ClientSetBlock"]: self.setblock,
            PacketIDs["PositionAndOrientation"]: self.posandort,
            PacketIDs["Message"]: self.message
        }
        
        self.name = None
        self.ID = None
        self.op = False
        
        self.x = 0
        self.y = 0
        self.z = 0
        self.yaw = 0
        self.pitch = 0
        
        print "SchnitzelProtocol created"
    
    def dataReceived(self, data):
        self.buf += data
        while self.buf:
            if not self.packetsize:
                byte = unpack_byte(self.buf[0])
                if byte in self.handlers:
                    self.packetsize = PacketSizes[byte]
                else:
                    print "Error! Unhandled packet! (%s)" % byte
                    self.transport.loseConnection()
            else:
                if len(self.buf) >= self.packetsize:
                    self.handlers[byte](self.buf[:PacketSizes[byte]]) # Handle packet
                    self.buf = self.buf[PacketSizes[byte]:]
                    self.packetsize = None
                else:
                    break
                    
    def connectionLost(self, reason):
        print "\"%s\" disconnected" % self.name
        if self.ID:
            del self.factory.protocols[self.ID]
            self.factory.sendPacketSkip(self, PacketIDs["DespawnPlayer"], self.ID)
            if self.op:
                self.factory.sendMessage("[OP] %s disconnected" % self.name)
            else:
                self.factory.sendMessage("%s disconnected" % self.name)
            args = (self.name, self.x/32, self.y/32, self.z/32)
            print "\"%s\" despawned (%s, %s, %s)" % args
                
    def sendPacket(self, *packet):
        format = PacketFormats[packet[0]]
        packet = struct.pack(format, *packet)
        self.transport.write(packet)
        
    def unpackPacket(self, data):
        format = PacketFormats[unpack_byte(data[0])]
        return struct.unpack(format, data)
    
    def identify(self, data):
        packet = self.unpackPacket(data)
        self.name = notch_to_string(packet[2])
        key = notch_to_string(packet[3])
        if key != "--":
            print "\"%s\" identified with verification key \"%s\"" % (self.name, key)
        else:
            print "\"%s\" identified without verification" % self.name
        if self.name in self.factory.config["ops"]:
            self.op = True
        
        # Send welcome
        name = string_to_notch(self.factory.config["name"])
        motd = string_to_notch(self.factory.config["motd"])
        op = 0x64 if self.op else 0x00
        self.sendPacket(PacketIDs["Identification"], 0x07, name, motd, op)
        
        # Send level
        gzippedmap = self.factory.world.gzip(numblocks=True)
        totallen = len(gzippedmap)
        currentlen = 0
        self.sendPacket(PacketIDs["LevelInitialize"])
        while gzippedmap:
            chunk = gzippedmap[:1024].ljust(1024,'\0')
            gzippedmap = gzippedmap[1024:]
            currentlen += len(chunk)
            pc = int(currentlen/totallen * 255)
            self.sendPacket(PacketIDs["LevelDataChunk"], len(chunk), chunk, pc)
        size = self.factory.world.x, self.factory.world.y, self.factory.world.z
        self.sendPacket(PacketIDs["LevelFinalize"], *size)
        
        # Acquire ID
        for i in range(self.factory.config["maxplayers"]):
            if not i in self.factory.protocols:
                self.factory.protocols[i] = self
                self.ID = i
                break
        else:   
            print "wait... hold on a second, that wasn't supposed to happen"
            self.transport.loseConnection()
        
        # Set position
        self.x = self.factory.world.x*16
        self.y = self.factory.world.y*32
        self.z = self.factory.world.z*16
        
        # Spawn rest of world to client
        for i in self.factory.protocols.itervalues():
            if i != self and i.ID != None:
                name = string_to_notch(i.name)
                pos = (i.x, i.y, i.z, i.yaw, i.pitch)
                self.sendPacket(PacketIDs["SpawnPlayer"], i.ID, name, *pos)
            
        # Spawn client to rest of world
        name = string_to_notch(self.name)
        pos = (self.x, self.y, self.z, self.yaw, self.pitch)
        pid = PacketIDs["SpawnPlayer"]
        self.factory.sendPacketSkip(self, pid, self.ID, name, *pos)
        if self.op:
            self.factory.sendMessage("[OP] %s joined the server" % self.name)
        else:
            self.factory.sendMessage("%s joined the server" % self.name)
        
        # Teleport client
        self.sendPacket(PacketIDs["PositionAndOrientation"], 255, *pos)
        args = (self.name, self.x/32, self.y/32, self.z/32)
        print "\"%s\" spawned (%s, %s, %s)" % args
        
    def posandort(self, data):
        packet = self.unpackPacket(data)
        
        newpos = tuple(packet[2:8])
        oldpos = (self.x, self.y, self.z, self.yaw, self.pitch)
        if newpos != oldpos:
            pid = PacketIDs["PositionAndOrientation"]
            self.factory.sendPacketSkip(self, pid, self.ID, *newpos)
        
    def setblock(self, data):
        packet = self.unpackPacket(data)
        x, y, z = packet[1:4]
        btype = packet[5] if packet[4] else Blocks["Air"]
        below = self.factory.world.block(x, y-1, z)
        
        if packet[4] and packet[5] == Blocks["RedMushroom"]:
            block = self.factory.world.block(x, y, z)
            if block == Blocks["BlueCloth"]:
                btype = Blocks["StationaryWater"]
            elif block == Blocks["OrangeCloth"]:
                btype = Blocks["StationaryLava"]
            elif block == Blocks["Sapling"]:
                for i in TreeShape:
                    coords = i[1][0]+x, i[1][1]+y, i[1][2]+z, i[0]
                    if i is TreeShape[0]:
                        x, y, z, btype = coords
                    else:
                        self.factory.world.block(*coords)
                        self.factory.sendPacket(PacketIDs["SetBlock"], *coords)
            elif block == Blocks["LimeCloth"]:
                btype = Blocks["Grass"]
                
        elif btype == Blocks["Slab"] and below == Blocks["Slab"]:
            self.sendPacket(PacketIDs["SetBlock"], x, y, z, Blocks["Air"])
            y -= 1
            btype = Blocks["DoubleSlab"]
        self.factory.world.block(x, y, z, btype)
        self.factory.sendPacket(PacketIDs["SetBlock"], x, y, z, btype)
        
        if not btype in TransparentBlocks:
            for i in range(y):
                if self.factory.world.block(x, i, z) == Blocks["Grass"]:
                    ntype = Blocks["Dirt"]
                    self.factory.world.block(x, i, z, ntype)
                    self.factory.sendPacket(PacketIDs["SetBlock"], x, i, z, ntype)
                    break
        
    def message(self, data):
        packet = self.unpackPacket(data)
        msg = notch_to_string(packet[2])
        color = "&" + hex(self.ID % 16)[2]
        msg = ("[OP] " if self.op else "") + color + self.name + ":&f " + msg
        self.factory.sendMessage(msg, self.ID)
