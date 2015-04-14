import urllib
from threading import Timer

class Heartbeat(object):
    def __init__(self, factory, endpoint):
        self.factory = factory
        self.endpoint = endpoint
        self.timer = None
    def start(self):
        self.beat()
    def stop(self):
        self.timer.cancel()
    def beat(self):
        try:
            fh = urllib.urlopen(self.endpoint, urllib.urlencode({
                "port": self.factory.config["port"],
                "users": len(self.factory.protocols),
                "max": self.factory.config["maxplayers"],
                "name": self.factory.config["name"],
                "public": self.factory.config["public"],
                "version": 7,
                "salt": self.factory.salt,
            }))
            url, self.factory.url = self.factory.url, fh.read().strip()
            if url != self.factory.url:
                print "Server URL: %s" % self.factory.url
        finally:
            self.timer = Timer(45.0, self.beat)
            self.timer.start()
