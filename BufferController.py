import threading as tr
import LFTPHelper as helper

class BufferController:
    """docstring for BufferController"""
    isSender = 0            # sender or not
    isServer = 0            # server or not
    socketInstance = 0      # socket instance
    windowSize = 4          # window size
    length = 0              # buffer's length
    status = []             # 0:not send, 1:sent not ack, 2:acked
    cache = []              # data cache
    index = []              # data seq
    maxDataSeq = 0          # max seq
    recevDataSeq = 0        # next recev/acked max seq
    file = 0                # file pointer (already open)
    onRecev = 0             # control recev func
    ip_port = 0             # (ip, port)
    mutex = 0               # mutex for length, 0:idle, 1:sending and putting 2:clearing acked seq
    writeFileOver = 0       # flag for stopping file writing
    sending = 0             # send status
    lastTimeOutWnd = 15     # last time-out window size
    maxWnd = 30             # buffer max window size
    timeOutCount = 0        # continual timeOut counter
    def __init__(self, _isSender, _isServer, _socketInstance, _ip_port, _file = 0, _maxDataSeq = 0):
        self.isSender = _isSender
        self.isServer = _isServer
        self.socketInstance = _socketInstance
        self.file = _file
        self.ip_port = _ip_port
        self.maxDataSeq = _maxDataSeq
        self.windowSize = 4
        self.length = 0;
        self.status = []
        self.cache = []
        self.index = []
        self.recevDataSeq = 0
        self.onRecev = 0
        self.mutex = 0
        self.writeFileOver = 0
        self.sending = 0
        self.lastTimeOutWnd = 15
        self.maxWnd = 30
        self.timeOutCount = 0


    # 增加窗口大小
    def increaseWindowSize(self):
        if self.windowSize >= self.maxWnd:
            return
        if self.windowSize < self.lastTimeOutWnd:
            self.windowSize *= 2
        else:
            self.windowSize += 1

    # 超时处理
    def timeOutEvent(self):
        self.lastTimeOutWnd = self.windowSize
        self.windowSize = 4
        self.timeOutCount += 1
        if self.timeOutCount >= 3:
            self.recevDataSeq = self.maxDataSeq + 1
            if self.isServer == 0:
                print("\nreceiver gone, LFTP exit")
            else:
                print("[Server][", self.isServer, "]  client receiver no response")
                print("[Server][", self.isServer, "]  release port")
            exit()
        # self.clearBuffer()
        self.reSendPackets()

    # 发送数据包
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
            if self.index[x] > self.recevDataSeq + self.windowSize // 2:
                break
        self.mutex = 0

    # 重发数据包
    def reSendPackets(self):
        # print("resend")
        # print("index : ", self.index)
        # print("status: ", self.status)
        while self.mutex == 2:
            continue
        self.mutex = 1
        for x in range(0, self.length):
            if self.status[x] == 1:
                self.socketInstance.sendto(self.cache[x], self.ip_port)
            if self.index[x] > self.recevDataSeq + 5:
                break
        self.mutex = 0

    # 将数据包放入缓冲
    def putPacketIntoBuffer(self, data, sa):
        self.clearBuffer()
        # print("want to put data:")
        # print("index : ", self.index)
        # print("status: ", self.status)
        if (self.isSender and self.length >= self.windowSize):
            return False;
        while self.mutex == 2:
            continue
        self.mutex = 1
        self.cache.append(data)
        #if self.isSender:
        #    if self.recevDataSeq + self.windowSize // 2 <= sa:
        #        self.socketInstance.sendto(data, self.ip_port)
        #        self.status.append(1)
        #        self.index.append(sa)
        #        self.length += 1
        #    else:
        #    self.status.append(0)
        #    self.index.append(sa)
        #    self.length += 1
        #        self.sendPackets()
        #else:
        self.status.append(0)
        self.index.append(sa)
        self.length += 1
        self.mutex = 0
        return True

    # 可以发送状态
    def readyToSend(self):
        if self.length >= self.windowSize // 4 or self.recevDataSeq >= self.maxDataSeq - 5:
            return True
        return False

    # 结束
    def isEnd(self):
        return self.recevDataSeq <= self.maxDataSeq

    # 设置窗口大小
    def setWindowSize(self, sWnd):
        if sWnd < self.windowSize:
            self.windowSize = sWnd

    # 从缓冲拿数据包
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

    # 从缓冲拿全部数据包
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

    # 接受数据包
    def getData(self):
        count = self.maxDataSeq/40
        t = 0
        self.socketInstance.settimeout(10)
        while self.recevDataSeq <= self.maxDataSeq:
            try:
                datagram, clientAddress = self.socketInstance.recvfrom(helper.BUFSIZE)
            except Exception as e:
                if self.isServer == 0:
                    print("\n")
                    print(e)
                    print("server is disconnected")
                else:
                    print("[Server][", self.isServer, "]  Error:")
                    print(e)
                    print("[Server][", self.isServer, "]  client sender is disconnected")
                    print("[Server][", self.isServer, "]  release port")
                self.recevDataSeq = self.maxDataSeq + 1
                break
            else:
                header = datagram[:10]
                data = datagram[10:]
                seq = helper.getSeq(header)
                # print("seq, recevDataSeq : ", seq, self.recevDataSeq)

                # receive in-order packet
                if seq == self.recevDataSeq:
                    self.putPacketIntoBuffer(data, seq)
                    self.recevDataSeq = seq + 1
                    t += 1
                    if t > count:
                        if (self.isServer):
                            pass
                        else:
                            helper.updateProgressBar(self.recevDataSeq/self.maxDataSeq, self.file.name, self.ip_port)
                        count += self.maxDataSeq/40

                # reply ack = seq if packet is in order
                # reply ack = max recev seq no matther receiving advanced packet or delayed packet
                ACK = self.recevDataSeq
                # rwdn is the remaining space of buffer
                rwdn = helper.memoryBuffer-self.length
                self.socketInstance.sendto(helper.createHeader(0, ACK, rwdn), self.ip_port)
        self.writeFileOver = 1

    # 将文件写入硬盘
    def autoWriteFile(self):
        while self.writeFileOver == 0:
            if self.length > 0:
                data = self.getAllPacketFromBuffer()
                for x in range(0, len(data)):
                    self.file.write(data[x])
        if self.length > 0:
            data = self.getAllPacketFromBuffer()
            for x in range(0, len(data)):
                self.file.write(data[x])
        if self.isServer == 0:
            print("\ndownload complete")
        else:
            print("[Server][", self.isServer, "]  file already receive")
            print("[Server][", self.isServer, "]  release port")
        self.file.close()

    # 接受ack
    def getACK(self):
        self.socketInstance.settimeout(3)
        count = self.maxDataSeq/40
        t = 0
        while self.recevDataSeq <= self.maxDataSeq:
            try:
                ACKDatagram, addr = self.socketInstance.recvfrom(helper.BUFSIZE)
                ACK = helper.getACK(ACKDatagram[:10])
                sWnd = helper.getWindow(ACKDatagram[:10])
            except Exception as e:
                if self.isServer == 0:
                    print("\n")
                    print(e)
                    print("TimeOut!")
                else:
                    print("[Server][", self.isServer, "]  Error:")
                    print(e)
                    print("[Server][", self.isServer, "]  file already receive")
                    print("[Server][", self.isServer, "]  release port")
                self.timeOutEvent()
            else:
                if self.recevDataSeq < ACK:
                    self.recevDataSeq = ACK
                    t += 1
                    if t > count:
                        if (self.isServer):
                            pass
                        else:
                            helper.updateProgressBar(self.recevDataSeq/self.maxDataSeq, self.file.name, self.ip_port)
                        count += self.maxDataSeq/40

                for x in range(0, self.length):
                    if (self.index[x] <= ACK - 1):
                        self.status[x] = 2
                    if (self.index[x] > ACK - 1):
                        break
                #self.sendPackets()
                self.setWindowSize(sWnd)
                self.increaseWindowSize()
                self.timeOutCount = 0
        self.recevDataSeq = self.maxDataSeq + 1
        if self.isServer == 0:
            print("\nget ACK over")
        else:
            print("[Server][", self.isServer, "]  send file over")
            print("[Server][", self.isServer, "]  release port")

    # 清理已ack包
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

    # 开启接受
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
