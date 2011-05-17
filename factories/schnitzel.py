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
        try:
            self.loadConfig()
        except IOError:
            self.createConfig()
            self.saveConfig()
        
        # World
        self.world = World(self.config["world"])
        
        print "SchnitzelFactory created"
        
    def createConfig(self):
        self.config = {}
        self.config["port"] = 25565
        self.config["name"] = "SchnitzelCraft"
        self.config["motd"] = ""
        self.config["maxplayers"] = 128
        self.config["saveinterval"] = 600 # 10 minutes
        self.config["public"] = True
        self.config["noverify"] = False
        self.config["world"] = "world.dat"
        print "Created Configuration from defaults"
        
    def loadConfig(self):
        with open(self.configname, "r") as fp:
            self.config = json.load(fp)
        print "Loaded Configuration from \"%s\"" % self.configname
            
    def saveConfig(self):
        with open(self.configname, "w") as fp:
            json.dump(self.config, fp, indent=4)
        print "Saved Configuration to \"%s\"" % self.configname
        
    def startFactory(self):
        self.pingtimer = LoopingCall(self.sendPacket, PacketIDs["Ping"])
        self.pingtimer.start(1, False)
        
        def save(self):
            self.world.save()
            self.sendMessage("World saved")
            self.saveConfig()
        self.savetimer = LoopingCall(save, self)
        self.savetimer.start(self.config["saveinterval"], False)
        
        # Runtime vars
        self.protocols = {} # Dictionary of Protocols indexed by ID
        
        print "SchnitzelFactory started"
        
    def stopFactory(self):
        print "SchnitzelFactory stopping..."
        for i in self.protocols.itervalues():
            i.transport.loseConnection()
        self.world.save()
        self.saveConfig()
        print "SchnitzelFactory stopped"
        
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
