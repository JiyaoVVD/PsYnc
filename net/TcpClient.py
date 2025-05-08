# -*- coding: utf-8 -*-

import socket
import threading

class TcpClient(object):

	def __init__(self, ip, port):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((ip, port))

	def recv_loop(self):
		while True:
			try:
				data = self.sock.recv(1024)
				print(data)
			except:
				break