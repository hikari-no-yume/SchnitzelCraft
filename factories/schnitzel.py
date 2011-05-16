from twisted.internet.protocol import ServerFactory
from constants import PacketIDs
from protocols.schnitzel import SchnitzelProtocol
from util import notch_to_string, string_to_notch
from world import World
from twisted.internet.task import LoopingCall
import json

class SchnitzelFactory(ServerFactory):
    protocol = SchnitzelProtocol

    def __init__(self, name):
        # Configuration
        self.configname = name
        self.loadConfig()
        
        # World
        self.world = World(self.config["world"])
        
        print "SchnitzelFactory created"
        
    def loadConfig(self):
        try:
            with open(self.configname, "r") as fp:
                self.config = json.load(fp)
        except IOError:
            self.config = {}
            self.config["port"] = 25565
            self.config["name"] = "SchnitzelCraft"
            self.config["motd"] = ""
            self.config["maxplayers"] = 128
            self.config["world"] = "world.dat"
            self.saveConfig()
            
    def saveConfig(self):
        with open(self.configname, "w") as fp:
            json.dump(self.config, fp)
        
    def startFactory(self):
        # Automatic ping
        def ping(self):
            self.sendPacket(PacketIDs["Ping"])
            print "Ping!"
        self.pingtimer = LoopingCall(self.sendPacket, PacketIDs["Ping"])
        self.pingtimer.start(1, False)
        
        # Runtime vars
        self.protocols = {} # Dictionary of Protocols indexed by ID
        
        print "SchnitzelFactory started"
        
    def sendPacket(self, *packet):
        for i in self.protocols.itervalues():
            i.sendPacket(*packet)
                
    def sendPacketSkip(self, skip, *packet):
        for i in self.protocols.itervalues():
            if i != skip:
                i.sendPacket(*packet)
                
    def sendMessage(self, msg, pid=255):
        while msg:
            msgpart = string_to_notch(msg[:64])
            msg = msg[64:]
            self.sendPacket(PacketIDs["Message"], pid, msgpart)
