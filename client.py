import socket
import LFTPHelper as helper

IP_PORT = ('192.168.199.111', 5005)
BUFSIZE = 1024
UDP_Client = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

f = open('./data/lena.jpg', 'rb') #打开文件

seg = f.read(200)
Seq = 0
SYN = 1
FIN = 0
WindowSize = 20

while len(seg):
    packetData = seg
    seg = f.read(200)
    if len(seg) == 0:
        FIN = 1
    packetHeader = helper.createHeader(0, 5005, Seq, 0, SYN, FIN, WindowSize)

    Seq += 200
    SYN = 0
    packet = bytes(packetHeader, 'ascii') + packetData
    UDP_Client.sendto(packet, IP_PORT)
    back_msg, addr = UDP_Client.recvfrom(BUFSIZE)
    print(back_msg, addr)

f.close()
