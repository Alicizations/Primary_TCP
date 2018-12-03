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

''' state: 0: error
           1: ready to transfer
           2: file not found
           3: no available port
'''
errorMessage = ["unknown error", "OK", "file not found", "no available port"]
def createMessage(isDownload, state, transferPort, fileSize, fileName):
    message = intToBytes(isDownload, 1)
    message += intToBytes(state, 1)
    message += intToBytes(transferPort, 2)
    message += intToBytes(fileSize, 4)
    message += fileName.encode("utf-8")
    return message

def getIsDownload(message):
    return intFromBytes(message[:1])

def getState(message):
    return intFromBytes(message[1:2])

def getTransferPort(message):
    return intFromBytes(message[2:4])

def getFileSize(message):
    return intFromBytes(message[4:8])

def getFileName(message):
    return message[8:].decode("utf-8")

class sender:
    def __init__(self, senderUDPsocket, receiver_IP_Port, fileObject, packetsNum):
        self.UDPsocket = senderUDPsocket
        self.controller = BufferController.BufferController(True, senderUDPsocket, receiver_IP_Port, 0, packetsNum)
        self.file = fileObject
        self.seq = 0
        self.working = True

    def sendFile(self):
        self.controller.openReceive() # To receive ack from receiver

        while self.working:
            while self.controller.notFull():
                packetData = self.file.read(packetSize)

                if len(packetData) == 0:
                    # if read out of file
                    self.working = 0
                    break

                packetHeader = createHeader(self.seq, 0)
                packet = packetHeader + packetData
                print("seq: ", self.seq)
                self.controller.putPacketIntoBuffer(packet, self.seq)
                self.controller.sendPackets()
                self.seq += 1
        self.file.close()



class receiver(object):
    """ ACK: cumulative ACK, next bytes expected to receive"""
    def __init__(self, receiverUDPSocket, sender_IP_Port, fileObject, packetsNum):
        self.controller = BufferController.BufferController(False, receiverUDPSocket, sender_IP_Port, fileObject, packetsNum)

    def receiveFile(self):
        self.controller.openReceive()

