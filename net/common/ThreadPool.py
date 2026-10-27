# -*- coding: utf-8 -*-
"""
服务端线程池封装
"""

import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.Singleton import Singleton

NET_THREAD_MAX_WORKER = 10

class ThreadPool(metaclass=Singleton):
	def __init__(self):
		self.executor = ThreadPoolExecutor(max_workers=NET_THREAD_MAX_WORKER)
		self.tasks = []

	def add_task(self, task, *args, **kwargs):
		callback = kwargs.pop('callback')
		future = self.executor.submit(task, *args, **kwargs)
		self.tasks.append((future, callback))


if __name__ == "__main__":
	def task(i):
		time.sleep(random.randint(1, 5))
		return i
	ThreadPool().add_task(task, 1)
	ThreadPool().add_task(task, 2)
	ThreadPool().add_task(task, 3)
	ThreadPool().add_task(task, 4)
	ThreadPool().add_task(task, 5)