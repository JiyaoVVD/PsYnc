# -*- coding: utf-8 -*-

from net.rpc.RpcStub import RpcStub

class RpcMethod:
	def __init__(self, target="server", handler=None, args=()):
		self.target = target
		self.handler = handler
		self.args = args

	def __get__(self, instance, owner):
		"""
		entity自身调用代表本地调用
		"""
		if instance is None:
			return self
		method = getattr(instance, self.handler, None)
		if not method:
			raise AttributeError("Rpc Method handler %s not found" % self.handler)
		return method


class RpcCallableMixin(object):
	__rpc_methods__ = {}

	def __init_subclass__(cls, **kwargs):
		super().__init_subclass__(**kwargs)
		# 按 MRO 收集最终可见的声明，避免父子类共享或污染注册表。
		attributes = {}
		for base in reversed(cls.__mro__):
			attributes.update(vars(base))
		cls.__rpc_methods__ = {
			name: value for name, value in attributes.items()
			if isinstance(value, RpcMethod)
		}

	def __init__(self, proxy):
		self.mailbox = None
		self.stub = RpcStub(self, proxy)