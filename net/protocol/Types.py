# -*- coding: utf-8 -*-

from net.protos import types_pb2


class Value:
	def __init__(self, default=None):
		self.default = default

	def serialize(self, value):
		raise NotImplementedError

	def deserialize(self, pak):
		raise NotImplementedError

	def default_value(self):
		return self.default

class Int(Value):
	def serialize(self, value):
		value = self.default if value is None else value
		return types_pb2.Value(int_val=value)

	def deserialize(self, pak):
		return pak.int_val

class Float(Value):
	def serialize(self, value):
		value = self.default if value is None else value
		return types_pb2.Value(float_val=value)

	def deserialzie(self, pak):
		return pak.float_val

class Str(Value):
	def serialize(self, value):
		value = self.default if value is None else value
		return types_pb2.Value(str_val=value)

	def deserialize(self, pak):
		return pak.str_val

class Bool(Value):
	def serialize(self, value):
		value = self.default if value is None else value
		return types_pb2.Value(bool_val=value)

	def deserialize(self, pak):
		return pak.bool_val

class Bytes(Value):
	def serialzie(self, value):
		value = self.default if value is None else value
		return types_pb2.Value(bytes_val=value)

	def deserialize(self, pak):
		return pak.bytes_val

if __name__ == "__main__":
	t = Int(2)
	pak = t.serialize(123)
	print(pak)
	print(t.deserialize(pak))