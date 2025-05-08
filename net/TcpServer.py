# -*- coding: utf-8 -*-

import socket
import threading

class TcpServer(object):

	def __init__(self, host='0.0.0.0', port=8080):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.bind((host, port))

	def start(self):
		self.sock.listen(5)
		while True:
			client, addr = self.sock.accept()
			threading.Thread(target=self.handle_client, args=(client,)).start()

	def handle_client(self, conn: socket.socket):
		try:
			while True:
				data = conn.recv(1024)
				if not data: break
				conn.sendall(data)
		finally:
			conn.close()