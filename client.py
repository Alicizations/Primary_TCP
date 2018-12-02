import socket
import LFTPHelper as helper
import BufferController as bController

IP_PORT = ('192.168.199.111', 5005)
BUFSIZE = 1024
UDP_Client = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
UDP_Client.bind(('192.168.199.129', 5005))

f = open('./data/lena.jpg', 'rb') #打开文件


Seq = 0
FIN = 0
WindowSize = 20

working = 1
controller = bController.BufferController(1, UDP_Client, IP_PORT, 0, 38984//200)

controller.openReceive()

while working:
    while controller.notFull():
        packetData = f.read(200)
        if len(packetData) == 0:
            FIN = 1
            # controller.sendPackets(IP_PORT)
            working = 0
            break

        packetHeader = helper.createHeader(0, 5005, Seq, 0, 0, FIN, WindowSize)

        packet = packetHeader + packetData
        print("seq: ", Seq)
        controller.putPacketIntoBuffer(packet, Seq)

        controller.sendPackets()
        Seq += 1
    

f.close()

# 发送方读文件填充buffer, 发送, 接受ack, 把ack了包pop, 读文件填充buffer, 继续发送
# 接收方每接受三个包回一个ack