import socket
import sys
import base64
import threading
from queue import Queue
import urllib
from time import sleep
import http.client
import urllib.request
import urllib.error
import logging

tunnel_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
forward_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

ssh_server = "localhost"
ssh_port = 22

website = "{0}:{1}"
ressource = "/random/value"
url = "http://{0}" + ressource

queries = Queue()
replies = Queue()

listening_event = threading.Event()
listening_event.clear()

def receive_queries():
	"""Receive querie from the other side of the HTTP tunnel."""
	logging.info('Receive_queries thread started')
	time_to_sleep = 1
	while True:
		try:
			opened_url = urllib.request.urlopen(url)
		except urllib.error.HTTPError as http_error:
			if http_error.getcode() == 503:
				time_to_sleep = 2
				logging.debug("No client connected for the moment")
			elif http_error.getcode() == 500:
				time_to_sleep = 0.5
				logging.debug("Nothing to get from the other side of the tunnel")
			else:
				raise
		else:
			if opened_url.code == 200:
				time_to_sleep = 0.1
				content = opened_url.read()
				query = base64.b64decode(content)
				logging.debug("Receive query %s", query)
				queries.put(query)
		sleep(time_to_sleep)

def forward_queries():
	"""Forward queries to the designated server."""
	logging.info('Forward_queries thread started')
	first_query = True
	while True:
		query = queries.get()
		logging.debug("New query to forward obtained from the queries fifo")
		if first_query:
			logging.info("First connection, opening the connection to the \
server")
			forward_socket.connect((ssh_server, ssh_port))
			first_query = False
			logging.info("First connection opened, unfreeze the reception \
of replies")
			listening_event.set()
		logging.debug("Forward query \"%s\" to %s:%s", query, ssh_server,
					  ssh_port)
		forward_socket.send(query)


def receive_replies():
	"""Receive replies from the designated server."""
	logging.info('Receive_replies thread started')
	listening_event.wait()
	logging.info("Starting to receive replies")
	while True:
		reply = forward_socket.recv(2048)
		logging.debug("New reply received : %s", reply)
		replies.put(reply)

def forward_replies():
	"""Forward replies to the other side of the HTTP tunnel."""
	logging.info('Forward_replies thread started')
	while True:
		reply = replies.get()
		logging.debug("New reply to forward obtained from the replies fifo")
		headers = {'Content-Type': 'text/html' }
		params = {'payload': base64.b64encode(reply)}
		client = http.client.HTTPConnection(website)
		logging.debug("Forwarding the reply : %s", reply)
		url_params = urllib.parse.urlencode(params)
		client.request("POST", ressource, url_params, headers)

if __name__ == "__main__":
	http_server = sys.argv[1]
	http_port = int(sys.argv[2])
	website = website.format(http_server, http_port)
	url = url.format(website)
	logging.basicConfig(format='%(levelname)8s:%(asctime)s:%(funcName)20s():%(message)s',
						filename='client.log',level=logging.DEBUG)

	try:
		ssh_server = sys.argv[3]
	except IndexError:
		logging.info("Default value for the and ssh server address (%s).",
					 ssh_server)

	try:
		ssh_port = int(sys.argv[4])
	except IndexError:
		logging.info("Default value for the and ssh server port (%s).",
					 ssh_port)

	r_queries_thread = threading.Thread(None, receive_queries,
										name="Receive_queries thread")
	f_queries_thread = threading.Thread(None, forward_queries,
										name="Forward_queries thread")
	r_replies_thread = threading.Thread(None, receive_replies,
										name="Receive_replies thread")
	f_replies_thread = threading.Thread(None, forward_replies,
										name="Forward_replies thread")


	try:
		r_queries_thread.start()
		f_queries_thread.start()
		r_replies_thread.start()
		f_replies_thread.start()
	except:
		forward_socket.close()
		raise
