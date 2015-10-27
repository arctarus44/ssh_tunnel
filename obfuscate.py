"""Implement a class to (de)obfuscate the traffic between the server side and
client side of the tunnel"""

import string
import random
import abc

URL_SIZE = 15
SUP_SIZE = 5

# todo find a better name for the following class
class Obfuscate:

	__metaclass__ = abc.ABCMeta

	# end of an url
	__url_img  = [".jpg", ".gif", ".png"]
	__url_text = ["toto.html", "fooo.html", "barr.php"]
	__end_url = __url_img + __url_text

	def __init__(self):
		pass

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

	@abc.abstractmethod
	def obfuscate(self, url, data):
		"""Obfuscate data using url to determine wich kind of obfuscation to
		used."""
		return

	@abc.abstractmethod
	def deobfuscate(self, url, data):
		"""Deobfuscate the data using url to determine wich kind of
		deobfuscation to use."""
		return

class ObfuscateImage(Obfuscate):

	__JPG = "jpg"
	__PNG = "png"
	__GIF = "gif"
	__headers = {__GIF: b'GIF89a',
	             __PNG: b'\x89PNG\r\n\x1a',
	             __JPG: b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xfe\x00;CREATOR: gd-jpeg v1.0 (using IJG JPEG v80)'}


	def obfuscate(self, url, data):
		file_type = url[-3:]
		print(file_type)
		header = self.__headers[file_type]
		return header + data

	def deobfuscate(self, url, data):
		file_type = url[-3:]
		header = self.__headers[file_type]
		content = data.replace(header, "".encode())
		return content

# class ObfuscateText(Obfuscate):

	# __markers = ["p", "a", "h2"] # every markers used to store data
	# def __init__(self):
	# 	self.mapping = {}
	# 	i = 0
	# 	for end in self.__url_text:
	# 		self.mapping[end] = self.__markers[i]
	# 		i+=1
