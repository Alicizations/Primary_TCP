import BufferController as BC
import sys
import math

packetSize = 2000
BUFSIZE = 2048
memoryBuffer = 40 # count in number of packets

# num should be a non-negative number
def intToBytes(num, byteNum):
    return num.to_bytes(byteNum, "big")

def intFromBytes(byte):
    return int.from_bytes(byte, "big")

# window count in number of packets
def createHeader(seq, ack, window=20):
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

totalWidth = 40
def updateProgressBar(percentage, filepath, IP_Port):
    elements = filepath.split("\\")
    filename = elements[len(elements)-1]

    barWidth = math.ceil(percentage * totalWidth)

    sys.stdout.write("\r[%s]\t%s\t%s" % (" " * totalWidth, filename, IP_Port))
    sys.stdout.write("\r[%s" % ("-" * (barWidth)))
    sys.stdout.flush()

class sender:
    def __init__(self, isServer,senderUDPsocket, receiver_IP_Port, fileObject, packetsNum):
        self.UDPsocket = senderUDPsocket
        self.controller = BC.BufferController(True, isServer, senderUDPsocket, receiver_IP_Port, fileObject, packetsNum-1)
                                                                  # maxSeq = pckNum - 1,count from zero
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
                # print("seq: ", self.seq)
                # if buffer is full, wait buffer space
                while (self.controller.putPacketIntoBuffer(packet, self.seq) == False):
                    self.controller.putPacketIntoBuffer(packet, self.seq)

                if (self.controller.readyToSend()):
                    self.controller.sendPackets()
                self.seq += 1
                self.working = self.controller.isEnd()

            if (self.controller.readyToSend()):
                self.controller.sendPackets()
            self.controller.clearBuffer()
            self.working = self.controller.isEnd()
        self.file.close()
        print("send over!")



class receiver(object):
    """ ACK: cumulative ACK, next bytes expected to receive"""
    def __init__(self, isServer, receiverUDPSocket, sender_IP_Port, fileObject, packetsNum):
        self.controller = BC.BufferController(False, isServer, receiverUDPSocket, sender_IP_Port, fileObject, packetsNum-1)
                                                                            # maxSeq = pckNum - 1,count from zero
        if (not isServer):
            updateProgressBar(0, fileObject.name, sender_IP_Port)

    def receiveFile(self):
        self.controller.openReceive()


