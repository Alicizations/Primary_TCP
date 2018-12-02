import BufferController

timeInterval = 5
packetSize = 200

# num should be a non-negative number
def intToBytes(num, byteNum):
    return num.to_bytes(byteNum, "big")

def intFromBytes(byte):
    return int.from_bytes(byte, "big")

def createHeader(seq, ack, window=1024):
    header = intToBytes(seq, 4)
    header += intToBytes(ack, 4)
    header += intToBytes(window, 2)
    return header

def getSeq(header):
    return intFromBytes(header[0:4])

def getACK(header):
    return intFromBytes(header[4:8])

def getWindow(header):
    return intFromBytes(header[8:10])

''' isOK: 1: ready to transfer
          0: error
          2: file not found
          3: no available port
'''
def createCommand(isDownload, isOK, transferPort, fileSize, filePath):
    command = intToBytes(isDownload, 1)
    command += intToBytes(isOK, 1)
    command += intToBytes(transferPort, 2)
    command += intToBytes(fileSize, 4)
    command += filePath.encode("utf-8")
    return command

def getIsDownload(command):
    return intFromBytes(command[:1])

def getIsOK(command):
    return intFromBytes(command[1:2])

def getTransferPort(command):
    return intFromBytes(command[2:4])

def getFileSize(command):
    return intFromBytes(command[4:8])

def getFilePath(command):
    return command[8:].decode("utf-8")

class sender:
    def __init__(self, sender_IP_Port, receiver_IP_Port, fileObject, packetsNum):
        UDPsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        UDPsocket.bind(sender_IP_Port)
        self.controller = BufferController.BufferController(True, UDPsocket, receiver_IP_Port, 0, packetsNum)
        self.file = fileObject
        self.seq = 0
        self.working = True

    def sendFile():
        self.controller.openReceive() # To receive ack from receiver

        while self.working:
            while self.controller.notFull():
                packetData = self.file.read(packetSize)

                if len(packetData) == 0:
                    # if read out of file
                    self.working = 0
                    break

                packetHeader = createHeader(seq, 0)
                packet = packetHeader + packetData
                print("seq: ", seq)
                self.controller.putPacketIntoBuffer(packet, seq)
                self.controller.sendPackets()
                seq += 1

        self.file.close()


class receiver(object):
    """ ACK: cumulative ACK, next bytes expected to receive"""
    def __init__(self, sender_IP_Port, receiver_IP_Port, fileObject, packetsNum):
        UDPsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        UDPsocket.bind(receiver_IP_Port)
        self.controller = BufferController.BufferController(Flase, UDPsocket, sender_IP_Port, fileObject, packetsNum)

    def receiveFile():
        self.controller.openReceive()

