"""Implement the client side of the HTTP tunnel."""

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

tunnel_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
forward_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

ssh_server = "localhost"
ssh_port = 22

website = "{0}:{1}"
ressource = "/random/value"
url = "http://{0}" + ressource

queries = Queue()
replies = Queue()

listening_event = threading.Event()
listening_event.clear()
forwarding_event = threading.Event()
forwarding_event.clear()

def clean_queue(queue):
	while not queue.empty():
		queue.get(block=False)

def receive_queries():
	"""Receive querie from the other side of the HTTP tunnel."""
	logging.info('Receive_queries thread started')
	time_to_sleep = 1
	while True:
		try:
			opened_url = urllib.request.urlopen(url)
		except urllib.error.HTTPError as http_error:
			if http_error.getcode() == 404:
				time_to_sleep = 2
				logging.info("No client connected for the moment.")
			elif http_error.getcode() == 500:
				time_to_sleep = 0.5
				logging.info("Nothing to get from the other side of the tunnel.")
			elif http_error.getcode() == 503:
				time_to_sleep = 2
				logging.info("Distant client disconnected.")
				clean_queue(queries)
				forward_socket.close()
			else:
				logging.exception(http_error)
				raise
		else:
			if opened_url.code == 200:
				logging.info("New query to forward to the local server.")
				time_to_sleep = 0.1
				content = opened_url.read()
				query = base64.b64decode(content)
				logging.debug("Received query : %s", query)
				queries.put(query)
		sleep(time_to_sleep)

def forward_queries():
	"""Forward queries to the designated server."""
	logging.info('Forward_queries thread started')
	first_query = True

	while True:
		query = queries.get()
		logging.info("New query to forward obtained from the queries fifo")
		if first_query:
			logging.info("First connection, opening the connection to the server")
			forward_socket.connect((ssh_server, ssh_port))
			forwarding_event.set()
			first_query = False
			listening_event.set()
		logging.debug("Forward query : %s", query)
		forward_socket.send(query)


def receive_replies():
	"""Receive replies from the designated server."""
	logging.info('Receive_replies thread started')
	listening_event.wait()
	logging.debug("Starting to receive replies")
	while True:
		forwarding_event.wait()
		reply = forward_socket.recv(2048)
		logging.info("New reply received.")
		logging.debug("New reply received : %s", reply)
		replies.put(reply)

def forward_replies():
	"""Forward replies to the other side of the HTTP tunnel."""
	logging.info('Forward_replies thread started')

	first_empty_reply = False
	while True:
		reply = replies.get()

		if first_empty_reply:
			clean_queue(replies)
			first_empty_reply = False
			break

		if reply == b"":
			first_empty_reply = True

		logging.info("New reply to forward obtained from the replies fifo")
		headers = {'Content-Type': 'text/html'}
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
	                    filename='client.log', level=logging.DEBUG)

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
