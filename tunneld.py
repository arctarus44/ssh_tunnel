import http.server
import threading
from queue import Queue, Empty
import socket
import sys
import base64
import urllib
import argparse
import logging

# todo in case of inactivity in the other side of the tunnel, clean the
# queries and replies fifo, close the client socket.

CONTENT_TYPE = "Content-type"
TXT_HTML = "text/html"
PAYLOAD = "payload"
MSG_200 = b"Thank you <3"

listening_port = 2222
forwarding_port = 8000
http_address = localhost

forward_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client = None
queries = Queue()
replies = Queue()
client_event = threading.Event()
client_event.clear()
client_close = True

#########
# Utils #
#########
class TunnelHTTPHandler(http.server.SimpleHTTPRequestHandler):

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
			try:
				query = base64.b64encode(queries.get(block = False))
			except Empty:
				if client_close:
					logging.debug("Client close and nothing in the queries fifo.")
					self.send_response(503)
					self.send_header(CONTENT_TYPE, TXT_HTML)
					self.end_headers()
				else:
					logging.debug("Nothing to forward at this moment.")
					self.send_response(500)
					self.send_header(CONTENT_TYPE, TXT_HTML)
					self.end_headers()
			else:
				logging.info("Forwarding the query :%s", base64.b64decode(query))
				self.send_response(200)
				self.send_header(CONTENT_TYPE, TXT_HTML)
				self.end_headers()
				self.wfile.write(query)

	def do_POST(self):
		"""Manage to a POST request."""
		global client
		length = int(self.headers['Content-Length'])
		data = urllib.parse.parse_qs(self.rfile.read(length).decode('utf-8'))
		try:
			payload = data[PAYLOAD][0]
		except KeyError:
			logging.debug("No payload")
		else:
			logging.debug("New reply received : %s", base64.b64decode(payload))
			replies.put(base64.b64decode(payload))
			self.send_response(200)
			self.send_header(CONTENT_TYPE, TXT_HTML)
			self.end_headers()
			self.wfile.write(MSG_200)

###########
# Threads #
###########
def httpd():
	""" Start the http server and made it server forever."""
	logging.info("Starting the HTTP server thread")
	server_class = http.server.HTTPServer
	httpd = server_class(("localhost", forwarding_port),
						 TunnelHTTPHandler)
	httpd.serve_forever()

def receive_queries():
	"""Received queries from the client."""
	global client_close
	global client
	logging.info("Starting the forward queries thread.")

	while True:
		client_close = False
		client, info = forward_socket.accept()
		logging.info("{0}:{1} connected".format(info[0], info[1]))
		client_event.set()
		query = client.recv(2048)
		client_event.wait()
		while query != b"":
			logging.debug("New query received : %s", query)
			queries.put(query)
			query = client.recv(2048)

		logging.debug("b'' received")
		queries.put(query)
		client_close = True
		client_event.clear()
		client.close()
		logging.info("Close %s:%s connection", info[0], info[1])


def forward_replies():
	"""Forward replies received from the HTTP tunnel to the client."""
	logging.info("Starting the forward replies thread.")
	logging.debug("Freeze forwarding replies")
	client_event.wait()
	logging.debug("Unfreeze forwarding replies")
	while True:
		logging.debug("Waiting to forward a reply")
		reply = replies.get()
		logging.debug("Sending the following reply : %s", reply)
		client.send(reply)
		logging.debug("Freeze forwarding replies")
		client_event.wait()
		logging.debug("Unfreeze forwarding replies")


if __name__ == "__main__":
	logging.basicConfig(format='%(levelname)8s:%(asctime)s:%(funcName)20s():%(message)s',
						filename='tunneld.log',level=logging.DEBUG)
	try:
		listening_port = int(sys.argv[1])
	except IndexError:
		logging.info("Default value for the listening port (%s).",
					 listening_port)
	try:
		forwarding_port = int(sys.argv[2])
	except IndexError:
		logging.info("Default value for the forwarding port (%s)",
					 forwarding_port)
	try:
		http_address = int(sys.argv[3])
	except IndexError:
		logging.info("Default value for the http address (%s)",
					 forwarding_port)

	forward_socket.bind(('localhost', listening_port))
	forward_socket.listen(1) # One client at a time

	httpd_thread = threading.Thread(None, httpd, name="HTTPD-thread")
	forward_queries_thread = threading.Thread(None, receive_queries, name="Receive-Queries-thread")
	forward_replies_thread = threading.Thread(None, forward_replies, name="Forward-Replies-thread")

	httpd_thread.start()
	forward_queries_thread.start()
	forward_replies_thread.start()
