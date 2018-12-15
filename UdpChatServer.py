#!/usr/bin/python
#UdpChatServer.py by Tianen Chen
#UNI: tc2841
#date: 3/1/2017

#This program serves as a handler for all messages and broadcasts who logs in to all clients logged into the server
#It's main function is to recognize who logs in and logs off and store/broadcast offline messages

import socket 
import time
import threading
import sys
import datetime
import time
import warnings




#Start up my program with associated global variables
def main():
	global serverIP
	global serverPort
	global serverSocket
	global masterList
	global onlineList
	global offlineMessageKeychain
	warnings.filterwarnings("ignore")
#NOTE: SERVER IP IS ASSUMED TO BE KNOWN AMONG ALL CLIENTS..DEFAULT SET AS LOCALHOST
	masterList = []
	onlineList = []
	offlineMessageKeychain = []
	serverIP = '127.0.0.1'
#Make sure that the entered port is correct
	try:
		serverPort = int(sys.argv[1])
		print '>>> [Server started.]'
	except:
		print '>>> [Invalid port entered for server]'
		serverPort = 4000
		KeyboardInterrupt
		sys.exit()
#set up socket
	serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	serverSocket.bind((serverIP,serverPort))

#Listen for commands from the clients
def listen():
	while 1:
		message = serverSocket.recv(1024)
		messageParts = message.split('|')
	#	print message
		command = messageParts[0]
#Make a command that tells the server which subroutine to run
		if command == 'LOGINFIRST':
			firstMasterList(message)
			createSendOnlineList(message)
		if command == 'DEREG':
			removeSendOnlineList(message)
		if command == 'OFFLINEATTEMPT':
			storeOfflineMessage(message)
		if command == 'REGBACK':
			createSendOnlineList(message)
			sendOfflineMessage(message)

#This function broadcasts all offline messages upon re-registration to the specified client
def sendOfflineMessage(message):
	global offlineMessageKeychain
	messageParts = message.split('|')
	relogName = messageParts[1]
	relogIP = messageParts[2]
	relogPort = int(messageParts[3])
	messageBlast = []
	messageCheck = 0
	newList = []
	for key in offlineMessageKeychain:
		if key[0] == relogName:
			fromName = key[3]
			offMess = key[4]
			messageToSend = fromName + ": " + offMess
			messageBlast.append(messageToSend)
			messageCheck = 1
#Append all offline messages to their respective user along with who the message came from
	for key in offlineMessageKeychain:
		if key[0] != relogName:
			newList.append((key[0],key[1],key[2],key[3],key[4]))
	offlineMessageKeychain = newList
	if messageCheck == 1:
		finalSend = "OFFLINEMESSAGE|" + str(messageBlast)
		serverSocket.sendto(finalSend, (relogIP, relogPort))
	if messageCheck == 0:
		finalSend = "OFFLINEMESSAGE|"

#Send out the masterlist of users who have ever logged in
def firstMasterList(message):
	messageParts = message.split('|')
	loginName = messageParts[1]
	loginIP = messageParts[2]
	loginPort = int(messageParts[3])
	masterKey = ((loginName, loginIP, loginPort))
	isUserInFlag = 0 
#Rejects clients who try to sign in with a nickname already in use
	for i in masterList:
		if i[0] == loginName:
			isUserInFlag = 1
			outMessage = 'NICKNAMEEXCEPT'
	if isUserInFlag == 1:
		serverSocket.sendto(outMessage, (loginIP, loginPort))
	if isUserInFlag == 0:
		masterList.append(masterKey)
	for users in masterList:
		stringMasterList = str(masterList)
		outMessage = "MASTERLIST|" + stringMasterList
		targetIP = users[1]
		targetPort = int(users[2])
		serverSocket.sendto(outMessage, (targetIP, targetPort))


#Create an online list of who is currently online and broadcast whenever a new person logs on or off.
def createSendOnlineList(message):
	messageParts = message.split("|")	
	loginName = messageParts[1]
	loginIP = messageParts[2]
	loginPort = messageParts[3]
	onlineKey = ((loginName, loginIP, loginPort))
	isInFlag = 0
	for i in onlineList:
		if i[0] == loginName:
			isInFlag = 1
#We append the tuple with log in information to the onlineList in order to create an array of who's online.
	if isInFlag == 0:
		onlineList.append(onlineKey)
	for users in masterList:
		stringOnlineList = str(onlineList)
		outMessage = "ONLINELIST|" + stringOnlineList
		targetIP = users[1]
		targetPort = int(users[2])
		serverSocket.sendto(outMessage, (targetIP, targetPort))

#Likewise, this does the same thing as the above function, but instead of appending, removes the tuple associated with a client from the online list.
def removeSendOnlineList(message):
#Here is where we send back the acknowledgement of successful deregistration
#Our client on the other side is going to try 6 times to get this acknowledgement. (1 initial try, 5 more retries)
	deregSuccessAck = 'DEREGSUCCESS'
	messageParts = message.split('|')
	loginName = messageParts[1]
	loginIP = messageParts[2]
	loginPort = messageParts[3]
	onlineKey = ((loginName, loginIP, loginPort))
	realPort = int(messageParts[3])
#Create online list tuple that is appended and used as a data structure
	serverSocket.sendto(deregSuccessAck, ((loginIP, realPort)))
	for users in onlineList:
		if users[0] == loginName:
			try:
				onlineList.remove(onlineKey)
			except:
				pass
	for users in masterList:
		stringOnlineList = str(onlineList)
		outMessage = "ONLINELIST|" + stringOnlineList
		targetIP = users[1]
		targetPort = int(users[2])
		serverSocket.sendto(outMessage, (targetIP, targetPort))

#This stores all offline messages sent to the server
def storeOfflineMessage(message):
	messageParts = message.split("|")
	toName = messageParts[1]
	toPort = messageParts[2]
	toIP = messageParts[3]
	activeUserFlag = 0
#Here, we make sure the user is actually offline before making appending the "offline message key chain"
	for users in onlineList:
		if users[0] == toName:
			activeUserFlag = 1
	if activeUserFlag == 0:
		fromName = messageParts[4]
		messageSend = messageParts[7]
		offLineMessageKey = (toName, toPort, toIP, fromName, messageSend)
		offlineMessageKeychain.append(offLineMessageKey)
#Here, we make note that the client is actually online and we sh
	if activeUserFlag == 1:
		offlineFail  = 'OFFLINEFAIL|' + toName
		fromIP = messageParts[5]
		fromPort = int(messageParts[6])
		serverSocket.sendto(offlineFail, ((fromIP, fromPort)))

#Start up my listening thread
if __name__ == '__main__':		
	main()
#Make threads daemon in order to succesfully close program
	listen_thread = threading.Thread(target=listen, args=())
	listen_thread.daemon = True
	listen_thread.start()
#Makes sure my keyboard interrupt shuts down the entire server and kills the chat client for all users upon server shutdown.
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		outMessage = 'COMPLETESHUTDOWN'
		for key in masterList:
			serverSocket.sendto(outMessage, (key[1],int(key[2])))
		print ">>> [Server shutdown]"