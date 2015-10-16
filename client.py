import socket
import sys
import base64
import threading
from queue import Queue
import urllib
from time import sleep
import http.client
import urllib.request

tunnel_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
forward_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

ssh_server = "localhost"
ssh_port = 22
http_server = "localhost"
http_port = 8000

website = "{0}:{1}"
ressource = "/random/value"
url = "http://{0}" + ressource

queries = Queue()
replies = Queue()


def receive_queries():
	"""Receive querie from the other side of the HTTP tunnel."""
	print('Receive_queries thread started')
	while True:
		opened_url = urllib.request.urlopen(url)
		if opened_url.code == 200:
			content = opened_url.read()
			query = base64.b64decode(content)
			print(query)
			queries.put(query)

def forward_queries():
	"""Forward queries to the designated server."""
	print('Forward_queries thread started')
	first_query = True
	while True:
		query = queries.get()
		if first_query:
			forward_socket.connect((ssh_server, ssh_port))
		forward_socket.send(query)


def receive_replies():
	"""Receive replies from the designated server"""
	print('Receive_replies thread started')
	pass

def forward_replies():
	"""Forward replies to the other side of the HTTP tunnel."""
	print('Forward_replies thread started')
	while True:
		reply = replies.get()
		headers = {'Content-Type': 'text/html' }
		params = {'payload': base64.b64encode(reply)}
		client = http.client.HTTPConnection(website)
		url_params = urllib.parse.urlencode(params)
		client.request(ressource)


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

	r_queries_thread = threading.Thread(None, receive_queries,
										name="Receive queries thread")
	f_queries_thread = threading.Thread(None, forward_queries,
										name="Forward queries thread")
	r_replies_thread = threading.Thread(None, receive_replies,
										name="Receive replies thread")
	f_replies_thread = threading.Thread(None, forward_replies,
										name="Forward replies thread")


	try:
		r_queries_thread.start()
		f_queries_thread.start()
		r_replies_thread.start()
		f_replies_thread.start()
	except:
		forward_socket.close()
		raise
