# -*- coding: utf-8 -*-
from net.protos import rpc_pb2
from net.protocol.Types import (
	Int, Float, Bool, Str, Bytes
)


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