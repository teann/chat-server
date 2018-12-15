#!/usr/bin/python
#UdpChat.py by Tianen Chen
#UNI: tc2841
#3/1/2017

#This program serves as a "client" for my UdpChat. 
#It's main functions are to handle incoming messages from the server and client and send commands (send, reg, dereg) to the server and other clients.

import socket 
import time
import threading
import sys
import time
import datetime
import os

#Main function starts up the program, declares all global variables, and takes the user input.
def main():
	global nickname
	global serverIP
	global serverPort
	global clientPort
	global clientIP
	global clientSocket
	global clientOnline
	global onlineList
	global masterList
	global ACKRECEIVED
	global sentinalkill
	global sendTrue

	sendTrue = 1

#Makes sure the user is inputting the right thing
	sentinalkill = 0
	try:
		nickname = str(sys.argv[1])
#NOTE: SERVER IP IS SET TO LOCALHOST
		serverIP = str(sys.argv[2])
		serverPort = int(sys.argv[3])
		clientPort = int(sys.argv[4])
	except:
		print '>>> [Invalid input please try again]'
		print '>>> [Input must be in the form of "python UdpChat.py <NICKNAME> <SERVERIP> <SERVERPORT> <YOUR PORT>"'
		sentinalkill = 1
		sys.exit()

#Sets up the socket
#Binds to its own IP and port.
	clientIP = socket.gethostbyname(socket.getfqdn())
	masterList = []
	onlineList = []
	clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	clientSocket.bind((clientIP,clientPort))	
	print '>>> [Welcome, you are registered]'
	firstLoginKey = 'LOGINFIRST|' + nickname + '|' + clientIP + '|' + str(clientPort)
	clientSocket.sendto(firstLoginKey, (serverIP, serverPort))

#The sending thread is here. We take user input as send, reg, or derg
def send():
	while sendTrue == 1:
		input = raw_input()
		inputParts = input.split(None, 2)
		command = inputParts[0]
		try:
			targetName = inputParts[1]
		except:
			targetName = 'null'

		offlineFlag = 0
		realUserFlag = 0 
		global ACKRECEIVED
		ACKRECEIVED = 0
#Send command preocedure. If the user types send followed by a username, we check if the target person is active on our local table
		if command == 'send':
			for i in onlineList: 
				if targetName == i[0]:
					actualMessage = inputParts[2]
					targetIP = i[1]
					targetPort = int(i[2])
					outMessage = 'DM|' + nickname + '|' + clientIP + '|' + str(clientPort) + '|' + actualMessage
					offlineFlag = 1
					clientSocket.sendto(outMessage, (targetIP, targetPort))
#Check if user even exists via masterList
			for i in masterList:
				if targetName == i[0]:
					targetIP = i[1]
					targetPort = int(i[2])
					realUserFlag = 1
			if offlineFlag == 0 and realUserFlag == 0:
				print '>>> [No such user exists within this chat client.]'
				targetIP = 'null'
				targetPort = 00
				actualMessage = 'null'
#Timeout occurs if the acknowledgement is not received
#If the timeout occurs, send the message to the server
			timeout = time.time() + .5
			while 1:
				if ACKRECEIVED == 1:
					print '>>> [Message received by ' + targetName + ' ]'
					break
				if ACKRECEIVED == 0 and time.time() > timeout:
					actualMessage = inputParts[2]
					#print "actual messaage: " + actualMessage
					offlineMessageToServer(actualMessage, targetName, targetIP, targetPort)
					print '>>> [No ack received, messaage sent to server]'
					break	
#Run through the procedure that allows us to register and deregister our client
		elif command == 'reg':
			regBack()
		elif command == 'dereg':
			deReg()
		else:
			print '>>> [Not a recognized command.]'		






#regBack is the "reg" command the client sends
#Updates the online list at the server
def regBack():
	outMessage = 'REGBACK|' + nickname + '|' + clientIP + '|' + str(clientPort)
	onlineList.append((nickname, clientIP, clientPort))
	clientSocket.sendto(outMessage, (serverIP, serverPort))


#deReg is the "dereg" command the client sends
def deReg():
	global deregACK
	global sentinalkill
#Here, we check for the acknowledgement from the server
#We try once, then retry 5 more times. Hence, that is why tryCount is limited to 6 before killing hte program.
	timeout = time.time() + .5
	tryCount = 1
	deregACK = 0
	while 1:
		if deregACK == 1:
			print ">>> [You are offline. Bye.]"
			break
		if deregACK == 0 and time.time() > timeout and tryCount <= 6:
			outMessage = 'DEREG|' + nickname + '|' + clientIP + '|' + str(clientPort)
			clientSocket.sendto(outMessage, (serverIP, serverPort))
			tryCount = tryCount + 1
		if tryCount > 6:
			print '>>> [Server not responding]'
			print '>>> [Exiting]'
			sentinalkill = 1 
			break
				
#listen	is the listening thread that handles all information coming from server and other clients		
def listen():
	global sendTrue
	while 1:
		message = clientSocket.recv(1024)
		messageParts = message.split('|')
		command = messageParts[0]
#Receives the message, and based on the "key", directs the program to go to other functions that handle the command
		if command == "DM":
			fromName = messageParts[1]
			fromIP = messageParts[2]
			fromPort = int(messageParts[3])
			actualMessage = messageParts[4]
			onlineDMPrint(actualMessage, fromName, fromIP, fromPort)
		if command == 'DMACK':
			global ACKRECEIVED
			ACKRECEIVED = 1
		if command == 'DEREGSUCCESS':
			global deregACK
			deregACK = 1
		if command == 'MASTERLIST':
			storeMasterList(message)
		if command == 'ONLINELIST':
			storeOnlineList(message)
		if command == 'OFFLINEMESSAGE':
			printOfflineMessage(message)
		if command == 'REMOVEONLINELIST':
			removeOnlineList(message)
		if command == 'COMPLETESHUTDOWN':
			deReg()
#This prevents users from signing in with nickname already in use
		if command == 'NICKNAMEEXCEPT':
			print '>>> [You have registered with a nickname already in use.]'
			print '>>> [You have been disconnected from the server with specified port and IP.]'
			print '>>> [Press ctrl+c and try signing in with a nickname not in use.]'
			sendTrue = 0
			break
#Check for the error described in the assignment when an offline message gets sent to an online client
		if command == 'OFFLINEFAIL':
			toName = messageParts[1]
			print ">>> [Client " + toName + " exists!!]"


#Sends bounced messages when offline to the server	
def offlineMessageToServer(message, targetName, targetIP, targetPort):
	ts = time.time()
	st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
	#print 'offline message to server: ' + message
	withTimeStamp = "<" + st + ">" +  " " + message
	bouncedMessage = "OFFLINEATTEMPT|" + targetName + "|" + targetIP + "|" + str(targetPort) + "|" + nickname + "|" + clientIP + "|" + str(clientPort) + "|" + withTimeStamp
	#print "bounced message: " + bouncedMessage
	clientSocket.sendto(bouncedMessage, (serverIP,serverPort))
	print '>>> [Messages received by the server and saved.]'

#Prints all offline messages upon re-registration
#Iterates and checks to make sure that there is, in fact, offline messages available
def printOfflineMessage(message):
	splitOfflineMessage = message.split('|')
	messageArray = splitOfflineMessage[1]
	realArray = eval(messageArray)
	if len(realArray) == 0:
		print ">>> [No offline messages were available.]" 
	if len(realArray) > 0:
		print ">>> [You have messages!]"
	for offMessIndividual in realArray:
		print offMessIndividual
	
	
	
#Updates the local online list when another user deregisters
def removeOnlineList(message):
	global onlineList
#Make sure that upon deregistration, the tuple with the user's information is removed from the online list
	storedMessage = message.split('|', 3)
	fromName = messageParts[1]
	fromIP = messageParts[2]
	fromPort = messageParts[3]
	removeKey = (fromName, fromIP, fromPort)
	for i in onlineList:
		if i[0] == fromName:
			onlineList.remove(removeKey)

#Prints the received direct message from the other client
#Sends out the acknowledgement that the message is received
def onlineDMPrint(message, fromName, fromIP, fromPort):

	dmack = 'DMACK'
	clientSocket.sendto(dmack, (fromIP, fromPort))
	print fromName + ": " + message

#Stores all client information in an online list
def storeOnlineList(message):
	messageParts = message.split('|')
	onlineListString = messageParts[1]
	global onlineList
	onlineList = eval(onlineListString)
	print '>>> [Client table updated]'
	print '>>> Online Users:'
	for i in onlineList: 
		print i[0]

#Stores all client information of anybody who has ever logged on to the server ever.
def storeMasterList(message):
	global masterList
	messageParts = message.split('|')
	masterListString = messageParts[1]
	masterList = eval(masterListString)




if __name__ == '__main__':		
	main()
#Start the listening thread
#Each thread is daemon to make sure that program exits gracefully.
	listen_thread = threading.Thread(target=listen, args=())
	listen_thread.daemon = True
	listen_thread.start()
#Start the sending thread
	send_thread = threading.Thread(target=send, args=())
	send_thread.daemon = True
	send_thread.start()
#Make sure that a keyboard interrupt call (ctrl+c) exits the program cleanly and deregisters the client
	try:
		while True:
			time.sleep(1)
			if sentinalkill == 1:
				break
#Make sure we deregister upon a keyboard interruption
	except KeyboardInterrupt:
		outMessage = 'DEREG|' + nickname + '|' + clientIP + '|' + str(clientPort)
		clientSocket.sendto(outMessage, (serverIP, serverPort))
		print ">>> [You are offline. Bye.]"

