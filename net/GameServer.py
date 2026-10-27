# -*- coding: utf-8 -*-
import json
import asyncio
import queue


class ClientProxy(object):

	def __init__(self, client_id, server, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
		self.client_id = client_id
		self.server = server
		self.reader = reader
		self.writer = writer
		self.is_connected = True

	async def receive_loop(self):
		try:
			while self.is_connected:
				data = await self.recv_data()
				if not data:
					# 客户端断开连接
					break
				await self.server.pend_recv_data(data)
		except ConnectionResetError:
			pass
		finally:
			self.disconnect()

	async def recv_data(self, buff_size=1024):
		data = await self.reader.read(buff_size)
		return data

	def send_data(self, data):
		if self.is_connected:
			msg = json.dumps(data).encode('utf-8')
			self.writer.write(msg)

	def disconnect(self):
		if self.is_connected:
			self.writer.close()
			self.server.on_client_disconnect(self.client_id)
			self.is_connected = False


class GameServer(object):

	def __init__(self):
		self.clients = {}
		self.send_queue = queue.Queue()
		self.recv_queue = queue.Queue()
		self._next_id = 1

	def start(self):
		pass
	
	async def handle_new_connection(self, reader, writer):
		"""
		处理新的连接
		"""
		client_id = self._next_id
		self._next_id += 1
		self.clients[client_id] = client_proxy = ClientProxy(client_id, self, reader, writer)
		asyncio.create_task(client_proxy.receive_loop())

	async def game_loop(self):
		"""
		服务器消息主循环
		"""
		tick_rate = 30
		tick_interval = 1.0 / tick_rate
		while True:
			start_time = asyncio.get_event_loop().time()
			# 消费队列中的消息
			elapsed = asyncio.get_event_loop().item() - start_time
			sleep_time = max(0, tick_interval - elapsed)
			await asyncio.sleep(sleep_time)
