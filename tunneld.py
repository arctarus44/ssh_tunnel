import http.server
import threading
from queue import Queue
import socket
import sys
import base64
import urllib
import argparse
import logging

CONTENT_TYPE = "Content-type"
TXT_HTML = "text/html"
PAYLOAD = "payload"
# MSG_404 = b"I am so sorry :("
MSG_200 = b"Thank you <3"
PAYLOAD = "payload"

fifo_query = None
client = None
parser = None

listening_port = None
forwarding_port = None

class TunnelHTTPHandler(http.server.SimpleHTTPRequestHandler):

	def do_HEAD(self):
		self.send_response(200)
		self.send(CONTENT_TYPE, TXT_HTML)
		self.send_header()

	def do_GET(self):
		"""Respond to a GET request."""
		global fifo_query
		logging.info("New GET request received.")
		if client == None:
			logging.debug("No query to forward.")
			self.send_response(503)
			self.send_header(CONTENT_TYPE, TXT_HTML)
			self.end_headers()
		else:
			self.send_response(200)
			self.send_header(CONTENT_TYPE, TXT_HTML)
			self.end_headers()
			logging.debug("Waiting for some data to forward.")
			query = base64.b64encode(fifo_query.get())
			logging.debug("Forwarding the query :%s", base64.b64decode(query))
			self.wfile.write(query)

	def do_POST(self):
		"""Manage to a POST request."""
		global client
		length = int(self.headers['Content-Length'])
		data = urllib.parse.parse_qs(self.rfile.read(length).decode('utf-8'))
		payload = data[PAYLOAD][0]
		logging.debug("New reply received : %s", base64.b64decode(payload))
		client.send(base64.b64decode(payload))
		self.send_response(200)
		self.send_header(CONTENT_TYPE, TXT_HTML)
		self.end_headers()
		self.wfile.write(MSG_200)


def httpd():
	logging.info("Starting the HTTP server thread")
	server_class = http.server.HTTPServer
	# httpd = server_class((socket.gethostname(), forwarding_port),
	# 					 TunnelHTTPHandler)
	httpd = server_class(("localhost", forwarding_port),
						 TunnelHTTPHandler)
	httpd.serve_forever()

def listend():
	global fifo_query
	global client
	logging.info("Starting the query listener thread")
	socket_query = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	socket_query.bind(('localhost', listening_port))
	socket_query.listen(1) # One client at a time
	while True:
		client, info = socket_query.accept()
		logging.info("{0}:{1} connected".format(info[0], info[1]))
		# maybe a while true for client.recv is a good idea.
		query = client.recv(1024)
		fifo_query.put(query)
		logging.info("Close %s:%s connection", info[0], info[1])

if __name__ == "__main__":
	logging.basicConfig(format='%(levelname)8s:%(asctime)s:%(funcName)20s():%(message)s',
						filename='tunneld.log',level=logging.DEBUG)
	try:
		listening_port = int(sys.argv[1])
	except IndexError:
		listening_port = 2222
		logging.info("Default value for the listening port(%s).",
					 listening_port)
	try:
		forwarding_port = int(sys.argv[2])
	except IndexError:
		forwarding_port = 8000
		logging.info("Default value for the and forwarding port(%s)",
					 forwarding_port)

	# Todo when thread quit, close cleany the socket.
	fifo_query = Queue()

	httpd_thread = threading.Thread(None, httpd, name="HTTPD-thread")
	sshd_thread = threading.Thread(None, listend, name="Listend-thread")

	httpd_thread.start()
	sshd_thread.start()
