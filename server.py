import socket
import threading
import os
import LFTPHelper as helper
import BufferController as B

packetSize = 200
BUFSIZE = 1024

server_IP = "192.168.199.111"
server_IP_Port = ("192.168.199.111", 3000)
commandListener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
commandListener.bind(server_IP_Port)
uploadPath = "C:/Users/user/Desktop/Primary_TCP/date/"

ports = [5000, 5001, 5002, 5003, 5004, 5005, 5006, 5007, 5008, 5009]
threadLock = [False for x in range(10)]
availableThread = [None for x in range(10)]

def findAvailablePorts():
    for i in range(0, 10):
        if  threadLock[i] == False and (availableThread[i] is None or available[i].is_alive() == False):
            threadLock[i] = True
            return i + 5000
    return -1

# main
while(True):
    command, client_IP_Port = commandListener.recvfrom(BUFSIZE)

    serverPort = findAvailablePorts()
    if (serverPort in ports):
        if helper.getIsDownload(command):
            # client want to download
            try:
                filePath = getFilePath(command)
                fileSize = os.path.getsize(filePath)
                packetsNum = fileSize // packetSize
                fileObject = open(filePath, "rb")
            except Exception as e:
                # open file fails
                print(e)
                commandListener.sendto(helper.createCommand(0, 2, 0, 0, ""), client_IP_Port)
            else:
                commandListener.sendto(helper.createCommand(0, 1, serverPort, fileSize, ""), client_IP_Port)
                sender = helper.sender((server_IP, availablePort), client_IP_Port, fileObject, packetsNum)
                sendFileTread = threading.Thread(target = sender.sendFile)
                sendFileTread.start()
                threadLock[serverPort-5000] = False
        else:
            # client want to upload
            fileName = getFilePath(command) # filename indeed
            fileSize = getFileSize(command)
            packetsNum = fileSize // packetSize
            fileObject = open(uploadPath + fileName, "wb")

            commandListener.sendto(helper.createCommand(0, 1, 0, 0, ""), client_IP_Port)
            receiver = helper.receiver((server_IP, availablePort), client_IP_Port, fileObject, packetsNum)
            receiveFileTread = threading.Thread(target = receiver.receiveFile)
            receiveFileTread.start()

    else:
        # no available port
        commandListener.sendto(helper.createCommand(0, 3, 0, 0, ""), client_IP_Port)