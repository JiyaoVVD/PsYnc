# -*- coding: utf-8 -*-

from net.protos import types_pb2

_PROTO_MAP = {
	int: 'int_val',
	float: 'float_val',
	bool: 'bool_val',
	str: 'str_val',
	bytes: 'bytes_val',
	list: 'list_val',
	dict: 'dict_val',
}


class Value:
	def __init__(self, default=None):
		self.value = default

	def serialize(self, value):
		raise NotImplementedError

	def deserialize(self, pak):
		raise NotImplementedError

class Int(Value):
	def serialize(self, value):
		return types_pb2.Value(int_val=value)

	def deserialize(self, pak):
		return pak.int_val

class Float(Value):
	def serialize(self, value):
		return types_pb2.Value(float_val=value)

	def deserialzie(self, pak):
		return pak.float_val

class Str(Value):
	def serialize(self, value):
		return types_pb2.Value(str_val=value)

	def deserialize(self, pak):
		return pak.str_val

class Bool(Value):
	def serialize(self, value):
		return types_pb2.Value(bool_val=value)

	def deserialize(self, pak):
		return pak.bool_val

class Bytes(Value):
	def serialzie(self, value):
		return types_pb2.Value(bytes_val=value)

	def deserialize(self, pak):
		return pak.bytes_val


def serialize_value(value_type, value):
	prop_name = _PROTO_MAP[value_type]
	value_pak = types_pb2.Value()
	setattr(value_pak, prop_name, value)
	return value_pak

def deserialize_value(value_type, value_pak):
	prop_name = _PROTO_MAP[value_type]
	return getattr(value_pak, prop_name)

if __name__ == "__main__":
	t = Int(2)
	pak = t.serialize(123)
	print(pak)
	print(t.deserialize(pak))