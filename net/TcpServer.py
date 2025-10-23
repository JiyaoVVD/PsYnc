# -*- coding: utf-8 -*-

import socket
import threading


class ClientProxy(object):
	def __init__(self, server, sock, addr):
		self.server = server
		self.sock = sock
		self.addr = addr
		self._thread = None

	def start(self):
		self._thread = threading.Thread(target=self.handle_client)
		self._thread.start()

	def close(self):
		self.sock.close()

	def handle_client(self):
		try:
			while True:
				data = self.sock.recv(1024)
				if not data:
					break
				print(f"recv>{data}")
				self.sock.sendall(data)
		except socket.timeout:
			print("connect timeout")
		except socket.error as e:
			print(f"socket error: {e}")
		finally:
			self.close()


class TcpServer(object):

	def __init__(self, host='0.0.0.0', port=8080):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.bind((host, port))
		self.clients = []

	def start(self):
		self.sock.listen(5)
		while True:
			sock, addr = self.sock.accept()
			client = ClientProxy(self, sock, addr)
			self.clients.append(client)
			client.start()

if __name__ == '__main__':
	server = TcpServer()
	server.start()