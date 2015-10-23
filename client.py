"""Implement the client side of the HTTP tunnel."""

import sys
import threading
import socket
import logging
import base64
import urllib.request
import urllib.error
from time import sleep


SLEEP_NO_CLT = 2
SLEEP_NO_DATA = 0.5
SLEEP_DATA = 0.05
PROTOCOL = "http://"

url = None
local_server = "localhost"
server_port = 22

# The socket used to forward queries to the local server
forward_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# event used to prevent reading on a closed socket
socket_event = threading.Event()
socket_event.clear()

def receive_queries():
	"""Receive a query from the other side of the HTTP tunnel and send it
	to the local server."""

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

			elif error_code == 503:
				logging.info("Client disconnected.")
				time_to_sleep = SLEEP_NO_CLT
				socket_event.set()
				forward_socket.clear()
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
					socket_event.set()
					logging.info("Connected socket to %s:%s.", local_server,
					             server_port)
					first_forward = False
				forward_socket.send(query)
		logging.debug("Go to sleep for %ss", time_to_sleep)
		sleep(time_to_sleep)



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

	url = "{0}{1}:{2}".format(PROTOCOL, http_server, http_port, "random/value")

	logging.basicConfig(format='%(levelname)8s:%(asctime)s:%(funcName)20s():%(message)s',
	                    filename='client.log', level=logging.DEBUG)

	r_queries_thread = threading.Thread(None, receive_queries,
	                                    name="Receive_queries thread")

	try:
		r_queries_thread.start()
	except:
		logging.error(sys.exc_info()[0])
		forward_socket.close()
		raise
