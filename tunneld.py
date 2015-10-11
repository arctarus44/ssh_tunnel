import http.server
import threading
from queue import Queue
import socket
import sys
import base64

CONTENT_TYPE = "Content-type"
TXT_HTML = "text/html"

ssh_query = None

class TunnelHTTPHandler(http.server.SimpleHTTPRequestHandler):

	def do_HEAD(self):
		self.send_response(200)
		self.send(CONTENT_TYPE, TXT_HTML)
		self.send_header()

	def do_GET(self):
		"""Respond to a GET request."""
		global ssh_query
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		query = base64.b64encode(ssh_query.get())
		self.wfile.write(query)


def httpd():
	server_class = http.server.HTTPServer
	httpd = server_class(("localhost", 8000), TunnelHTTPHandler)
	httpd.serve_forever()

def sshd():
	global ssh_query
	sockt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sockt.bind(('', 2222))
	sockt.listen(10)
	while True:
		client, address = sockt.accept()
		print("{0} connected".format(address))
		query = client.recv(255)
		ssh_query.put(query)


if __name__ == "__main__":
	ssh_query = Queue()

	httpd_thread = threading.Thread(None, httpd, name="HTTPD-thread")
	httpd_thread.start()

	sshd_thread = threading.Thread(None, sshd, name="SSHD-thread")
	sshd_thread.start()
