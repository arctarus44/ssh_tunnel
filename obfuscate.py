"""Implement a class to (de)obfuscate the traffic between the server side and
client side of the tunnel"""

import string
import random
import abc

URL_SIZE = 15
SUP_SIZE = 5

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
		return

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
