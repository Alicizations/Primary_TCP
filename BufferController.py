import threading as tr
import LFTPHelper as helper

class BufferController:
    """docstring for BufferController"""
    isSender = 0            # sender or not
    socketInstance = 0      # socket instance
    windowSize = 4          # window size
    length = 0              # buffer's length
    status = []             # 0:not send, 1:send not ack, 2:acked
    cache = []              # data cache
    index = []              # data seq
    maxDataSeq = 0          # max seq
    recevDataSeq = -1       # already recev max seq
    file = 0                # file pointer (already open)
    onRecev = 0             # control recev func
    ip_port = 0             # (ip, port)
    mutex = 0               # mutex for length
    writeFileOver = 0       # flag for stopping file writing
    sending = 0             # send status
    lastTimeOutWnd = 15     # last time-out window size
    maxWnd = 30             # buffer max window size
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
        self.lastTimeOutWnd = 15
        self.maxWnd = 30

    def increaseWindowSize(self):
        if self.windowSize >= self.maxWnd:
            return
        if self.windowSize < self.lastTimeOutWnd:
            self.windowSize *= 2
        else:
            self.windowSize += 1
        

    def timeOutEvent(self):
        self.lastTimeOutWnd = self.windowSize
        self.windowSize = 4
        self.clearBuffer()
        self.reSendPackets()


    def sendPackets(self):
        # print("index : ", self.index)
        # print("status: ", self.status)
        while self.mutex == 2:
            continue
        self.mutex = 1
        for x in range(0, self.length):
            if self.status[x] == 0:
                self.status[x] = 1
                self.socketInstance.sendto(self.cache[x], self.ip_port)
            if self.index[x] > self.recevDataSeq + 10:
                break
        self.mutex = 0

    def reSendPackets(self):
        print("resend")
        print("index : ", self.index)
        print("status: ", self.status)
        while self.mutex == 2:
            continue
        self.mutex = 1
        for x in range(0, self.length):
            if self.status[x] == 1:
                self.socketInstance.sendto(self.cache[x], self.ip_port)
            if self.index[x] > self.recevDataSeq + 5:
                break
        self.mutex = 0

    def putPacketIntoBuffer(self, data, sa):
        # print("want to put data:")
        # print("index : ", self.index)
        # print("status: ", self.status)
        if (self.isSender and self.length >= self.windowSize):
            return False;
        while self.mutex == 2:
            continue
        self.mutex = 1
        self.status.append(0)
        self.cache.append(data)
        self.index.append(sa)
        self.length += 1
        self.mutex = 0
        return True

    def readyToSend(self):
        if self.length >= self.windowSize // 4 or self.recevDataSeq >= self.maxDataSeq - 5:
            return True
        return False

    def setWindowSize(self, sWnd):
        if sWnd < self.windowSize:
            self.windowSize = sWnd

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
        self.length -= 1
        self.mutex = 0
        return data

    def getAllPacketFromBuffer(self):
        if self.length <= 0:
            return
        while self.mutex == 1:
            continue
        self.mutex = 1
        data = self.cache
        self.status = []
        self.cache = []
        self.index = []
        self.length = 0
        self.mutex = 0
        return data

    def getData(self):
        count = 1000
        t = 0
        while self.recevDataSeq < self.maxDataSeq:
            datagram, clientAddress = self.socketInstance.recvfrom(helper.BUFSIZE)
            header = datagram[:10]
            data = datagram[10:]
            seq = helper.getSeq(header)

            # print("seq, recevDataSeq : ", seq, self.recevDataSeq)
            # reply ack, ack = seq
            if (seq <= self.recevDataSeq + 1):
                self.socketInstance.sendto(helper.createHeader(0, seq, helper.memoryBuffer-self.length), self.ip_port)
            if seq == self.recevDataSeq + 1:
                self.putPacketIntoBuffer(data, seq)
                self.recevDataSeq = seq
                if t > count:
                    print(count)
                    t += 1
                    count += 1000
        self.writeFileOver = 1

    def autoWriteFile(self):
        while self.writeFileOver == 0:
            if self.length > 0:
                data = self.getAllPacketFromBuffer()
                for x in range(0, len(data)):
                    self.file.write(data[x])
        if self.length > 0:
            print("last time to write data")
            data = self.getAllPacketFromBuffer()
            for x in range(0, len(data)):
                self.file.write(data[x])
        self.file.close()

    def getACK(self):
        self.socketInstance.settimeout(3)
        while self.recevDataSeq < self.maxDataSeq:
            try:
                ACKDatagram, addr = self.socketInstance.recvfrom(helper.BUFSIZE)
                ACK = helper.getACK(ACKDatagram[:10])
                sWnd = helper.getWindow(ACKDatagram[:10])
                # print("ACK: ", ACK)
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
                        break
                self.clearBuffer()
                self.increaseWindowSize()
                self.setWindowSize(sWnd)
            # finally:
                # print("index : ", self.index)
                # print("status: ", self.status)
        print("get ACK over")

    def clearBuffer(self):
        if self.length <= 0:
            return
        while self.mutex == 1:
            continue
        self.mutex = 2
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
