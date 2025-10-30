# -*- coding: utf-8 -*-

import time
import socket
import threading


class ClientProxy(object):
	def __init__(self, server, sock, addr):
		self.server = server
		self.sock = sock
		self.addr = addr
		self._thread = None

		self.heartbeat_last_send = time.time()
		self.heartbeat_last_recv = time.time()

	def start(self):
		self._thread = threading.Thread(target=self.handle_client)
		self._thread.start()
		self._heartbeat_checker = threading.Thread(target=self.heartbeat_checker, args=(10,))
		self._heartbeat_checker.daemon = True
		self._heartbeat_checker.start()
		self._heartbeat_sender = threading.Thread(target=self.heartbeat, args=(5,))
		self._heartbeat_sender.daemon = True
		self._heartbeat_sender.start()

	def close(self):
		self.sock.close()

	def handle_client(self):
		try:
			while True:
				data = self.sock.recv(1024)
				if data == b"HEARTBEAT_ACK":
					self.on_heartbeat_ack()
				print(f"recv>{data}")
				self.sock.sendall(data)
		except socket.timeout:
			print("connect timeout")
		except socket.error as e:
			print(f"socket error: {e}")
		finally:
			self.close()

	def heartbeat(self, interval=30):
		while True:
			try:
				self.sock.sendall(b"HEARTBEAT")
				print("heartbeat send")
				self.heartbeat_last_send = time.time()
				time.sleep(interval)
			except (socket.error, OSError):
				break

	def heartbeat_checker(self, timeout=90):
		while True:
			current_time = time.time()
			if current_time - self.heartbeat_last_recv > timeout:
				self.close()

	def on_heartbeat_ack(self):
		self.heartbeat_last_recv = time.time()



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