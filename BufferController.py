import threading as tr
import LFTPHelper as helper

class BufferController:
    """docstring for BufferController"""
    isSender = 0
    socketInstance = 0
    windowSize = 2
    base = 0;
    length = 0;
    status = [] # 0:not send, 1:send not ack, 2:acked
    cache = []
    index = []
    totalDataSeq = 0
    recevDataSeq = 0
    file = 0
    onRecev = 0
    BUFSIZE = 1024
    ip_port = 0
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
        self.sendPackets()

    
    def sendPackets(self):
        for x in xrange(0, self.length):
            if self.status[x] != 2:
                self.socketInstance.sendto(self.cache[x], self.ip_port)
                self.status[x] = 1

    def putPacketIntoBuffer(self, data, sa):
        if (self.isSender && self.length >= self.windowSize):
            return false;
        self.status.append(0)
        self.cache.append(data)
        self.index.append(sa)
        self.length += 1
        return true

    def isEmpty(self):
        return self.length > 0

    def getPacketFromBuffer(self):
        data = self.cache[0]
        self.status = status[1:]
        self.cache = cache[1:]
        self.index = index[1:]
        self.base = self.index[0]
        self.length -= 1
        return data

    def getData(self):
        while self.recevDataSeq < self.totalDataSeq:
            datagram, clientAddress = self.socketInstance.recvfrom(BUFSIZE)
            back_ack = datagram[:20]
            data = datagram[20:]
            seq = helper.parseHeader(back_ack)[3]
            self.recevDataSeq += seq
            self.socketInstance.sendto(back_ack, self.ip_port)
            self.putPacketIntoBuffer(data, seq)

    def autoWriteFile(self):
        while self.length > 0:
            data = self.getPacketFromBuffer()
            self.file.write(data)

    def getACK(self):
        clearTime = 0
        while self.length > 0:
            try:
                back_msg, addr = self.socketInstance.recvfrom(BUFSIZE)
                back_msg = helper.parseHeader(back_msg[:20])
            except Exception as e:
                print(e)
                print("TimeOut!")
                self.timeOutEvent()
            else:
                clearTime += 1
                for x in xrange(0, self.length):
                    if (self.index[x] == back_msg[3]):
                        self.status[x] = 2
                if (clearTime >= 3):
                    self.clearBuffer()

    def clearBuffer(self):
        ackedIndex = 0
        for x in xrange(0, self.length):
            if (self.status[x] != 2):
                ackedIndex = x
                break
        self.status = status[ackedIndex:]
        self.cache = cache[ackedIndex:]
        self.index = index[ackedIndex:]
        self.base = self.index[0]
        self.length = len(self.status)

    def notFull(self):
        return self.length < windowSize

    def openReceive(self):
        if self.onRecev == 1:
            return
        self.onRecev = 1
        if self.isSender:
            self.socketInstance.settimeout(2)
            gACK = tr.Thread(target = getACK, args = (self,))
            gACK.start()
        else:
            wf = tr.Thread(target = autoWriteFile, args = (self,))
            gData = tr.Thread(target = autoWriteFile, args = (self,))
            gData.start()
            wf.start()
