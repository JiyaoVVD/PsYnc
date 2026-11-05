# -*- coding: utf-8 -*-

import itertools
from net.protos import rpc_pb2


class RpcDispatcher(object):
	def __init__(self, server):
		self.server = server

	def dispatch(self, msg):
		pak = rpc_pb2.RpcCall.FromString(msg)
		mailbox = pak.mailbox
		entity = self.server.get_entity_by_mailbox(mailbox)
		if not entity:
			return
		self._invoke(entity, pak)

	def _invoke(self, entity, rpc_call):
		if rpc_call.mailbox != entity.mailbox:
			raise RuntimeError("Rpc call from unknown mailbox %s" % rpc_call.mailbox)
		method_name = rpc_call.method_name
		rpc_defs = entity.__rpc_methods__
		if method_name not in rpc_defs:
			raise RuntimeError("Rpc method %s not found" % method_name)
		rpc_def = rpc_defs[method_name]
		handler_name = rpc_def.handler
		handler = getattr(entity, handler_name, None)
		if not handler:
			raise RuntimeError("Rpc method %s handler not implemented" % method_name)
		args = []
		for arg_type, arg in itertools.zip_longest(rpc_def.args, rpc_call.args):
			if arg_type is None:
				raise RuntimeError("Rpc method %s has too many arguments" % method_name)
			args.append(arg_type.deserialize(arg))
		return handler(*args)
