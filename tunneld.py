"""Implement the server side of the HTTP tunnel"""

# todo in case of inactivity in the other side of the tunnel, clean the
# queries and replies fifo, close the client socket.

import http.server
import threading
from queue import Queue, Empty
import socket
import sys
import base64
import urllib
import logging
import obfuscate as obf
from utils import ConfigHandler



CONTENT_TYPE = "Content-type"
TXT_HTML = "text/html"
PAYLOAD = "payload"
MSG_200 = b"Thank you <3"

CACHE_CONTROL = "Cache-Control"
PRAGMA = "Pragma"
NO_CACHE = "no-cache"
MAX_AGE_0 = "max-age=0"

http_host = None
http_port = None

forward_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client = None
queries = Queue()
replies = Queue()
client_event = threading.Event()
client_event.clear()
client_close = True

obfuscate = obf.Obfuscate()

#########
# Utils #
#########
class TunnelHTTPHandler(http.server.SimpleHTTPRequestHandler):
	"""This class handle HTTP request in order to send/receive data from/into
	the HTTP tunnel"""

	def do_GET(self):
		"""Manage GET request. Send a request to the other side of the HTTP
		tunnel."""
		global fifo_query
		global client
		logging.debug("New GET request received.")
		if client == None:
			logging.debug("No client connected.")
			self.send_response(404)
			self.send_header(CONTENT_TYPE, TXT_HTML)
			self.end_headers()
		else:
			try:
				query = base64.b64encode(queries.get(block=False))
			except Empty:
				if client_close:
					logging.debug("Client disconnected and nothing in the queries fifo.")
					self.send_response(503)
					self.send_header(CONTENT_TYPE, TXT_HTML)
					self.end_headers()
					client = None
				else:
					logging.debug("Nothing to forward at this moment.")
					self.send_response(500)
					self.send_header(CONTENT_TYPE, TXT_HTML)
					self.end_headers()
			else:
				logging.debug("Forwarding the query :%s", base64.b64decode(query))
				content= obfuscate.obfuscate(str(self.path),
				                                            query)
				self.send_response(200)
				self.send_header(CONTENT_TYPE, TXT_HTML)
				self.send_header(CACHE_CONTROL, MAX_AGE_0)
				self.send_header(PRAGMA, NO_CACHE)
				self.end_headers()
				content = obfuscate.obfuscate(str(self.path), query)
				self.wfile.write(content)

	def do_POST(self):
		"""Manage POST request. Extract the payload and put it into
		the replies query."""
		global client
		logging.info("New POST request received.")
		length = int(self.headers['Content-Length'])
		data = urllib.parse.parse_qs(self.rfile.read(length).decode('utf-8'))
		try:
			payload = data[PAYLOAD][0]
			payload = obf.derandomize_payload(payload)
		except KeyError:
			logging.debug("No payload")
		else:
			logging.debug("New reply received : %s", payload)
			replies.put(base64.b64decode(payload))
			self.send_response(200)
			self.send_header(CONTENT_TYPE, TXT_HTML)
			self.end_headers()
			self.wfile.write(MSG_200)


httpd = None
###########
# Threads #
###########
def httpd():
	""" Start the http server and made it server forever."""
	global httpd
	logging.info("Starting the HTTP server thread")
	server_class = http.server.HTTPServer
	httpd = server_class((http_host, http_port), TunnelHTTPHandler)
	httpd.serve_forever()

def receive_queries():
	"""Received queries from the client."""
	global client_close
	global client
	logging.info("Starting the forward queries thread.")

	while True:
		client, info = forward_socket.accept()
		client_close = False
		logging.info("%s:%s connected", info[0], info[1])
		client_event.set()
		query = client.recv(2048)
		client_event.wait()
		while query != b"":
			logging.debug("New query received : %s", query)
			queries.put(query)
			query = client.recv(2048)

		logging.debug("b'' received")
		queries.put(query)
		logging.info("Close %s:%s connection", info[0], info[1])
		client_close = True
		client.close()
		client_event.clear()


def forward_replies():
	"""Forward replies received from the HTTP tunnel to the client."""
	logging.info("Starting the forward replies thread.")
	client_event.wait()
	while True:
		reply = replies.get()
		logging.info("New reply to forward")
		logging.debug("Sending the following reply : %s", reply)
		client.send(reply)
		client_event.wait()


if __name__ == "__main__":
	logging.basicConfig(format='%(levelname)8s:%(asctime)s:%(funcName)20s():%(message)s',
	                    filename='tunneld.log', level=logging.INFO)

	conf = ConfigHandler()
	conf.read_conf()

	http_host = conf[conf.SCT_TUNNELD][conf.OPT_HTTP_HOST]
	http_port = int(conf[conf.SCT_TUNNELD][conf.OPT_HTTP_PORT])
	listening_host = conf[conf.SCT_TUNNELD][conf.OPT_LISTEN_HOST]
	listening_port = int(conf[conf.SCT_TUNNELD][conf.OPT_LISTEN_PORT])


	listen = "Listening on {0}:{1}.".format(listening_host, listening_port)
	forward = "HTTP server on {0}:{1}.".format(http_host, http_port)

	print(listen)
	print(forward)
	logging.info(listen)
	logging.info(forward)
	del(listen)
	del(forward)

	forward_socket.bind((listening_host, listening_port))
	forward_socket.listen(1) # One client at a time

	httpd_thread = threading.Thread(None, httpd, name="HTTPD-thread")
	forward_queries_thread = threading.Thread(None,
	                                          receive_queries,
	                                          name="Receive-Queries-thread")
	forward_replies_thread = threading.Thread(None,
	                                          forward_replies,
	                                          name="Forward-Replies-thread")

	try:
		httpd_thread.start()
		forward_queries_thread.start()
		forward_replies_thread.start()
	except:
		 httpd.server_close()
