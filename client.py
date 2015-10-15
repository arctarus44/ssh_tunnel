import socket
import sys
import base64
import threading
from queue import Queue
import urllib
from time import sleep
import http.client
import urllib.request

client = None
tunnel_socket = None
forward_socket = None

ssh_server = "localhost"
ssh_port = 22
http_server = "localhost"
http_port = 8000

website = "{0}:{1}"
url = "http://{0}/random/value"


def forward():
	""" each second, a GET package is send to the server """

	print("Forward thread started")



	connected = False

	while True:
		opened_url = urllib.request.urlopen(url)
		print(url + " -> " + str(opened_url.code))
		if opened_url.code == 200:
			content = opened_url.read()
			request = base64.b64decode(content)
			print(request)
			if connected == False:
				forward_socket.connect((ssh_server, ssh_port))
			forward_socket.send(request)
	forward_socket.close() # usefull? Maybe

def post():
	"""take reply of server and use a socket (sockSshIN) to redirect on 22 port """
	print("Reply thread started")
	tunnel_socket.connect((http_server, http_port))

	while True:
		response = forward_socket.recv(1024)
		print(response)
		headers = {'Content-Type': 'text/html' }
		params = {'payload': base64.b64encode(response)}
		client = http.client.HTTPConnection(website)
		url_params = urllib.parse.urlencode(params)
		print("ZERTYUIOP")
		client.request('POST', 'stelar/login.aspx', url_params, headers)
		r = client.getresponse()
		print(r.code)

		# sleep(0.1)

	tunnel_socket.close()



if __name__ == "__main__":
	http_server = sys.argv[1]
	http_port = int(sys.argv[2])
	website = website.format(http_server, http_port)
	url = url.format(website)

	print(website)
	print(url)

	try:
		ssh_server = sys.argv[3]
		print(ssh_server)
	except IndexError:
		print("Default value for ssh server")

	try:
		ssh_port = int(sys.argv[4])
	except IndexError:
		print("Default value for ssh port")

	# """ FIFO stores HTTP request """
	# ssh_query = Queue()
	forward_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	tunnel_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)


	forw_thread = threading.Thread(None, forward, name="Forward-thread")
	re_thread = threading.Thread(None, post, name="Reply-thread")

	try:
		forw_thread.start()
		re_thread.start()
	except:
		forward_socket.close()
		tunnel_socket.close()
		raise
