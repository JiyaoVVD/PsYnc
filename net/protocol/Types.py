# -*- coding: utf-8 -*-

from net.protos import types_pb2


def serialize_by_type(value):
	value_type = type(value)
	if value_type not in VALUE_TYPE_MAP:
		raise RuntimeError("Unsupported value type: %s" % value_type.__name__)
	return VALUE_TYPE_MAP[value_type].serialize(value)


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
			item_field = item.WhichOneof('kind')
			item_value = getattr(item, item_field) if item_field is not None else None
			value.append(item_value)
		return value


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
			key_field = k.WhichOneof('kind')
			key_value = getattr(k, key_field) if key_field is not None else None
			value_field = v.WhichOneof('kind')
			value_value = getattr(v, value_field) if value_field is not None else None
			value[key_value] = value_value
		return value


VALUE_TYPE_MAP = {
	int: Int(),
	str: Str(),
	bool: Bool(),
	float: Float(),
	bytes: Bytes(),
	list: List(),
	dict: Dict(),
}


if __name__ == "__main__":
	v = {1: 2, "abc": True, "list": ["a", 1, True]}
	pak = Dict().serialize(v)
	print(pak)
	print(Dict().deserialize(pak))