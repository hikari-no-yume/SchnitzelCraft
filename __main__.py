from twisted.internet import reactor
from factories.schnitzel import SchnitzelFactory
   
factory = SchnitzelFactory("schnitzel.json")
reactor.listenTCP(factory.config["port"], factory)
reactor.run()
