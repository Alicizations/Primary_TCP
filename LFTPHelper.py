def intToBinary(num, bit):
    return bin(num)[2:].zfill(bit)

def binaryToInt(binary):
    return int(binary, 2)

def createHeader(sourcePort, destPort, sequenceNum, ackNum, window=1024):
    header = intToBinary(sourcePort, 16)
    header += intToBinary(destPort, 16)
    header += intToBinary(sequenceNum, 32)
    header += intToBinary(ackNum, 32)
    header += intToBinary(0, 16)
    header += intToBinary(window, 16)
    header += intToBinary(0, 32)
    return header

def parseHeader(header):
    header = (header[2:] if header[1]=='b' else header)
    sourcePort = binaryToInt(header[0:16])
    destPort = binaryToInt(header[16:32])
    sequenceNum = binaryToInt(header[32:64])
    ackNum = binaryToInt(header[64:96])
    window = binaryToInt(header[112:128])
    return sourcePort, destPort, sequenceNum, ackNum, window



