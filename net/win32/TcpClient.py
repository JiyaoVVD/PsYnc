# -*- coding: utf-8 -*-

import socket
import threading


class TcpClient(object):

	def __init__(self, ip, port):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((ip, port))

	def start(self):
		threading.Thread(target=self.recv_loop).start()

	def close(self):
		try:
			self.sock.shutdown(socket.SHUT_WR)
			while self.sock.recv(1024):
				pass
		finally:
			self.sock.close()

	def recv_loop(self):
		while True:
			if not self.sock:
				return
			try:
				data = self.sock.recv(1024)
				if data == b"HEARTBEAT":
					self.send_data(b'HEARTBEAT_ACK')
			except:
				break

	def send_data(self, data):
		self.sock.send(data)

	def set_disconnect_callback(self, callback):
		self._disconnect_cb = callback

if __name__ == '__main__':
	client = TcpClient('127.0.0.1', 8080)
	client.start()
	while True:
		data = input("> ")
		data = bytes(data, 'utf-8')
		if not data:
			client.close()
		client.send_data(data)
