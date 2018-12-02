import threading as tr
import LFTPHelper as helper

class BufferController:
    """docstring for BufferController"""
    isSender = 0
    socketInstance = 0
    windowSize = 4
    base = 0;
    length = 0;
    status = [] # 0:not send, 1:send not ack, 2:acked
    cache = []
    index = []
    totalDataSeq = 0
    recevDataSeq = -1
    file = 0
    onRecev = 0
    BUFSIZE = 1024
    ip_port = 0
    mutex = 0
    writeFileOver = 0
    def __init__(self, _isSender, _socketInstance, _ip_port, _file = 0, _totalDataSeq = 0):
        self.isSender = _isSender
        self.socketInstance = _socketInstance
        self.file = _file
        self.ip_port = _ip_port
        self.totalDataSeq = _totalDataSeq

    def doubleWindowSize(self):
        self.windowSize *= 2

    def timeOutEvent(self):
        # self.windowSize = 2
        self.clearBuffer()
        self.reSendPackets()


    def sendPackets(self):
        print("index : ", self.index)
        while self.mutex == 1:
            continue
        mutex = 1
        for x in range(0, self.length):
            if self.status[x] == 0:
                self.status[x] = 1
                self.socketInstance.sendto(self.cache[x], self.ip_port)
        mutex = 0

    def reSendPackets(self):
        print("index : ", self.index)
        while self.mutex == 1:
            continue
        mutex = 1
        for x in range(0, self.length):
            if self.status[x] == 1:
                self.socketInstance.sendto(self.cache[x], self.ip_port)
        mutex = 0

    def putPacketIntoBuffer(self, data, sa):
        if (self.isSender and self.length >= self.windowSize):
            return False;
        while self.mutex == 1:
            continue
        mutex = 1
        self.status.append(0)
        self.cache.append(data)
        self.index.append(sa)
        self.length += 1
        mutex = 0
        return True

    def isEmpty(self):
        return self.length > 0

    def getPacketFromBuffer(self):
        while self.mutex == 1:
            continue
        mutex = 1
        data = self.cache[0]
        self.status = self.status[1:]
        self.cache = self.cache[1:]
        self.index = self.index[1:]
        # self.base = self.index[0]
        self.length -= 1
        mutex = 0
        return data

    def getData(self):
        while self.recevDataSeq < self.totalDataSeq:
            datagram, clientAddress = self.socketInstance.recvfrom(self.BUFSIZE)
            header = datagram[:10]
            data = datagram[10:]
            seq = helper.getSeq(header)
            # reply ack, ack = seq
            self.socketInstance.sendto(helper.createHeader(0, seq), self.ip_port)
            if seq == self.recevDataSeq + 1:
                self.putPacketIntoBuffer(data, seq)
                self.recevDataSeq = seq
        self.writeFileOver = 1

    def autoWriteFile(self):
        while self.writeFileOver == 0:
            print(self.length)
            if self.length > 0:
                data = self.getPacketFromBuffer()
                print("writing data: ", data)
                self.file.write(data)
        self.file.close()

    def getACK(self):
        self.socketInstance.settimeout(2)
        while self.recevDataSeq < self.totalDataSeq:
            try:
                ACKDatagram, addr = self.socketInstance.recvfrom(self.BUFSIZE)
                ACK = helper.getACK(ACKDatagram[:10])
            except Exception as e:
                print(e)
                print("TimeOut!")
                self.timeOutEvent()
                print("status: ", self.status)
            else:
                if self.recevDataSeq < ACK:
                    self.recevDataSeq = ACK
                for x in range(0, self.length):
                    if (self.index[x] == ACK):
                        self.status[x] = 2
                self.clearBuffer()

    def clearBuffer(self):
        while self.mutex == 1:
            continue
        mutex = 1
        ackedIndex = 0
        for x in range(0, self.length):
            if (self.status[x] != 2):
                ackedIndex = x
                break
        self.status = self.status[ackedIndex:]
        self.cache = self.cache[ackedIndex:]
        self.index = self.index[ackedIndex:]
        self.base = self.index[0]
        self.length = len(self.status)
        mutex = 0

    def notFull(self):
        return self.length < self.windowSize

    def openReceive(self):
        if self.onRecev == 1:
            return
        self.onRecev = 1
        if self.isSender:
            gACK = tr.Thread(target = self.getACK)
            gACK.start()
        else:
            wf = tr.Thread(target = self.autoWriteFile)
            gData = tr.Thread(target = self.getData)
            gData.start()
            wf.start()
