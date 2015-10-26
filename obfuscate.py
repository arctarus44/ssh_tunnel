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

	@classmethod
	def random_url(cls):
		"""Generate a random url."""
		begin = ''.join(random.choice(string.ascii_lowercase +
		                              string.digits + "/")
		                for _ in range(URL_SIZE))

		end = random.choice(cls.__end_url)

		if end in cls.__url_img and begin[-1] == "/":
			begin += "".join(random.choice(string.ascii_lowercase
			                               + string.digits)
			                 for _ in range(SUP_SIZE))
		return begin + end
