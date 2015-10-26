"""Implement a class to (de)obfuscate the traffic between the server side and
client side of the tunnel"""

import string
import random

URL_SIZE = 15
SUP_SIZE = 5

# todo find a better name for the following class
class Obfuscate:

	# end of an url
	__url_img  = [".jpg", ".bmp"]
	__url_text = ["toto.html", "fooo.html", "barr.php"]
	__end_url = __url_img + __url_text
	__markers = ["p", "a", "h2"]

	def __init__(self):
		self.mapping = {}
		i = 0
		for end in self.__url_text:
			self.mapping[end] = self.__markers[i]
			i+=1

	def __random_url(self):
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
		pass

	def deobfuscate(self, url, data):
		"""Deobfuscate the data using url to determine wich kind of
		deobfuscation to use."""
		pass
