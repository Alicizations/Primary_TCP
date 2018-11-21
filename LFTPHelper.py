def intToBinary(num, bit):
    return bin(num)[2:].zfill(bit)

def binaryToInt(binary):
    return int(binary, 2)

def createHeader(sourcePort, destPort, sequenceNum, ackNum, SYN=0, FIN=0, window=1024):
    header = intToBinary(sourcePort, 16)
    header += intToBinary(destPort, 16)
    header += intToBinary(sequenceNum, 32)
    header += intToBinary(ackNum, 32)
    header += intToBinary(0, 14)
    header += intToBinary(SYN, 1)
    header += intToBinary(FIN, 1)
    header += intToBinary(window, 16)
    header += intToBinary(0, 32)
    return header

def parseHeader(header):
    header = (header[2:] if header[1]=='b' else header)
    sourcePort = binaryToInt(header[0:16])
    destPort = binaryToInt(header[16:32])
    sequenceNum = binaryToInt(header[32:64])
    ackNum = binaryToInt(header[64:96])
    SYN = binaryToInt((header[110]))
    FIN = binaryToInt((header[111]))
    window = binaryToInt(header[112:128])
    return sourcePort, destPort, sequenceNum, ackNum, SYN, FIN, window

def sendFile():
    return

def receiveFile():
    return

