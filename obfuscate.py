"""Implement a class to (de)obfuscate the traffic between the server side and
client side of the tunnel"""

import string
import random
import abc

URL_SIZE = 15
SUP_SIZE = 5
SPLIT = 10						# split every 10har

class HTMLGenerator:

	__MAX_DEPTH = 7
	__BLOCk_MARKER = ["div","p", "h1" ,"h2", "h3"]
	__PROBA_BLOCk = 75			# 0.75 of chance to have a bloc

	def __init__(self, marker, payload):
		self.__MARKER = marker
		self.__payload = [payload[i:i+SPLIT]
		                  for i in range(0, len(payload), SPLIT)]
		self.__payload_used = 0
		self.__depth = 1

	def __use_block(self):
		rand = random.randint(0,100)
		if rand > self.__PROBA_BLOCk:
			return False
		else:
			return True

	def random_page(self):
		page = '<html><body>'
		page += self.__random_body()
		page += '</body></html>'
		return page

	def __random_body(self):
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
		block = ""
		if self.__use_block() and self.__depth < self.__MAX_DEPTH:
			marker = random.choice(self.__BLOCk_MARKER)
			self.__depth += 1
			block += "<" + marker + ">"
			block += self.__random_block()
			block +=  "</" + marker + ">"
		else:
			block += self.__gen_inline()
		return block

	def __gen_inline(self):
		inline = "<" + self.__MARKER + ">"
		inline += self.__payload[self.__payload_used]
		self.__payload_used += 1
		inline += "</" + self.__MARKER + ">"
		return inline

# todo find a better name for the following class
class Obfuscate:

	__url_img  = [".jpg", ".gif", ".png"]
	__url_text = ["toto.html", "fooo.html", "barr.php"]
	__end_url = __url_img + __url_text # end of an url
	__element = ["span", "a", "i"] # every markers used to store data

	def __init__(self):
		self.mapping = {}
		i = 0
		for end in self.__url_text:
			self.mapping[end] = self.__element[i]
			i+=1

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
		if url[-3:] in self.__url_img:
			return self.__obfuscate_image(url, data)
		if url[-9:] in self.__url_text(url, data):
			return self.__obfuscate_text(url, data)
		raise ValueError("No obfuscation scheme for this url")

	def deobfuscate(self, url, data):
		"""Deobfuscate the data using url to determine wich kind of
		deobfuscation to use."""
		return

	def __obfuscate_image(self, url, data):
		file_type = url[-3:]
		header = self.__headers[file_type]
		return header + data

	def __deobfuscate__image(self, url[-3:], data):
		file_type = url[-3:]
		header = self.__headers[file_type]
		content = data.replace(header, "".encode())
		return content

	def __obfuscate_text(self, url, data):
		pass

	def __deobfuscate__text(self, url, data):
		pass
