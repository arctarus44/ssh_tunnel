import socket
import http.client
import sys
import base64
import threading
from queue import Queue
import httplib
import urllib

ssh_query = None
client = None

""" each one second, a GET package is send to the server """
# need to add a target
def sending():
	global client
	
	while True:
		client.request("GET")
		threading.Condition.wait(1000)

""" take reply of server and use a socket (sockSsh) to redirect on 22 port """
def forwarding():
	global ssh_query
	global client

	while True :
		#threading.Condition.wait(1000)
		reply = client.getresponse()
		if reply.reason == "OK":
			data = client.getresponse()
			pack = base64.b64decode(data)
			cmd = pack.read()
			#sockSsh.send(cmd_bin)




if __name__ == "__main__":

	""" FIFO stores HTTP request """
	ssh_query = Queue()
	client = http.client.HTTPConnection("localhost",8000)
	sockSsh = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

	
	send_thread = threading.Thread(None, sending, name="send-getting")
	send_thread.start()
	
	forw_thread = threading.Thread(None, forwarding, name="forward")
	forw_thread.start()

