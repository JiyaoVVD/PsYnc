# -*- coding: utf-8 -*-
import asyncio
import threading
import queue


class ClientProxy(object):

	RECV_BUFFER_SIZE = 1024

	def __init__(self, client_id, server, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
		self.client_id = client_id
		self.server = server
		self.reader = reader
		self.writer = writer
		self.is_connected = True

		self.send_queue = None

	async def start(self):
		self.send_queue = asyncio.Queue()
		await self.network_loop()

	async def network_loop(self):
		try:
			await asyncio.gather(
				self._network_receive(),
				self._network_send()
			)
		except Exception as e:
			print(f"network error: {e}")
			# FIXME: 里面try过了，后面再来斟酌下
			pass

	async def _network_receive(self):
		reader = self.reader
		while self.is_connected:
			try:
				print(f"client_{self.client_id} waiting for data received...")
				data = await reader.read(self.RECV_BUFFER_SIZE)
				print(f"client_{self.client_id} receive data: {data}")
				if not data:
					# TODO: 断开连接的处理
					break
				self.server.recv_queue.put_nowait(data)
				# TODO: 交给协议层decode之后push进服务端的公共接收队列
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

	async def recv_data(self, buff_size=1024):
		data = await self.reader.read(buff_size)
		return data

	def send_data(self, data):
		if self.is_connected and self.send_queue is not None:
			self.server.net_loop.call_soon_threadsafe(self.send_queue.put_nowait, data)

	def disconnect(self):
		if self.is_connected:
			self.writer.close()
			self.server.on_client_disconnect(self.client_id)
			self.is_connected = False


class GameServer(object):

	def __init__(self):
		self.host = None
		self.port = None
		self.net_thread = None	# 玩具项目，先用一个线程处理所有网络事件
		self.net_loop = None
		self.clients = {}
		self.recv_queue = queue.Queue()
		self._next_id = 1
		self.server = None

	def start(self, host, port):
		self.host = host
		self.port = port
		self.net_loop = asyncio.new_event_loop()
		self.net_thread = threading.Thread(target=self._thread_entry, args=(host, port), daemon=True)
		self.net_thread.start()

	def _thread_entry(self, host, port):
		self.net_loop.run_until_complete(self._serve(host, port))

	async def _serve(self, host, port):
		self.server = await asyncio.start_server(self.handle_new_connection, host, port)
		await self.server.serve_forever()

	async def handle_new_connection(self, reader, writer):
		"""
		处理新的连接
		"""
		client_id = self._next_id
		self._next_id += 1
		self.clients[client_id] = client_proxy = ClientProxy(client_id, self, reader, writer)
		print(f"client {client_id} connected.")
		await client_proxy.start()


def recv_data(server):
	while True:
		try:
			data = server.recv_queue.get(timeout=0.1)
			if data:
				print(f">>>recv: {data}")
				server.clients[1].send_data(b"Echo: " + data)
		except queue.Empty:
			pass
		


if __name__ =="__main__":
	server = GameServer()
	server.start("127.0.0.1", 8080)
	print("running...")
	recv_data(server)
