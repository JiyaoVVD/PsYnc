# -*- coding: utf-8 -*-

import select
import socket


class ClientProxy(object):
	def __init__(self, socket, addr):
		pass


class TcpServer(object):

	def __init__(self, host='0.0.0.0', port=8080):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.bind((host, port))
		self.sock.setblocking(False)
		self.clients = {}
		self.epoll = select.epoll()

	def start(self):
		try:
			while True:
				events = self.epoll.poll(1)
				for fd, event in events:
					# 新连接
					if fd == self.sock.fileno():
						client_sock, addr = self.sock.accept()
						client_proxy = ClientProxy(self, client_sock, addr)
						client_fd = client_proxy.fileno()
						self.epoll.register(client_fd, select.EPOLLIN)
						self.clients[fd] = client_proxy
						print(f">>>new connection: {addr}")
					# 可读事件
					elif event & select.EPOLLIN:
						data = self.clients[fd].recv_data()
						if data:
							print(f">>>recv: {data}")
							self.clients[fd].send_data(b"Echo:" + data)
						else:
							self.epoll.unregister(fd)
							self.clients[fd].close()
							del self.clients[fd]
		finally:
			self.epoll.unregister(self.sock.fileno())
			self.epoll.close()
			self.sock.close()