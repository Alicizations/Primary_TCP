import socket
import LFTPHelper as helper

address = '192.168.199.111'
UDPport = 5005
BUFSIZE = 1024

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverSocket.bind((address, UDPport))


fileData = bytes(0)
while True:
    datagram, clientAddress = serverSocket.recvfrom(BUFSIZE)

    header = datagram[:160]
    content = datagram[160:]
    #print(str(header))

    sourcePort, destPort, sequenceNum, ackNum, SYN, FIN, window = helper.parseHeader(str(header))
    print(str(header)[111])
    print(str(header)[112])
    print(str(header)[113])
    print(FIN)
    # checking
    # do something

    # if checking passed

    ackNum = sequenceNum + len(content) // 8 + 1
    response = helper.createHeader(sourcePort, destPort, sequenceNum, ackNum)
    serverSocket.sendto(bytes(response, "ascii"), clientAddress)
    if (FIN):
        fileName = "1.jpg"
        break
    else:
        fileData += content

print("out?")
file = open("./data/1.jpg", "wb")
file.write(fileData)
file.close()



