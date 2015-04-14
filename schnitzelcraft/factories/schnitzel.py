from twisted.internet.protocol import ServerFactory
from constants import PacketIDs
from protocols.schnitzel import SchnitzelProtocol
from util import notch_to_string, string_to_notch, generate_salt
from world import World
from twisted.internet.task import LoopingCall
from heartbeat import Heartbeat
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
        self.url = ""
        self.world = World(self.config["world"])
        
        print "SchnitzelFactory created"
        
    def createConfig(self):
        self.config = {
            "port": 25565,
            "name": "SchnitzelCraft",
            "motd": "",
            "maxplayers": 128,
            "saveinterval": 600, # 10 minutes
            "ops": [],
            "plugins": [],
            "magicwand": True,
            "public": True,
            "noverify": False,
            "world": "world.dat"
        }
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
        # Runtime vars
        self.usedIDs = [] # List of Player IDs used (can be occupied by mobs)
        self.protocols = {} # Dictionary of Protocols indexed by ID
        self.salt = generate_salt()
        
        self.pingtimer = LoopingCall(self.sendPacket, PacketIDs["Ping"])
        self.pingtimer.start(1, False)

        self.heart = Heartbeat(self)
        self.heart.start()
        
        def save(self):
            self.world.save()
            self.sendMessage("World saved")
            self.saveConfig()
        self.savetimer = LoopingCall(save, self)
        self.savetimer.start(self.config["saveinterval"], False)
        
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
