# -*- coding: utf-8 -*-

import asyncio


class GameClient(object):

	def __init__(self):
		self.reader = None
		self.writer = None
		self.is_connected = False
		self.pending_data = asyncio.Queue()

	async def connect(self, host, port):
		try:
			self.reader, self.writer = await asyncio.open_connection(host, port)
			self.is_connected = True
		except ConnectionResetError:
			self.reader = None
			self.writer = None
			self.is_connected = False

	async def send_data(self, data):
		self.writer.write(data)
		await self.writer.drain()

	async def recv_data(self, buff_size=1024):
		data = await self.reader.read(buff_size)
		return data

	async def receive_loop(self, data):
		try:
			while self.is_connected:
				data = await self.recv_data()
				self.pending_data.put_nowait(data)
		except ConnectionResetError:
			pass
		finally:
			self.disconnect()

	def disconnect(self):
		if self.is_connected:
			self.writer.close()
			self.is_connected = False