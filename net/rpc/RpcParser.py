# -*- coding: utf-8 -*-

from net.protos import rpc_pb2, types_pb2


class ClientRpcCallerMixin(object):
	def __init__(self, stub):
		self.mailbox = None
		self.stub = stub

	def call(self, method_name, *args):
		pass

class ServerRpcCallerMixin(object):
	def __init__(self, stub):
		self.mailbox = None
		self.stub = stub


if __name__ == "__main__":
	rpc_call = rpc_pb2.RpcCall(
		mailbox=1,
		args=[
			{"int_val": 3},
			{"str_val": "abc"},
			{"bool_val": True}
		]
	)
	print(rpc_call)