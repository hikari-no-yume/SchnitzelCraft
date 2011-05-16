import struct

PacketIDs = {
    "Identification": 0x00,
    "Ping": 0x01,
    "LevelInitialize": 0x02,
    "LevelDataChunk": 0x03,
    "LevelFinalize": 0x04,
    "ClientSetBlock": 0x05,
    "SetBlock": 0x06,
    "SpawnPlayer": 0x07,
    "PositionAndOrientation": 0x08,
    "PositionAndOrientationUpdate": 0x09,
    "PositionUpdate": 0x0a,
    "OrientationUpdate": 0x0b,
    "DespawnPlayer": 0x0c,
    "Message": 0x0d,
    "DisconnectPlayer": 0x0e,
    "UpdateUserType": 0x0f
}

PacketFormats = {
    PacketIDs["Identification"]: ">BB64s64sB",
    PacketIDs["Ping"]: ">B",
    PacketIDs["LevelInitialize"]: ">B",
    PacketIDs["LevelDataChunk"]: ">BH1024sB",
    PacketIDs["LevelFinalize"]: ">BHHH",
    PacketIDs["ClientSetBlock"]: ">BHHHBB",
    PacketIDs["SetBlock"]: ">BHHHB",
    PacketIDs["SpawnPlayer"]: ">BB64sHHHBB",
    PacketIDs["PositionAndOrientation"]: ">BBHHHBB",
    PacketIDs["DespawnPlayer"]: ">BB",
    PacketIDs["Message"]: ">BB64s"
}

PacketSizes = {}
for k, v in PacketFormats.iteritems():
    PacketSizes[k] = struct.calcsize(v)
    
Blocks = {
    "Air": 0x00,
    "Stone": 0x01,
    "Grass": 0x02,
    "Dirt": 0x03
}
