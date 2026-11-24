# -*- coding: utf-8 -*-
from net.protos import ssproperty_pb2
from net.protocol.Types import ALL_TYPES, Dict, List

class SyncCond:
	NONE = 0
	OWNER_ONLY = 1
	OWNER_EXCEPT = 2
	ALL = 3


class _HookedList(list):
	def __init__(self, owner, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.owner = owner

	def __setitem__(self, key, value):
		if value != self[key]:
			self.owner.changed = True
		if isinstance(value, dict):
			value = _HookedDict(self.owner, value)
		elif isinstance(value, list):
			value = _HookedList(self.owner, value)
		super().__setitem__(key, value)

	def __delitem__(self, key):
		self.owner.changed = True
		super().__delitem__(key)

	def pop(self, key=-1):
		ret = super().pop(key)
		self.owner.changed = True
		return ret

	def append(self, value):
		if isinstance(value, dict):
			value = _HookedDict(self.owner, value)
		elif isinstance(value, list):
			value = _HookedList(self.owner, value)
		super().append(value)
		self.owner.changed = True

	def extend(self, values):
		new_values = []
		for value in values:
			if isinstance(value, dict):
				value = _HookedDict(self.owner, value)
			elif isinstance(value, list):
				value = _HookedList(self.owner, value)
			new_values.append(value)
		super().extend(new_values)
		self.owner.changed = True

	def insert(self, index, value):
		if isinstance(value, dict):
			value = _HookedDict(self.owner, value)
		elif isinstance(value, list):
			value = _HookedList(self.owner, value)
		super().insert(index, value)
		self.owner.changed = True

	def remove(self, value):
		super().remove(value)
		self.owner.changed = True

	def reverse(self):
		super().reverse()
		self.owner.changed = True

	def sort(self, *args, **kwargs):
		super().sort(*args, **kwargs)
		self.owner.changed = True


class _HookedDict(dict):
	"""
	Hook buildin dict来支持修改key时能够触发同步
	"""
	def __init__(self, owner, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.owner = owner

	def __setitem__(self, key, value):
		if value != self.get(key):
			self.owner.changed = True
		if isinstance(value, dict):
			value = _HookedDict(self.owner, value)
		elif isinstance(value, list):
			value = _HookedList(self.owner, value)
		super().__setitem__(key, value)

	def __delitem__(self, key):
		self.owner.changed = True
		super().__delitem__(key)

	def pop(self, key, default=None):
		self.owner.changed = True
		return super().pop(key, default)

	def popitem(self):
		self.owner.changed = True
		return super().popitem()

	def clear(self):
		self.owner.changed = True
		super().clear()

	def update(self, *args, **kwargs):
		self.owner.changed = True
		super().update(*args, **kwargs)


class Property(object):

	def __init__(self, type=None, default=None, cond=None):
		if type not in ALL_TYPES:
			raise RuntimeError("Unsupported value type: %s" % type.__name__)
		if isinstance(type, (List, Dict)):
			raise RuntimeError("Property do not support List or Dict type")
		self.type = type
		self.default = default
		self.cond = cond

		self.changed = False
		self.value = default

	def __set_name__(self, owner, name):
		if "_ss_properties" not in owner.__dict__:
			raise RuntimeError("Property must be defined in subclass of PropertyHostMixin")
		owner._ss_properties[name] = self

	def __get__(self, instance, owner):
		return self.value

	def __set__(self, instance, value):
		if not self.type.check(value):
			raise RuntimeError("Property value type incompatible: %s, should be %s" % (type(value).__name__, type(self.type).__name__))
		if self.value != value:
			self.changed = True
		# dict和list即使只改一个元素也会全量同步，建议用专门的SyncDict/SyncList
		if isinstance(self.type, Dict):
			value = _HookedDict(self, value)
		elif isinstance(self.type, List):
			value = _HookedList(self, value)
		self.value = value

	def serialize(self):
		value = self.type.serialize(self.value)


class PropertyHostMixin(object):
	def __init_subclass__(cls, **kwargs):
		super().__init_subclass__(**kwargs)
		cls._ss_properties = {}

	def pack_property(self):
		if not hasattr(self, "_ss_properties") or not self._ss_properties\
			or not hasattr(self, "mailbox"):
			return None
		patch = ssproperty_pb2.PropertyPatch(mailbox=self.mailbox)
		changed = False
		for name, prop in self._ss_properties.items():
			if prop.changed:
				changed = True
				change_msg = prop.serialize()
				patch.changes.append(change_msg)
				prop.changed = True
		return patch.SerilaizeToString() if changed else None

	def apply_property_changes(self, changes):
		pass


class SyncDict(dict, PropertyHostMixin):
	"""
	同步字典，支持嵌套。支持通过path一次同步某个字段
	"""
	def __init__(self, ):
		pass


class SyncList(PropertyHostMixin):
	"""
	同步列表，支持嵌套。支持通过path一次同步某个字段
	"""


ALL_SS_PROPERTY_TYPES = ALL_TYPES.union({SyncDict, SyncList})