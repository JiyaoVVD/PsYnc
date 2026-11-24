# -*- coding: utf-8 -*-

from net.protos import types_pb2


def serialize_by_type(value):
	value_type = type(value)
	codec = VALUE_TYPE_MAP.get(value_type)
	if codec is None:
		if isinstance(value, list):
			codec = VALUE_TYPE_MAP[list]
		elif isinstance(value, dict):
			codec = VALUE_TYPE_MAP[dict]
		else:
			raise RuntimeError("Unsupported value type: %s" % value_type.__name__)
	return codec.serialize(value)


def deserialize_by_type(pak):
	field_name = pak.WhichOneof("kind")
	if field_name not in VALUE_FIELD_MAP:
		raise RuntimeError("Unsupported value field: %s" % field_name)
	return VALUE_FIELD_MAP[field_name].deserialize(pak)


ALL_TYPES = set()

class _ValueMeta(type):
	def __new__(cls, name, bases, attrs):
		new_cls = super().__new__(cls, name, bases, attrs)
		if name != "Value":
			ALL_TYPES.add(new_cls)
		return new_cls


class Value(metaclass=_ValueMeta):
	def __init__(self, default=None):
		self.default = default

	def serialize(self, value):
		raise NotImplementedError

	def deserialize(self, pak):
		raise NotImplementedError

	def check(self, value):
		return True

	def default_value(self):
		return self.default

class Int(Value):
	def serialize(self, value):
		value = self.default if value is None else value
		return types_pb2.Value(int_val=value)

	def deserialize(self, pak):
		return pak.int_val

	def check(self, value):
		return type(value) == int


class Float(Value):
	def serialize(self, value):
		value = self.default if value is None else value
		return types_pb2.Value(float_val=value)

	def deserialize(self, pak):
		return pak.float_val

	def check(self, value):
		return type(value) in (float, int)
	

class Str(Value):
	def serialize(self, value):
		value = self.default if value is None else value
		return types_pb2.Value(str_val=value)

	def deserialize(self, pak):
		return pak.str_val

	def check(self, value):
		return type(value) == str


class Bool(Value):
	def serialize(self, value):
		value = self.default if value is None else value
		return types_pb2.Value(bool_val=value)

	def deserialize(self, pak):
		return pak.bool_val

	def check(self, value):
		return type(value) == bool


class Bytes(Value):
	def serialize(self, value):
		value = self.default if value is None else value
		return types_pb2.Value(bytes_val=value)

	def deserialize(self, pak):
		return pak.bytes_val

	def check(self, value):
		return type(value) == bytes


class List(Value):
	def serialize(self, value):
		value = self.default if value is None else value
		list_value = types_pb2.ListValue()
		for item in value:
			list_value.items.append(serialize_by_type(item))
		return types_pb2.Value(list_val=list_value)

	def deserialize(self, pak):
		value = []
		for item in pak.list_val.items:
			value.append(deserialize_by_type(item))
		return value

	def check(self, value):
		"""
		list和dict都只检查最外层容器的类型就行了，内部元素的类型检查交给协议层实现
		"""
		return type(value) == list or issubclass(type(value), list)


class Dict(Value):
	def serialize(self, value):
		value = self.default if value is None else value
		kv_pair = types_pb2.KVPair
		dict_value = types_pb2.DictValue()
		for k, v in value.items():
			dict_value.items.append(kv_pair(key=serialize_by_type(k), value=serialize_by_type(v)))
		return types_pb2.Value(dict_val=dict_value)

	def deserialize(self, pak):
		value = {}
		for kv_pair in pak.dict_val.items:
			k = kv_pair.key
			v = kv_pair.value
			value[deserialize_by_type(k)] = deserialize_by_type(v)
		return value

	def check(self, value):
		return type(value) == dict or issubclass(type(value), dict)


VALUE_TYPE_MAP = {
	int: Int(),
	str: Str(),
	bool: Bool(),
	float: Float(),
	bytes: Bytes(),
	list: List(),
	dict: Dict(),
}

VALUE_FIELD_MAP = {
	"int_val": Int(),
	"float_val": Float(),
	"str_val": Str(),
	"bool_val": Bool(),
	"bytes_val": Bytes(),
	"list_val": List(),
	"dict_val": Dict(),
}


if __name__ == "__main__":
	v = {1: 2, "abc": True, "list": ["a", 1, True]}
	pak = Dict().serialize(v)
	print(pak)
	print(Dict().deserialize(pak))