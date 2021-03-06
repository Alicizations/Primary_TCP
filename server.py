import socket
import threading
import os
import LFTPHelper as helper
import math

server_IP = ""
server_IP_Port = ("", 3000) # bind IP automatically
messageListener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
messageListener.bind(server_IP_Port)
dataPath = ".\\data\\"
dirPath = os.path.realpath(".\\data\\") + "\\"

ports = [5000, 5001, 5002, 5003, 5004, 5005, 5006, 5007, 5008, 5009]
threadLock = [False for x in range(10)]
availableThread = [None for x in range(10)]
UDPSocketPool = [None for x in range(10)]
nextPort = 0

def findAvailablePorts():
    for i in range(0, 10):
        if  threadLock[i] == False and (availableThread[i] is None or availableThread[i].is_alive() == False):
            if (UDPSocketPool[i] is not None):
                UDPSocketPool[i].close() # close a socket if no longer used
            threadLock[i] = True
            return i + 5000
    return -1

# main
print("[Server]          LFTP server is running")
while(True):
    message, client_IP_Port = messageListener.recvfrom(helper.BUFSIZE)
    print("[Server]          get request, try to assign an available port")
    availablePort = findAvailablePorts()
    if (availablePort in ports):
        print("[Server][", availablePort, "]  find port")
        if helper.getIsDownload(message):
            # client want to download
            try:
                fileName = helper.getFileName(message)
                fileSize = os.path.getsize(dirPath + fileName)
                packetsNum = math.ceil(fileSize / helper.packetSize)
                fileObject = open(dataPath + fileName, "rb")
            except Exception as e:
                # open file fails
                print(e)
                messageListener.sendto(helper.createMessage(0, 2, 0, 0, ""), client_IP_Port)
            else:
                messageListener.sendto(helper.createMessage(0, 1, availablePort, fileSize, ""), client_IP_Port)

                senderUDPSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                senderUDPSocket.bind((server_IP, availablePort))
                UDPSocketPool[availablePort-5000] = senderUDPSocket
                # new a thread to transfer
                sender = helper.sender(availablePort, senderUDPSocket, client_IP_Port, fileObject, packetsNum)
                sendFileTread = threading.Thread(target = sender.sendFile)
                availableThread[availablePort-5000] = sendFileTread
                sendFileTread.start()
                threadLock[availablePort-5000] = False
                print("[Server][", availablePort, "]  server start to send file: ", fileName)
        else:
            # client want to upload
            fileName = helper.getFileName(message)
            fileSize = helper.getFileSize(message)
            packetsNum = packetsNum = math.ceil(fileSize / helper.packetSize)
            fileObject = open(dataPath + fileName, "wb")

            messageListener.sendto(helper.createMessage(0, 1, availablePort, 0, ""), client_IP_Port)

            receiverUDPSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            receiverUDPSocket.bind((server_IP, availablePort))
            UDPSocketPool[availablePort-5000] = receiverUDPSocket
            # new a thread to transfer
            receiver = helper.receiver(availablePort, receiverUDPSocket, client_IP_Port, fileObject, packetsNum)
            receiveFileTread = threading.Thread(target = receiver.receiveFile)
            availableThread[availablePort-5000] = receiveFileTread
            receiveFileTread.start()
            print("[Server][", availablePort, "]  server start to receive file: ", fileName)

    else:
        # no available port
        print("[Server]  no available port, response to client")
        messageListener.sendto(helper.createMessage(0, 3, 0, 0, ""), client_IP_Port)