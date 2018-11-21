import socket

IP_PORT = ('192.168.199.111', 5005)
BUFSIZE = 1024
UDP_Client = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
Header = [0 for x in range(0,20)]
Seq = 0

f = open('./data/lena.jpg', 'rb') #打开文件

seg = f.read(200)
time = 1

while len(seg):
    packetHeader = Header.copy()
    packetData = seg
    seg = f.read(200)
    if len(seg) == 0:
        packetHeader[14] = 1
    packetHeader[7] = Seq % 256;
    packetHeader[6] = (Seq >> 8) % 256;
    packetHeader[5] = (Seq >> 16) % 256;
    packetHeader[4] = (Seq >> 24);
    Seq += 200;
    packet = bytes(packetHeader) + packetData
    UDP_Client.sendto(packet, IP_PORT)
    back_msg, addr = UDP_Client.recvfrom(BUFSIZE)
    print(back_msg, addr)

f.close() #关闭文件



# def SetSourcePort(header):
#     pass

# def SetTargetPort(header):
#     pass

# def SetIndex(header):
#     pass

# def SetConfirmNum(header):
#     pass

# def SetACK(header):
#     pass

# while True:
#     msg = input('>>: ').strip()
#     if not msg:
#         continue

#     UDP_Client.sendto(a, IP_PORT)
