# -*- coding: utf-8 -*-

import time
import socket
import asyncio
from asyncio import StreamReader, StreamWriter
from asyncio.trsock import TransportSocket


class ClientProxy(object):
	def __init__(self, server, reader, writer, addr):
		self.server = server
		self.reader = reader
		self.writer = writer
		self.addr = addr

	def fileno(self):
		return self.sock.fileno()

	def recv_data(self, buffer_size=1024):
		return self.sock.read(buffer_size)

	def send_data(self, data):
		self.writer.write(data)

	async def recv_data_async(self, buff_size=1024):
		data = await self.reader.read(buff_size)
		return data

	def start(self):
		return

	def close(self):
		self.sock.close()


class TcpServer(object):

	def __init__(self, host='0.0.0.0', port=8080):
		self.server = None
		self.host = host
		self.port = port
		self.clients = {}

	async def handle_client(self, reader: StreamReader, writer: StreamWriter):
		client_socket = writer.get_extra_info("socket")
		addr = writer.get_extra_info('peername')
		client_id = client_socket.fileno()
		self.clients[client_socket.fileno()] = client_proxy = ClientProxy(self, reader, writer, addr)

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
		self.server = await asyncio.start_server(self.handle_client, self.host, self.port, reuse_address=True, reuse_port=False)
		async with self.server:
			await self.server.serve_forever()

	def start(self):
		asyncio.run(self.start_async())


if __name__ == '__main__':
	server = TcpServer('127.0.0.1', 8080)
	server.start()