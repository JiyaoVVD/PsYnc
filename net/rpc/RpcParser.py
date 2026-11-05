# -*- coding: utf-8 -*-

import itertools
from net.protos import rpc_pb2
from net.protocol.Types import (
	Int, Float, Bool, Str, Bytes
)


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


class RpcStub(object):
	TYPE_2_PROTO = {
		int: Int(),
		str: Str(),
		bool: Bool(),
		float: Float(),
		bytes: Bytes(),
		list: None,
		dict: None,
	}

	def __init__(self, owner, proxy):
		"""
		:param proxy: 网络层的通信代理
		"""
		self.owner = owner
		self.proxy = proxy

	def _encode_rpc(self, mailbox, method_name, args):
		rpc_call = rpc_pb2.RpcCall()
		rpc_call.mailbox = mailbox
		rpc_call.method_name = method_name
		for arg in args:
			arg_type = type(arg)
			if arg_type not in RpcStub.TYPE_2_PROTO:
				raise RuntimeError("Unsupported rpc argument type: %s" % arg_type.__name__)
			value = RpcStub.TYPE_2_PROTO[arg_type].serialize(arg)
			rpc_call.args.append(value)
		return rpc_call.SerializeToString()

	def on_dispatch(self, rpc_call):
		if rpc_call.mailbox != self.owner.mailbox:
			raise RuntimeError("Rpc call from unknown mailbox %s" % rpc_call.mailbox)
		method_name = rpc_call.method_name
		rpc_defs = self.owner.__rpc_methods__
		if method_name not in rpc_defs:
			raise RuntimeError("Rpc method %s not found" % method_name)
		rpc_def = rpc_defs[method_name]
		handler_name = rpc_def.handler
		handler = getattr(self.owner, handler_name, None)
		if not handler:
			raise RuntimeError("Rpc method %s handler not implemented" % method_name)
		args = []
		for arg_type, arg in itertools.zip_longest(rpc_def.args, rpc_call.args):
			if arg_type is None:
				raise RuntimeError("Rpc method %s has too many arguments" % method_name)
			args.append(arg_type.deserialize(arg))
		return handler(*args)

	def call(self, mailbox, method_name, *args):
		"""
		当前端不知道远端rpc的参数类型定义，根据实参类型序列化
		"""
		data = self._encode_rpc(mailbox, method_name, args)
		self.proxy.send_data(data)

	def __getattr__(self, name):
		def invoke(*args):
			mailbox = self.owner.mailbox
			if mailbox is None:
				raise RuntimeError("Entity mailbox is not assigned")
			return self.call(mailbox, name, *args)
		return invoke


class RpcDispatcher(object):
	def __init__(self, server):
		self.server = server

	def dispatch(self, msg):
		pak = rpc_pb2.RpcCall.FromString(msg)
		mailbox = pak.mailbox
		entity = self.server.get_entity_by_mailbox(mailbox)
		if not entity:
			return
		entity.stub.on_dispatch(pak)


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


if __name__ == "__main__":
	dispatcher = None
	class FakeProxy:
		def send_data(self, data):
			print(data)
			dispatcher.dispatch(data)

	class Receiver(RpcCallableMixin):
		test = RpcMethod(target="server", handler="on_test", args=(Int(), Str()))

		def on_test(self, a, b):
			print("on_test", a, b)

	class Sender(RpcCallableMixin):
		pass

	sender = Sender(FakeProxy())

	receiver = Receiver(FakeProxy())
	receiver.mailbox = 321
	# sender 表示接收实体的远端引用，mailbox 指向同一个目标。
	sender.mailbox = receiver.mailbox

	class FakeServer(object):
		def get_entity_by_mailbox(self, mailbox):
			return receiver if mailbox == receiver.mailbox else None

	dispatcher = RpcDispatcher(FakeServer())
	sender.stub.test(1, "2")
