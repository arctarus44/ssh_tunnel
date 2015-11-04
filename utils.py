""" Some stuff needed by both the client and the tunnel daemon."""

import configparser as cp


class ConfigHandler(cp.ConfigParser):

	SCT_TUNNELD = "Tunneld"
	OPT_HTTP_HOST = "http_host"
	OPT_HTTP_PORT = "http_port"
	OPT_LISTEN_HOST ="listening_host"
	OPT_LISTEN_PORT = "listening_port"

	SCT_CLIENT = "Client"
	OPT_FORWARD_HOST = "forwarding_host"
	OPT_FORWARD_PORT = "forwarding_port"

	__LOCALHOST = "localhost"
	__DFLT_HTTP_PORT = 80
	__DFLT_FORWARD_PORT = 22
	__DFLT_LISTEN_PORT = 2222

	# def __init__(self):
	__DEFAULT_CONF = {SCT_TUNNELD: { OPT_HTTP_HOST: __LOCALHOST,
									 OPT_HTTP_PORT: __DFLT_HTTP_PORT,
									 OPT_LISTEN_PORT: __DFLT_LISTEN_PORT,
									 OPT_LISTEN_HOST: __LOCALHOST},
					  SCT_CLIENT: {
						  OPT_FORWARD_HOST: __LOCALHOST,
						  OPT_FORWARD_PORT: __DFLT_FORWARD_PORT}}

	def read_conf(self, conf_file="tunnel.ini"):
		"""Read the configuration file and set the default value."""
		self.read_dict(self.__DEFAULT_CONF)
		self.read("tunnel.ini")
