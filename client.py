"""Implement the client side of the HTTP tunnel."""

import sys
import threading
import socket
import logging
import base64
import urllib.request
import urllib.error
from time import sleep
import http.client


SLEEP_NO_CLT = 2
SLEEP_NO_DATA = 0.5
SLEEP_DATA = 0.05
PROTOCOL = "http://"

url = None
website = "{0}:{1}"
local_server = "localhost"
ressource = "/random/value"
server_port = 22

# The socket used to forward queries to the local server
forward_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# event used to prevent reading on a closed socket
socket_event = threading.Event()
socket_event.clear()

def receive_queries():
	"""Receive a query from the other side of the HTTP tunnel and send it
	to the local server."""
	global forward_socket

	logging.info("Receive queries thread started.")

	# the time the thread have to sleep before launching a new query
	time_to_sleep = 2
	first_forward = True

	while True:
		try:
			opened_url = urllib.request.urlopen(url)
		except urllib.error.HTTPError as http_error:
			error_code = http_error.getcode()

			if error_code == 404: # no client connected on the other side
				logging.debug("No distant client connected for the moment.")
				time_to_sleep = SLEEP_NO_CLT

			elif error_code == 500: # no data on the other side
				logging.debug("No data to forward to the local server.")
				time_to_sleep = SLEEP_NO_DATA

			elif error_code == 503: # The client had just disconnected.
				logging.info("Client disconnected.")
				time_to_sleep = SLEEP_NO_CLT
				socket_event.clear()
				forward_socket.close()
				forward_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				logging.info("Socket closed.")
				first_forward = True # otherwise, the socket will not be opened again

			else:
				logging.error(http_error)

		else:
			if opened_url.code == 200:
				time_to_sleep = SLEEP_DATA

				content = opened_url.read()
				query = base64.b64decode(content)
				logging.debug("Received query : %s", query)

				if first_forward:
					forward_socket.connect((local_server, server_port))
					logging.info("Connected socket to %s:%s.", local_server,
					             server_port)
					logging.debug("Socket event unlocked")
					socket_event.set()
					first_forward = False
				forward_socket.send(query)
		logging.debug("Go to sleep for %ss", time_to_sleep)
		sleep(time_to_sleep)


def forward_replies():
	"""Forward replies to the other side of the HTTP tunnel."""
	logging.info("Forward replies thread started.")
	socket_event.wait()
	empty_reply = False

	while True:
		logging.debug("Forward replies thread locked.")
		socket_event.wait()
		logging.debug("Forward replies thread unlocked.")
		reply = forward_socket.recv(2048)
		headers = {'Content-Type': 'text/html'}
		params = {'payload': base64.b64encode(reply)}
		client = http.client.HTTPConnection(website)
		url_params = urllib.parse.urlencode(params)
		logging.debug("Forwarding replies : %s.", params["payload"])
		client.request("POST", ressource, url_params, headers)

if __name__ == "__main__":
	http_server = sys.argv[1]
	http_port = int(sys.argv[2])

	try:
		local_server = sys.argv[3]
	except IndexError:
		logging.info("Using default value for the local server address (%s).",
		             ssh_server)

	try:
		server_port = int(sys.argv[4])
	except IndexError:
		logging.info("Using default value for the local server port (%s).",
		             server_port)

	url = "{0}{1}:{2}".format(PROTOCOL, http_server, http_port, ressource)
	website = website.format(local_server, http_port)

	logging.basicConfig(format='%(levelname)8s:%(asctime)s:%(funcName)20s():%(message)s',
	                    filename='client.log', level=logging.DEBUG)

	r_queries_thread = threading.Thread(None, receive_queries,
	                                    name="Receive_queries thread")
	f_replies_thread = threading.Thread(None, forward_replies,
	                                    name="Forward_relies thread")

	try:
		r_queries_thread.start()
		f_replies_thread.start()
	except:
		logging.error(sys.exc_info()[0])
		forward_socket.close()
		raise
