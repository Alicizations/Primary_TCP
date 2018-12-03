import os
import socket
import LFTPHelper as helper
import threading
import math


server_MessageListener_Port = 3000

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clientSocket.bind(("", 0)) # automatically bind IP and port
dataPath = ".\\data\\"
dirPath = os.path.realpath(".\\data\\") + "\\"


# main
message = input("Command format: LFTP lsend/lget serverAddress fileName\n")
message = message.split()
if len(message) != 4:
    print("Invalid Command, LFTP exit")
    exit()
else:
    server_IP = message[2]
    server_IP_Port = (server_IP, server_MessageListener_Port)

if (message[1] == "lget"):
    # download
    fileName = message[3]
    clientSocket.settimeout(4)
    clientSocket.sendto(helper.createMessage(1, 1, 0, 0, fileName), server_IP_Port)
    try:
        feedback, server_IP_Port = clientSocket.recvfrom(helper.BUFSIZE)
    except Exception as e:
        print("Server no response, LFTP exit")
    else:
        state = helper.getState(feedback)
        if (state == 1):
            fileSize = helper.getFileSize(feedback)
            packetsNum = math.ceil(fileSize / helper.packetSize) - 1
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
        packetsNum = math.ceil(fileSize / helper.packetSize) - 1
        fileObject = open(dirPath + fileName, "rb")
    except Exception as e:
        # open file fails
        print(e)
    else:
        clientSocket.settimeout(4)
        clientSocket.sendto(helper.createMessage(0, 1, 0, fileSize, fileName), server_IP_Port)
        try:
            feedback, server_IP_Port = clientSocket.recvfrom(helper.BUFSIZE)
        except Exception as e:
            print("Server no response, LFTP exit")
        else:
            state = helper.getState(feedback)
            if (state == 1):
                transferPort = helper.getTransferPort(feedback)
                print("Port:", transferPort)
                sender = helper.sender(clientSocket, (server_IP, transferPort), fileObject, packetsNum)
                sendFileTread = threading.Thread(target = sender.sendFile)
                sendFileTread.start()
            else:
                print(helper.errorMessage[state])
else:
    print(error)
