import threading as tr
import LFTPHelper as helper

class BufferController:
    """docstring for BufferController"""
    isSender = 0
    socketInstance = 0
    windowSize = 4
    length = 0
    status = [] # 0:not send, 1:send not ack, 2:acked
    cache = []
    index = []
    maxDataSeq = 0
    recevDataSeq = -1
    file = 0
    onRecev = 0
    ip_port = 0
    mutex = 0
    writeFileOver = 0
    sending = 0
    def __init__(self, _isSender, _socketInstance, _ip_port, _file = 0, _maxDataSeq = 0):
        self.isSender = _isSender
        self.socketInstance = _socketInstance
        self.file = _file
        self.ip_port = _ip_port
        self.maxDataSeq = _maxDataSeq
        self.windowSize = 4
        self.length = 0;
        self.status = []
        self.cache = []
        self.index = []
        self.recevDataSeq = -1
        self.onRecev = 0
        self.mutex = 0
        self.writeFileOver = 0
        self.sending = 0

    def doubleWindowSize(self):
        self.windowSize *= 2

    def timeOutEvent(self):
        # self.windowSize = 2
        self.clearBuffer()
        self.reSendPackets()


    def sendPackets(self):
        print("index : ", self.index)
        print("status: ", self.status)
        if self.sending:
            return
        while self.mutex == 1:
            continue
        self.mutex = 1
        self.sending = 1
        for x in range(0, self.length):
            if self.status[x] == 0:
                self.status[x] = 1
                self.socketInstance.sendto(self.cache[x], self.ip_port)
        self.sending = 0
        self.mutex = 0

    def reSendPackets(self):
        print("resend : ")
        print("index : ", self.index)
        print("status: ", self.status)
        while self.mutex == 1:
            continue
        self.mutex = 1
        self.sending = 1
        for x in range(0, self.length):
            if self.status[x] == 0 or self.status[x] == 1:
                self.socketInstance.sendto(self.cache[x], self.ip_port)
        self.sending = 0
        self.mutex = 0

    def putPacketIntoBuffer(self, data, sa):
        print("want to put data:")
        print("index : ", self.index)
        print("status: ", self.status)
        if (self.isSender and self.length >= self.windowSize):
            return False;
        while self.mutex == 1:
            continue
        self.mutex = 1
        self.status.append(0)
        self.cache.append(data)
        self.index.append(sa)
        self.length += 1
        self.mutex = 0
        return True

    def isEmpty(self):
        return self.length > 0

    def getPacketFromBuffer(self):
        if self.length <= 0:
            return
        while self.mutex == 1:
            continue
        self.mutex = 1
        data = self.cache[0]
        self.status = self.status[1:]
        self.cache = self.cache[1:]
        self.index = self.index[1:]
        # self.base = self.index[0]
        self.length -= 1
        self.mutex = 0
        return data

    def getData(self):
        while self.recevDataSeq < self.maxDataSeq:
            datagram, clientAddress = self.socketInstance.recvfrom(helper.BUFSIZE)
            header = datagram[:10]
            data = datagram[10:]
            seq = helper.getSeq(header)

            print("seq, recevDataSeq : ", seq, self.recevDataSeq)
            # reply ack, ack = seq
            if (seq <= self.recevDataSeq + 1):
                self.socketInstance.sendto(helper.createHeader(0, seq, helper.memoryBuffer-self.length), self.ip_port)
            if seq == self.recevDataSeq + 1:
                self.putPacketIntoBuffer(data, seq)
                self.recevDataSeq = seq
        self.writeFileOver = 1

    def autoWriteFile(self):
        while self.writeFileOver == 0:
            if self.length > 0:
                data = self.getPacketFromBuffer()
                print("writing data: ", data)
                self.file.write(data)
        while self.length > 0:
            data = self.getPacketFromBuffer()
            print("writing data: ", data)
            self.file.write(data)
        self.file.close()

    def getACK(self):
        self.socketInstance.settimeout(2)
        while self.recevDataSeq < self.maxDataSeq:
            try:
                ACKDatagram, addr = self.socketInstance.recvfrom(helper.BUFSIZE)
                ACK = helper.getACK(ACKDatagram[:10])
                rwdn = helper.getWindow(ACKDatagram[:10])
                print("ACK: ", ACK)
            except Exception as e:
                print(e)
                print("TimeOut!")
                self.timeOutEvent()
            else:
                if self.recevDataSeq < ACK:
                    self.recevDataSeq = ACK
                for x in range(0, self.length):
                    if (self.index[x] == ACK):
                        self.status[x] = 2
                self.clearBuffer()
            finally:
                print("index : ", self.index)
                print("status: ", self.status)
        print("get ACK over")

    def clearBuffer(self):
        if self.length <= 0:
            return
        while self.mutex == 1:
            continue
        self.mutex = 1
        ackedIndex = self.length
        for x in range(0, self.length):
            if (self.status[x] != 2):
                ackedIndex = x
                break
        self.status = self.status[ackedIndex:]
        self.cache = self.cache[ackedIndex:]
        self.index = self.index[ackedIndex:]
        self.length = len(self.status)
        self.mutex = 0

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
