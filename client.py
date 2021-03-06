"""Implement the client side of the HTTP tunnel."""

import sys
import threading
import socket
import logging
import urllib.request
import urllib.error
from time import sleep
from random import choice
import obfuscate as obf
import http.client
import requests
import time
import base64
from utils import ConfigHandler


SLEEP_NO_CLT = 2
SLEEP_NO_DATA = 0.5
SLEEP_DATA = 0.05
PROTOCOL = "http://"

http_server = None
http_port = None
listening_server = None
listening_port = None

url = "{0}{1}:{2}/"
website = "{0}:{1}"
local_server = "localhost"
ressource = "/random/value"
server_port = 22

# The socket used to forward queries to the local server
forward_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# event used to prevent reading on a closed socket
socket_event = threading.Event()
socket_event.clear()

user_agents = [
	'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
	'Opera/9.25 (Windows NT 5.1; U; en)',
	'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
	'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
	'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12',
	'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9'
]

USER_AGENT = choice(user_agents)

def create_get_header():
	"""Create a header for a GET request."""
	hour = int(time.strftime("%H", time.gmtime())) -1
	mod_time = time.strftime("%a, %d %b %Y {0}:%M:%S GMT", time.gmtime()).format(hour)
	request_headers = {
		"Accept-Language": "en-US,en;q=0.5",
		"User-Agent": USER_AGENT,
		"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
		"Referer": "http://www.google.fr/search?q=google",
		"Date": time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime()),
		"Server": "ECS",
		"Last-Modified": mod_time,
		"ETag": "0af64f232b5ce1:0",
		"Accept-Ranges": "bytes",
		"Vary": "Accept-Encoding",
		"Content-encoding": "gzip",
		"Connection": "keep-alive",
		"DNT": "1",
	}
	return request_headers

def create_post_header():
	"""Create a header for a POST request."""
	request_headers = {'Content-Type': 'text/plain',
	                   "User-agent": USER_AGENT}
	return request_headers


# todo find some specific value for time_of_sleep to keep the number of
# queries/replies per second the lowest possible.

def receive_queries():
	"""Receive a query from the other side of the HTTP tunnel and send it
	to the local server."""
	global forward_socket
	global url

	logging.info("Receive queries thread started.")

	# the time the thread have to sleep before launching a new query
	time_to_sleep = SLEEP_NO_CLT
	first_forward = True

	obfuscate = obf.Obfuscate()

	while True:
		requested_url = url + obfuscate.random_url()
		logging.debug("Requested url %s", requested_url)
		request = urllib.request.Request(requested_url,
		                                 headers = create_get_header())
		try:
			opened_url = urllib.request.urlopen(request)
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

		except urllib.error.URLError as error:
			logging.error(error)
			pass				# The client must run at all costs

		else:
			if opened_url.code == 200:
				time_to_sleep = SLEEP_DATA

				obfuscated_content = opened_url.read()
				content = obfuscate.deobfuscate(requested_url,
				                                obfuscated_content)
				query = base64.b64decode(content)
				logging.debug("Received query : %s", query)

				if first_forward:
					forward_socket.connect((forward_server, forward_port))
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

	while True:
		logging.debug("Forward replies thread locked.")
		socket_event.wait()
		logging.debug("Forward replies thread unlocked.")
		reply = forward_socket.recv(4096)
		headers = create_post_header()
		payload = base64.b64encode(reply)
		payload = obf.randomize_payload(payload.decode("ascii"))
		params = {'payload': payload}
		r = requests.post(url + ressource, headers=headers, data=params)

if __name__ == "__main__":
	logging.basicConfig(format='%(levelname)8s:%(asctime)s:%(funcName)20s():%(message)s',
	                    filename='client.log', level=logging.DEBUG)

	conf = ConfigHandler()
	conf.read_conf()

	http_server = conf[conf.SCT_TUNNELD][conf.OPT_HTTP_HOST]
	http_port = conf[conf.SCT_TUNNELD][conf.OPT_HTTP_PORT]
	forward_server = conf[conf.SCT_CLIENT][conf.OPT_FORWARD_HOST]
	forward_port = int(conf[conf.SCT_CLIENT][conf.OPT_FORWARD_PORT])
	url = url.format(PROTOCOL, http_server, http_port)
	website = website.format(local_server, http_port)

	listen = "Listening on {0}:{1}.".format(http_server, http_port)
	forward = "Forwarding on {0}:{1}.".format(forward_server, forward_port)

	print(listen)
	print(forward)
	logging.info(listen)
	logging.info(forward)
	del(listen)
	del(forward)

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
