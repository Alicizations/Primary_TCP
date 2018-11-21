import socket
import LFTPHelper as helper

ip_port = ('192.168.199.111', 5005)
BUFSIZE = 1024

udp_server_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

udp_server_client.bind(ip_port)

sequnceNumIndex = 8
dataIndex = 40


buffer = bytes()
while True:
    msg, addr = udp_server_client.recvfrom(BUFSIZE)
    print(msg, addr)

    receiveNum = msg[sequnceNumIndex:sequnceNumIndex+8]

    ACK = int.from_bytes( receiveNum, "big", signed=False) + 1
    buffer += msg[dataIndex:]

    ACKBinary = bin(ACK)[2:].zfill(32)
    ACKByte = int(ACKBinary, 2).to_bytes( (len(ACKBinary) + 7 ) // 8, 'big')

    response = bytes(16) + ACKByte + bytes(16)

    udp_server_client.sendto(response, addr)


