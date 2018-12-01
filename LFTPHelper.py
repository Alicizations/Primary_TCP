import threading

timeInterval = 5

# num should be a non-negative number
def intToBytes(num, byteNum):
    return num.to_bytes(byteNum, "big")

def intFromBytes(byte):
    return int.from_bytes(byte, "big")

def createHeader(srcPort, dstPort, seqNum, ackNum, SYN=0, FIN=0, window=1024):
    header = intToBytes(srcPort, 2)
    header += intToBytes(dstPort, 2)
    header += intToBytes(seqNum, 4)
    header += intToBytes(ackNum, 4)
    header += intToBytes(SYN, 1)
    header += intToBytes(FIN, 1)
    header += intToBytes(window, 2)
    header += intToBytes(0, 4)
    return header

def parseHeader(header):
    srcPort = intFromBytes(header[0:2])
    dstPort = intFromBytes(header[2:4])
    seqNum = intFromBytes(header[4:8])
    ackNum = intFromBytes(header[8:12])
    SYN = intFromBytes(header[12:13])
    FIN = intFromBytes(header[13:14])
    window = intFromBytes(header[14:16])
    return srcPort, dstPort, seqNum, ackNum, SYN, FIN, window

class sender:
    """
    base: oldest unacknowledged packet
    nextSeq: smallest unused sequence number
    """
    def __init__(self, srcPort, rcvPort, rcvIP, window):
        super(sender, self).__init__()
        self.srcPort = srcPort
        self.rcvPort = rcvPort
        self.rcvIP = rcvIP
        self.window = window

        self.UDPsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.base = 0
        self.nextSeq = 0
        self.window = window
        self.BUFSIZE = 1024

    def sendPacket(seq, ACK, data=bytes(0)):
        header = createHeader(self.srcPort, self.dstPort, seq, ACK)
        self.UDPsocket.sendto(header + data, (self.rcvIP, self.rcvPort))

    def startTimer(seq, data):
        # retransmit not-yet-acknowledged segment
        def retransmit(seq, data):
            if (seq < base):
                sendPacket(seq, 0, data)
                timer = threading.Timer(timeInterval, retransmit, seq, data)
                timer.start()

        timer = threading.Timer(timeInterval, retransmit, seq, data)
        timer.start()

    def sendFile():
        # while ACK >= file.size():
        pass

        while (true):
            # receive ACK, update base
            datagram, rcvAddress = self.UDPsocket.recvfrom(self.BUFSIZE)
            header = parseHeader(datagram[:20])
            ACK = header[3]
            if (ACK > self.base):
                self.base = ACK

            # read file into buffer
            pass

            # send packet if window is not full
            if (self.nextSeq < self.base + self.window):
                # data = fileBuffer[index]
                pass
                sendPacket(0, self.nextSeq, data)
                startTimer(self.nextSeq, data) # when to start timer?
                self.nextSeq += len(data)

class receiver(object):
    """ ACK: cumulative ACK, next bytes expected to receive"""
    def __init__(self, srcPort, rcvPort, srcIP, rcvIP, window):
        super(sender, self).__init__()
        self.srcPort = srcPort
        self.rcvPort = rcvPort
        self.rcvIP = rcvIP
        self.window = window

        self.UDPsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.UDPsocket.bind((srcIP, srcPort))
        self.BUFSIZE = 1024
        self.ACK = 0

    def sendPacket(seq, ACK, data=bytes(0)):
        header = createHeader(self.srcPort, self.dstPort, seq, ACK)
        self.UDPsocket.sendto(header + data, (self.rcvIP, self.rcvPort))

    def receiveFile():
        while (true):
            # receive data
            datagram, rcvAddress = self.UDPsocket.recvfrom(self.BUFSIZE)
            header = parseHeader(datagram[:20])
            seq = header[2]

            if (seq > self.ACK):
                # un-order packet
                sendPacket(0, self.ACK)
            else if (seq == self.ACK):
                data = datagram[20:]
                self.ACK += len(data)
                sendPacket(0, self.ACK)
                # write data into disk
                pass
            else:
                # drop duplicate packet