# -*- coding: utf-8 -*-
"""
单例模式元类
"""

class Singleton(type):
	def __init__(cls, name, bases, dict):
		super(Singleton, cls).__init__(name, bases, dict)
		cls._instance = None

	def __call__(cls, *args, **kwargs):
		if cls._instance is None:
			cls._instance = super(Singleton, cls).__call__(*args, **kwargs)
		return cls._instance
