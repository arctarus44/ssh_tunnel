import http.server
import threading
from queue import Queue
import socket
import sys
import base64

CONTENT_TYPE = "Content-type"
TXT_HTML = "text/html"

fifo_query = None

class TunnelHTTPHandler(http.server.SimpleHTTPRequestHandler):

	def do_HEAD(self):
		self.send_response(200)
		self.send(CONTENT_TYPE, TXT_HTML)
		self.send_header()

	def do_GET(self):
		"""Respond to a GET request."""
		global fifo_query
		if fifo_query.empty():
			self.send_response(404)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(b"I am so sorry :(")
		else:
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			query = base64.b64encode(fifo_query.get())
			self.wfile.write(query)


def httpd():
	server_class = http.server.HTTPServer
	httpd = server_class(("localhost", 8000), TunnelHTTPHandler)
	print("Starting the HTTP server thread")
	httpd.serve_forever()

def listend():
	global fifo_query
	print("Starting the query listener thread")
	socket_query = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	socket_query.bind(('', 2222))
	socket_query.listen(10)
	while True:
		client, info = socket_query.accept()
		print("{0} connected".format(info))
		# maybe a while true for client.recv is a good idea.
		query = client.recv(255)
		fifo_query.put(query)


if __name__ == "__main__":
	# Todo when thread quit, close cleany the socket.
	# Add management of the response.
	fifo_query = Queue()

	httpd_thread = threading.Thread(None, httpd, name="HTTPD-thread")
	httpd_thread.start()

	sshd_thread = threading.Thread(None, listend, name="Listend-thread")
	sshd_thread.start()
