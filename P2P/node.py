import socket 
import select 
import signal
import sys 
import pickle
import time
from _thread import *
import random
killSwitch=0
list_of_peers=[]

oldTags=[]
myTag=""
welcomeText=0

#==============================================INTIALIZATION================================================================#

# CREATE SOCKETS 

## SERVER SOCKET FOR ACCEPTING NEW NODES INTO THE NETWORK
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 

## CLIENT SOCKET TO JOIN INTO THE EXISTING NETWORK
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#ARG HELP
if len(sys.argv) != 4: 
	print("Correct usage: script, your ID,  parent connection port number, your port number")
	exit() 

# ARG PARSING 
IP_address = "127.0.0.1"

noParent=0	# SIGNIFIES IF NODE IS FIRST IN THE NETWORK
myID=sys.argv[1]  
if(sys.argv[2] == "None"):
	noParent=1
else:
	parentPort=int(sys.argv[2])

myPort = int(sys.argv[3]) 

#==============================================CATCH CTRL-C================================================================#
#==========================================DISCONNECT FROM PARENT==========================================================# 
#====================================AND POINT CHILDREN PEERS TO PARENT ===================================================#


def exit_handler(sig, frame):
	global killSwitch
	print('you wanna exit? (Y/N)')
	answer=sys.stdin.readline()
	if(answer=="Y" or  answer=="y"):
		killSwitch=1
		time.sleep(5)
	sys.exit(0)
signal.signal(signal.SIGINT, exit_handler)

#====================== CONNECT TO PARENT - AND COMMUNICATION BETWEEN NODE AND PARENT =====================================#  
# CONNECT TO PARENT

reconnect=0 # SET IF PARENT LEAVES

def parentCommuncation(socket):
	global killSwitch
	global list_of_peers
	global reconnect
	global myID
	global myPort
	global welcomeText
	global myTag
	global oldTags

	if not welcomeText:
		myTag=str(random.randint(0,999))
		socket.sendall((myTag+" Sup everybody! this is"+myID).encode('utf-8'))
		welcomeText=1
	list_of_peers.append(socket)

	while True: 
		# DISCONNECT ON SIGINT
		if (killSwitch==1):
			socket.sendall("BYE-BYE")
			socket.close()
			break
		# MAINTAINS A LIST OF POSSIBLE INPUT STREAMS 
		sockets_list = [sys.stdin, socket] 
		read_sockets,write_socket, error_socket = select.select(sockets_list,[],[]) 
		for socks in read_sockets: 
			if socks == socket: 
				message = (socks.recv(2048)).decode('utf-8') 
				if(message=="BYE-BYE"):
					reconnect=1
					newParent=(socks.recv(2048)).decode('utf-8')
					socks.close()
					socks.connect((IP_address,int(newParent)))
				elif(message=="ping me your port"):
					socks.sendall(str(myPort).encode('utf-8'))
				else:
					# PRINT RECEIVED MSG
					tagAndMessage=message.split(' ', 1)
					if(tagAndMessage[0] not in oldTags):
						print(tagAndMessage[1]) 
						forward(message,socks,"None")
						oldTags.append(tagAndMessage[0])

			else: 
				message = sys.stdin.readline()
				messageWithInfo="<" + myID+"> "+ message
				myTag=str(random.randint(0,999))
				oldTags.append(myTag)
				socket.sendall((myTag +" "+messageWithInfo).encode('utf-8'))
				sys.stdout.write("<You>") 
				sys.stdout.write(message) 
				forward(messageWithInfo,None,myTag)
				sys.stdout.flush() 

if not noParent:
	client.connect((IP_address,parentPort))
	start_new_thread(parentCommuncation,(client,))



#===================================== ACT AS SERVER FOR INCOMING NODES ===================================================#
# BIND SOCKET
server.bind((IP_address, myPort)) 

#LISTEN TO 100 CONNECTIONS MAX.
server.listen(100) 


def peerthread(conn, addr): 

	global killSwitch
	global noParent 
	global myPort
	global client
	global parentPort
	if noParent:
		conn.sendall(("ping me your port").encode('utf-8'))
#		print("<no parent for me, asked for port of child>")
		print((conn.recv(2048).decode('utf-8')))
		parentPort=int((conn.recv(2048)).decode('utf-8'))
#		print("<child says "+str(parentPort))
		client.connect((IP_address,parentPort))
		start_new_thread(parentCommuncation,(client,))
	# WELCOME TEXT
#	conn.sendall(("welcome to P2P chat! "+ "<" + str(addr[0]) + " : " + str(addr[1]) + "> ").encode('utf-8')) 

	while True:
		if killSwitch:
			conn.sendall(("BYE-BYE").encode('utf-8'))
			if not noParent:
				conn.sendall(str(parentPort).encode('utf-8'))
			conn.close()
		try: 
			message = (conn.recv(2048)).decode('utf-8')
			if message:

				# PRINT RECEIVED MSG
				tagAndMessage=message.split(' ', 1)
				if(tagAndMessage[0] not in oldTags):
					print(tagAndMessage[1]) 
					oldTags.append(tagAndMessage[0])					
					# FORWARD TO OTHER PEERS
					message_to_send=message
					# message_to_send = "<" + str(addr[0]) + " : " + str(addr[1]) + "> " + message
					forward(message_to_send, conn,"None") 
				
			else: 
				remove(conn) 

		except: 
			continue

# FORWARD TO CONNECTED CLIENTS
def forward(message, connection,tag): 
	for peers in list_of_peers: 
		if peers!=connection: 
			try: 
				if(tag=="None"):
					peers.sendall((message).encode('utf-8')) 
				else:
					peers.sendall((tag+" "+ message).encode('utf-8')) 
			except: 
				peers.close() 

				# IF THE LINK IS BROKEN, WE REMOVE THE PEER 
				remove(peers) 

# REMOVE THE CONNECTION
def remove(connection): 
	if connection in list_of_peers: 
		list_of_peers.remove(connection) 

while True: 

	# ACCEPT INCOMING CONNECTIONS
	conn, addr = server.accept() 
	
	# APPEND THE NEW CONNECTION
	list_of_peers.append(conn) 

	# PRINTS THE ADDRESS AND PORT OF THE NEW CONNCTION THAT JUST CONNECTED 
#	print(str(addr[0]) + " : " + str(addr[1]) + " connected")

	# CREATES AN INDIVIDUAL THREAD FOR EVERY PEER CONNECTION
	start_new_thread(peerthread,(conn,addr,))	 





conn.close() 
server.close() 


