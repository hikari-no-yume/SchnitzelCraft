from twisted.internet.protocol import ServerFactory
from constants import PacketIDs
from commands import Command
from bots import Bot
from protocols import ValetProtocol
from util import notch_to_string, string_to_notch
from heartbeat import Heartbeat
from world import World
from plugins import *
from twisted.internet.task import LoopingCall
import json, time

class ValetFactory(ServerFactory):
    protocol = ValetProtocol

    def __init__(self, config="config.json", plugins="plugins"):
        # Configuration
        self.configname = config
        self.pluginpath = plugins
        try:
            self.loadConfig()
        except IOError:
            self.createConfig()
            self.saveConfig()
        
        # Attributes
        self.protocols = {}
        self.bots = []
        self.url = ""
        self.salt = "mysalt%s" % time.time()
        self.commands = []
        self.heart = Heartbeat(self)
        self.world = World(self.config["world"])

        # Load Plugins
        for plugin in self.config["plugins"]:
            try: __import__("%s.%s" % (plugins, plugin))
            except ImportError: print "Unable to load plugin: %s" % plugin
        
    def createConfig(self):
        self.config = {}
        self.config["port"] = 25565
        self.config["name"] = "Minecraft Server [Valet]"
        self.config["motd"] = ""
        self.config["maxplayers"] = 128
        self.config["saveinterval"] = 600 # 10 minutes
        self.config["ops"] = []
        self.config["commandPrefix"] ="/"
        self.config["plugins"] = []
        self.config["magicwand"] = True
        self.config["public"] = True
        self.config["noverify"] = False
        self.config["world"] = "world.dat"
        print "Created configuration from defaults."

    def reloadPlugin(self, name):
        try:
            # self.unload
            plug = reload(__import__("%s.%s" % (self.pluginpath, name)))
            __import__("%s.%s" % (self.pluginpath, name))
        except ImportError:
            pass
        
    def loadConfig(self):
        with open(self.configname, "r") as fp:
            self.config = json.load(fp)
        print "Loaded configuration from '%s'." % self.configname
            
    def saveConfig(self):
        with open(self.configname, "w") as fp:
            json.dump(self.config, fp, indent=4)
        print "Saved configuration to '%s'." % self.configname
        
    def startFactory(self):
        self.pingtimer = LoopingCall(self.sendPacket, PacketIDs["Ping"])
        self.pingtimer.start(1, False)
        self.heart.start()
        self.greetBot = self.add_bot("Manager", True)
        self.notchBot = self.add_bot("Notch", False, 3552, 1091, 3580)
        
        def save(self):
            self.world.save()
            self.messageAll("World saved")
            self.saveConfig()
        self.savetimer = LoopingCall(save, self)
        self.savetimer.start(self.config["saveinterval"], False)
        
        # Runtime vars
        self.usedIDs = [] # List of Player IDs used (can be occupied by mobs)
        self.protocols = {} # Dictionary of Protocols indexed by ID
        
        print "Server ready."
        
    def stopFactory(self):
        for i in self.protocols.itervalues():
            i.transport.loseConnection()
        for i in self.bots:
            self.del_bot(i)
        self.heart.stop()
        self.world.save()
        self.saveConfig()

    def parseCommand(self, cl, msg):
        msg = msg.split()
        if not len(msg):
            return
        cmd = msg[0]
        arg = msg[1:]
        print "%s: running cmd '%s' with args %s" % (cl.name, cmd, arg)
        if cmd == 'pos':
            print "pos: %s x %s x %s" % (cl.x, cl.y, cl.z)

    def command(self, name, **options):
        def decorator(func):
            cmd = Command()
            cmd.name = name
            cmd.func = func
            cmd.help = func.__doc__
            if options.get("max_args"):
                cmd.max_args = options.get("max_args")
            if options.get("op_only"):
                cmd.op_only = options.get("op_only")
            self.commands.append(cmd)
            return func
        return decorator

    def has_command(self, name):
        for cmd in self.commands:
            if cmd.name == name:
                return True
        return False

    def get_command(self, name):
        for cmd in self.commands:
            if cmd.name == name:
                return cmd
        return None

    def add_bot(self, name="", op=False, x=0, y=0, z=0, yaw=0, pitch=0):
        bot = Bot(self, name, op, x, y, z, yaw, pitch)
        self.bots.append(bot)
        return bot

    def del_bot(self, bot):
        bot.disconnect()
        self.bots.remove(bot)
    
    def sendPacket(self, *packet):
        for i in self.protocols.itervalues():
            i.sendPacket(*packet)
                
    def sendPacketSkip(self, skip, *packet):
        for i in self.protocols.itervalues():
            if i != skip:
                i.sendPacket(*packet)
                
    def messageAll(self, msg, pid=255):
        while msg:
            msgpart = string_to_notch(msg[:64])
            msg = msg[64:]
            self.sendPacket(PacketIDs["Message"], pid, msgpart)

    def messageClient(self, cl, msg, pid=255):
        while msg:
            msgpart = string_to_notch(msg[:64])
            msg = msg[64:]
            cl.sendPacket(PacketIDs["Message"], pid, msgpart)
