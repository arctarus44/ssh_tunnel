"""Implement a class to (de)obfuscate the traffic between the server side and
client side of the tunnel"""

import string
import random

from bs4 import BeautifulSoup

URL_SIZE = 15
SUP_SIZE = 5

RANDOM_CHAR = ["_", ",", "@", "*", "_", " ", "[", "]"]

def randomize_payload(payload):
	# todo randomize the order of the element of the list before adding them
	# into payload_d
	print(payload)
	if type(payload) is bytes:
		payload = payload.decode()
	randomize_payload = ""
	for char in payload:
		if random.getrandbits(1) == 0:
			randomize_payload += random.choice(RANDOM_CHAR)
		randomize_payload += char
	# randomize_payload[::-1]
	return

def derandomize_payload(payload):
	# todo sort the element of payload using the first char of the part.
	# keys = list(payload.keys())
	# keys = [int(k) for k in keys]
	# keys.sort()
	# result = ""
	# for key in keys:
	# 	part = payload[str(key)][0]
	# 	part = part.replace(str(key), "")
	# 	result += part

	result = ""
	for char in RANDOM_CHAR:
		result = result.replace(char, "")
	# result = result[::-1]
	return result# [1:]


class HTMLGenerator:
	""" Generate a straightforward random page to hide some content."""

	__MAX_DEPTH = 7				# count from <html><body>
	__BLOCk_MARKER = ["div", "p", "h1", "h2", "h3"]
	__PROBA_BLOCk = 75			# 0.75 of chance to have a bloc
	__SPLIT = 10				# split every 10har

	def __init__(self, marker, payload):
		"""The marker, will be used as a marker to hide the payload. The payload
		will be spilt in a list of char.See __SPLIT."""
		self.__marker = marker
		nb_equal = 0
		if payload[-2:] == b"==":
			payload = payload[:-2]
			nb_equal = 2
		if payload[-1:] == b"=":
			payload = payload[:-1]
			nb_equal = 1
		self.__payload = [payload[i:i+self.__SPLIT]
		                  for i in range(0, len(payload), self.__SPLIT)]
		self.__payload += [str(nb_equal).encode()]
		self.__payload_used = 0
		self.__depth = 1

	def __use_block(self):
		"""Return a random boolean to indicate, if we had to create a new
		block node, or not."""
		rand = random.randint(0, 100)
		if rand > self.__PROBA_BLOCk:
			return False
		else:
			return True

	def random_page(self):
		"""Create a random html page. You can use this method as much as
		you want."""
		page = '<html><body>'
		page += self.__random_body()
		page += '</body></html>'
		self.__payload_used = 0
		return page.encode()

	def __random_body(self):
		"""Generate a new random body."""
		body = ""
		while self.__payload_used < len(self.__payload):
			if self.__use_block():
				body += self.__random_block()
			else:
				body += '<div>'
				body += self.__gen_inline()
				body += '</div>'
		return body

	def __random_block(self):
		"""Generate a new random block element. This method call __gen_inline
		 or itself recursively."""
		block = ""
		if self.__use_block() and self.__depth < self.__MAX_DEPTH:
			marker = random.choice(self.__BLOCk_MARKER)
			self.__depth += 1
			block += "<" + marker + ">"
			block += self.__random_block()
			block += "</" + marker + ">"
		else:
			block += self.__gen_inline()
		return block

	def __gen_inline(self):
		"""Generate a new inline block with __MARKER attribute."""
		inline = "<" + self.__marker + ">"
		# if self.__payload_used == len(self.__payload) - 1:
		# 	inline += str(self.__payload[self.__payload_used]
		# else:
		inline += self.__payload[self.__payload_used].decode()
		self.__payload_used += 1
		inline += "</" + self.__marker + ">"
		return inline

# todo find a better name for the following class
class Obfuscate:
	"""(De)obfuscate some content in order to bypass some detection tools
	used by the proxy."""

	__url_img = [".jpg", ".gif", ".png"]
	__url_text = ["toto.html", "fooo.html", "barrr.php"]
	__end_url = __url_img + __url_text # end of an url
	__end_url = __url_text # end of an url
	__element = ["span", "a", "i"] # every markers used to store data
	__GIF = "gif"
	__JPG = "jpg"
	__PNG = "png"
	__headers = {__GIF: b'GIF89a',
	             __JPG: b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00' +
	                    b'\x01\x00\x01\x00\x00\xff\xfe\x00;CREATOR: ' +
	                    b'gd-jpeg v1.0 (using IJG JPEG v80), quality : 92',
	             __PNG: b'\x89PNG\r\n\x1a\n'}

	def __init__(self):
		self.mapping = {}
		i = 0
		for end in self.__url_text:
			self.mapping[end] = self.__element[i]
			i += 1

	def random_url(self):
		"""Generate a random url."""
		begin = ''.join(random.choice(string.ascii_lowercase +
		                              string.digits + "/")
		                for _ in range(URL_SIZE))

		end = random.choice(self.__end_url)

		if end in self.__url_img and begin[-1] == "/":
			begin += "".join(random.choice(string.ascii_lowercase
			                               + string.digits)
			                 for _ in range(SUP_SIZE))
		return begin + end

	def obfuscate(self, url, data):
		"""Obfuscate data using url to determine wich kind of obfuscation to
		used."""
		if url[-4:] in self.__url_img:
			return self.__obfuscate_image(url, data)
		if url[-9:] in self.__url_text:
			return self.__obfuscate_text(url, data)
		raise ValueError("No obfuscation scheme for this url {}.".format(url))

	def deobfuscate(self, url, data):
		"""Deobfuscate data using url to determine wich kind of
		deobfuscation to use."""
		if url[-4:] in self.__url_img:
			return self.__deobfuscate_image(url, data)
		if url[-9:] in self.__url_text:
			return self.__deobfuscate_text(url, data)
		raise ValueError("No deobfuscation scheme for this url {}.".format(url))

	def __obfuscate_image(self, url, data):
		file_type = url[-3:]
		header = self.__headers[file_type]
		return header + data

	def __deobfuscate_image(self, url, data):
		file_type = url[-3:]
		header = self.__headers[file_type]
		content = data.replace(header, "".encode())
		return content

	def __obfuscate_text(self, url, data):
		end_url = url[-9:]
		generator = HTMLGenerator(self.mapping[end_url], data)
		return generator.random_page()

	def __deobfuscate_text(self, url, content):
		end_url = url[-9:]
		marker = self.mapping[end_url]
		parser = BeautifulSoup(content, 'html.parser')
		elements = parser.find_all(marker)
		data = ""
		for elt in elements[:-1]:
			data += elt.next
		if int(elements[-1].next) == 2:
			data += "=="
		elif int(elements[-1].next) == 1:
			data += "="
		return data
