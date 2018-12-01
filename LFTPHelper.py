
# num should be a non-negative number
def intToBytes(num, byteNum):
    return num.to_bytes(byteNum, "big")

def intFromBytes(byte):
    return int.from_bytes(byte, "big")

def createHeader(sourcePort, destPort, sequenceNum, ackNum, SYN=0, FIN=0, window=1024):
    header = intToBytes(sourcePort, 2)
    header += intToBytes(destPort, 2)
    header += intToBytes(sequenceNum, 4)
    header += intToBytes(ackNum, 4)
    header += intToBytes(SYN, 1)
    header += intToBytes(FIN, 1)
    header += intToBytes(window, 2)
    header += intToBytes(0, 4)
    return header

def parseHeader(header):
    sourcePort = intFromBytes(header[0:2])
    destPort = intFromBytes(header[2:4])
    sequenceNum = intFromBytes(header[4:8])
    ackNum = intFromBytes(header[8:12])
    SYN = intFromBytes(header[12:13])
    FIN = intFromBytes(header[13:14])
    window = intFromBytes(header[14:16])
    return sourcePort, destPort, sequenceNum, ackNum, SYN, FIN, window

def sendFile():
    return

def receiveFile():
    return

