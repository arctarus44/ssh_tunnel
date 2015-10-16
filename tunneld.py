import http.server
import threading
from queue import Queue
import socket
import sys
import base64
import urllib
import argparse

CONTENT_TYPE = "Content-type"
TXT_HTML = "text/html"
PAYLOAD = "payload"
MSG_404 = b"I am so sorry :("
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
		if client == None:
			self.send_response(503)
			self.send_header(CONTENT_TYPE, TXT_HTML)
			self.end_headers()
		else:
			self.send_response(200)
			self.send_header(CONTENT_TYPE, TXT_HTML)
			self.end_headers()
			print("Waiting for some data from the fifo")
			query = base64.b64encode(fifo_query.get())
			print("Sending data")
			self.wfile.write(query)

	def do_POST(self):
		"""Manage to a POST request."""
		global client
		length = int(self.headers['Content-Length'])
		data = urllib.parse.parse_qs(self.rfile.read(length).decode('utf-8'))
		payload = data[PAYLOAD][0]
		print(payload)
		client.send(base64.b64decode(payload))
		self.send_response(200)
		self.send_header(CONTENT_TYPE, TXT_HTML)
		self.end_headers()
		self.wfile.write(MSG_200)


def httpd():
	server_class = http.server.HTTPServer
	httpd = server_class((socket.gethostname(), forwarding_port),
						 TunnelHTTPHandler)
	print("Starting the HTTP server thread")
	httpd.serve_forever()

def listend():
	global fifo_query
	global client
	print("Starting the query listener thread")
	socket_query = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	socket_query.bind(('localhost', listening_port))
	socket_query.listen(1) # One client at a time
	while True:
		client, info = socket_query.accept()
		print("{0}:{1} connected".format(info[0], info[1]))
		# maybe a while true for client.recv is a good idea.
		empty_query = False
		while not empty_query: # While the socket is still open
			query = client.recv(1024)
			fifo_query.put(query)
			if query == b"":
				empty_query = True
		print("Close {0}:{1} connection".format(info[0], info[1]))
		client.close()

if __name__ == "__main__":
	try:
		listening_port = int(sys.argv[1])
		forwarding_port = int(sys.argv[2])
	except IndexError:
		listening_port = 2222
		forwarding_port = 8000

	# Todo when thread quit, close cleany the socket.
	fifo_query = Queue()

	httpd_thread = threading.Thread(None, httpd, name="HTTPD-thread")
	sshd_thread = threading.Thread(None, listend, name="Listend-thread")

	httpd_thread.start()
	sshd_thread.start()
