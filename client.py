import os
import socket
import LFTPHelper as helper
import threading
BUFSIZE = 1024
packetSize = 200

server_MessageListener_Port = 3000

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clientSocket.bind(("", 0)) # automatically bind IP and port
dataPath = ".\\data\\"
dirPath = os.path.realpath(".\\data\\") + "\\"


# main
message = input("Command format: LFTP lsend/lget serverAddress fileName\n")
message = message.split()
server_IP = message[2]
server_IP_Port = (server_IP, server_MessageListener_Port)

if (message[1] == "lget"):
    # download
    fileName = message[3]
    clientSocket.sendto(helper.createMessage(1, 1, 0, 0, fileName), server_IP_Port)
    feedback, server_IP_Port = clientSocket.recvfrom(BUFSIZE)
    state = helper.getState(feedback)
    if (state == 1):
        fileSize = helper.getFileSize(feedback)
        packetsNum = fileSize//packetSize
        transferPort = helper.getTransferPort(feedback)
        print("Port:", transferPort)
        fileObject = open(dataPath + fileName, "wb")
        receiver = helper.receiver(clientSocket, (server_IP, transferPort), fileObject, packetsNum)
        receiveFileTread = threading.Thread(target = receiver.receiveFile)
        receiveFileTread.start()
        # clientSocket.sendto(helper.createMessage(1, 1, 0, 0, ""), server_IP_Port)
    else:
        print(helper.errorMessage[state])

elif (message[1] == "lsend"):
    # upload
    # read file and get its size
    try:
        fileName = message[3]
        fileSize = os.path.getsize(dataPath + fileName)
        packetsNum = fileSize//packetSize
        fileObject = open(dirPath + fileName, "rb")
    except Exception as e:
        # open file fails
        print(e)
    else:
        clientSocket.sendto(helper.createMessage(0, 1, 0, fileSize, fileObject.name), server_IP_Port)
        feedback, server_IP_Port = clientSocket.recvfrom(BUFSIZE)

        state = helper.getState(feedback)
        if (state == 1):
            transferPort = helper.getTransferPort(feedback)

            sender = helper.sender(clientSocket, (server_IP, transferPort), fileObject, packetsNum)
            sendFileTread = threading.Thread(target = sender.receiveFile)
            sendFileTread.start()
        else:
            print(helper.errorMessage[state])
else:
    print(error)
