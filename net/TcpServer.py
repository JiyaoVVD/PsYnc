# -*- coding: utf-8 -*-

import time
import socket
import threading
import sys

class ClientProxy(object):
	def __init__(self, server, sock, addr):
		self.server = server
		self.sock = sock
		self.sock.setblocking(False)
		self.addr = addr
		self._thread = None

		self.heartbeat_last_send = time.time()
		self.heartbeat_last_recv = time.time()

	def fileno(self):
		return self.sock.fileno()

	def recv_data(self, buffer_size=1024):
		return self.sock.recv(buffer_size)

	def send_data(self, data):
		self.sock.send(data)

	async def recv_data_async(self, buff_size=1024):
		data = await self.sock.recv(buff_size)
		return data

	def start(self):
		return

	def close(self):
		self.sock.close()

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


if sys.platform == "win32":
	import asyncio
	from asyncio import StreamReader, StreamWriter

	class TcpServer(object):

		def __init__(self, host='0.0.0.0', port=8080):
			self.server = None
			self.sock = None
			self.host = host
			self.port = port
			self.clients = {}

		async def handle_client(self, reader: StreamReader, writer: StreamWriter):
			client_socket = writer.get_extra_info("socket")
			addr = writer.get_extra_info('peername')
			client_id = client_socket.fileno()
			self.clients[client_socket.fileno()] = client_proxy = ClientProxy(self, client_socket, addr)

			try:
				while True:
					data = await client_proxy.recv_data_async(1024)
					if not data:
						break
					message = data.decode()
					print(f">>>recv: {message}")
					writer.write(f"{message}".encode())
					await writer.drain()
			finally:
				writer.close()
				await writer.wait_closed()
				if client_id in self.clients:
					del self.clients[client_id]

		async def start_async(self):
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.sock.bind((self.host, self.port))
			self.sock.setblocking(False)
			self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.server = await asyncio.start_server(self.handle_client, self.host, self.port, reuse_address=True, reuse_port=False)
			async with self.server:
				await self.server.serve_forever()

		def start(self):
			asyncio.run(self.start_async())

elif sys.platform == "linux":
	import select
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

else:
	class TcpServer(object):
		def start(self):
			pass

if __name__ == '__main__':
	server = TcpServer('0.0.0.0', 8080)
	server.start()