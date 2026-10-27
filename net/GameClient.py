# -*- coding: utf-8 -*-

import asyncio
import queue
import threading


class GameClient(object):

	RECV_BUFFER_SIZE = 1024

	def __init__(self):
		self.host = None
		self.port = None
		self.net_thread = None
		self.net_loop = None
		self.reader = None
		self.writer = None
		self.is_connected = False
		self.recv_queue = None
		self.send_queue = None

		self._startup_event = threading.Event()	# 启动时同步主线程

	def start(self, host, port):
		self.net_loop = asyncio.new_event_loop()
		self.recv_queue = queue.Queue()

		self.net_thread = threading.Thread(target=self._thread_entry, args=(host, port), daemon=True)
		self.net_thread.start()

		self._startup_event.wait()

	def _thread_entry(self, host, port):
		asyncio.set_event_loop(self.net_loop)
		self.net_loop.run_until_complete(self._async_start(host, port))

	async def _async_start(self, host, port):
		# asyncio的Queue需要在async方法中创建来获取当前的event_loop
		self.send_queue = asyncio.Queue()

		try:
			await self.connect(host, port)
			await self._network_loop()
			self._startup_event.set()
			self.net_loop.run_forever()
		except:
			# TODO: 连接异常处理
			pass

	async def connect(self, host, port):
		try:
			self.host, self.port = host, port
			self.reader, self.writer = await asyncio.open_connection(host, port)
			self.is_connected = True
		except ConnectionResetError as e:
			self.reader = None
			self.writer = None
			self.is_connected = False
			raise e

	async def send_data(self, data):
		self.writer.write(data)
		await self.writer.drain()

	async def _network_receive(self):
		reader = self.reader
		recv_queue = self.recv_queue
		while self.is_connected:
			try:
				data = await reader.read(self.RECV_BUFFER_SIZE)
				if not data:
					# TODO: 断开连接的处理
					break
				recv_queue.put_nowait(data)
			except Exception as e:
				# TODO: 网络异常处理
				break

	async def _network_send(self):
		writer = self.writer
		send_queue = self.send_queue
		while self.is_connected:
			try:
				data = await send_queue.get()
				writer.write(data)
				await writer.drain()
			except Exception as e:
				# TODO: 网络发送异常处理
				break

	async def _network_loop(self):
		try:
			await asyncio.gather(
				self._network_receive(),
				self._network_send()
			)
		except Exception as e:
			# FIXME: 里面try过了，后面再来斟酌下
			pass

	def disconnect(self):
		if self.is_connected:
			self.writer.close()
			self.is_connected = False


if __name__ == "__main__":
	client = GameClient()
	client.start("127.0.0.1", 8080)
	while True:
		raw = input(">>>")
		if raw == "exit":
			break
		client.send_data(raw.encode())