# -*- coding: utf-8 -*-
from net.protos import ssproperty_pb2
from net.protocol.Types import ALL_TYPES, Dict, List

class SyncCond:
	NONE = 0
	OWNER_ONLY = 1
	OWNER_EXCEPT = 2
	ALL = 3


_MISSING = object()


def _wrap_value(owner, state, value):
	if isinstance(value, list):
		return _HookedList(owner, state, value)
	if isinstance(value, dict):
		return _HookedDict(owner, state, value)
	return value


class _HookedList(list):
	def __init__(self, owner, state, values=(), /):
		self.owner = owner
		self.state = state
		super().__init__(_wrap_value(owner, state, value) for value in values)

	def __setitem__(self, key, value):
		if isinstance(key, slice):
			value = [_wrap_value(self.owner, self.state, item) for item in value]
		elif self[key] is not value:
			value = _wrap_value(self.owner, self.state, value)
		super().__setitem__(key, value)
		self.state.changed = True

	def __delitem__(self, key):
		super().__delitem__(key)
		self.state.changed = True

	def __iadd__(self, values):
		self.extend(values)
		return self

	def __imul__(self, count):
		super().__imul__(count)
		self.state.changed = True
		return self

	def append(self, value, /):
		super().append(_wrap_value(self.owner, self.state, value))
		self.state.changed = True

	def extend(self, values, /):
		wrapped = [_wrap_value(self.owner, self.state, value) for value in values]
		if wrapped:
			super().extend(wrapped)
			self.state.changed = True

	def insert(self, index, value, /):
		super().insert(index, _wrap_value(self.owner, self.state, value))
		self.state.changed = True

	def pop(self, index=-1, /):
		value = super().pop(index)
		self.state.changed = True
		return value

	def remove(self, value, /):
		super().remove(value)
		self.state.changed = True

	def clear(self):
		if self:
			super().clear()
			self.state.changed = True

	def reverse(self):
		super().reverse()
		self.state.changed = True

	def sort(self, *, key=None, reverse=False):
		values = sorted(self, key=key, reverse=reverse)
		super().__setitem__(slice(None), values)
		self.state.changed = True


class _HookedDict(dict):
	def __init__(self, owner, state, /, *args, **kwargs):
		self.owner = owner
		self.state = state
		values = dict(*args, **kwargs)
		super().__init__({key: _wrap_value(owner, state, value) for key, value in values.items()})

	def __setitem__(self, key, value):
		if self.get(key, _MISSING) is not value:
			value = _wrap_value(self.owner, self.state, value)
		super().__setitem__(key, value)
		self.state.changed = True

	def __delitem__(self, key):
		super().__delitem__(key)
		self.state.changed = True

	def __ior__(self, values):
		self.update(values)
		return self

	def pop(self, key, default=_MISSING, /):
		value = super().pop(key, _MISSING)
		if value is _MISSING:
			if default is _MISSING:
				raise KeyError(key)
			return default
		self.state.changed = True
		return value

	def popitem(self):
		item = super().popitem()
		self.state.changed = True
		return item

	def clear(self):
		if self:
			super().clear()
			self.state.changed = True

	def setdefault(self, key, default=None, /):
		value = self.get(key, _MISSING)
		if value is not _MISSING:
			return value
		self[key] = default
		return self[key]

	def update(self, *args, **kwargs):
		values = dict(*args, **kwargs)
		if values:
			wrapped = {key: _wrap_value(self.owner, self.state, value) for key, value in values.items()}
			super().update(wrapped)
			self.state.changed = True


class _PropertyState:
	"""
	PropertyState用来存储改变状态以及属性的真实值
	"""
	def __init__(self, owner, value):
		self.value = _wrap_value(owner, self, value)
		self.changed = False


class Property:
	"""
	属性定义，不负责存储值，类型共享
	"""
	def __init__(self, type=None, default=None, cond=None):
		if type not in ALL_SS_PROPERTY_TYPES:
			raise RuntimeError("Unsupported value type: %r" % (type,))
		self.type = type
		self._codec = type()
		self.default = default
		self.cond = cond

	def __set_name__(self, owner, name):
		self.name = name

	def _get_state(self, instance):
		states = instance.__dict__.get("_ss_property_states")
		if states is None:
			states = instance._ss_property_states = {}
		state = states.get(self.name)
		if state is None:
			state = states[self.name] = _PropertyState(instance, self.default)
		return state

	def __get__(self, instance, owner=None):
		if instance is None:
			return self
		return self._get_state(instance).value

	def __set__(self, instance, value):
		if not self._codec.check(value):
			raise RuntimeError("Property %s value type incompatible: %s, should be %s" %
				(self.name, type(value).__name__, self.type.__name__))
		state = self._get_state(instance)
		if value is state.value:
			return
		state.value = _wrap_value(instance, state, value)
		state.changed = True

	def serialize(self, instance):
		return self._codec.serialize(self._get_state(instance).value)


class PropertyHostMixin:
	_ss_properties = {}

	def __init_subclass__(cls, **kwargs):
		super().__init_subclass__(**kwargs)
		properties = {}
		for base in reversed(cls.__mro__):
			for name, value in vars(base).items():
				if isinstance(value, Property):
					properties[name] = value
				else:
					properties.pop(name, None)
		cls._ss_properties = properties

	def __init__(self):
		# 只有被赋值给property的时候，这些值才会被真正的初始化
		self.owner = None
		self.state = None
		self.parent = None
		self._parent_key = None

		# 记录脏属性，用于打包
		# python3.7之后的dict遍历按照插入顺序遍历
		self._ss_property_dirty = {}
		self._path = None	# path lazy init，用于记录当前对象的路径

	def set_property(self, owner, state, parent, key):
		self.owner = owner
		self.state = state
		self.parent = parent
		self._parent_key = key

	def make_dirty(self, name):
		owner = getattr(self, "owner", None)
		if not owner:
			return
		if owner is self:
			self._ss_property_dirty[(None, name)] = None
		else:
			owner._ss_property_dirty[(id(self), name)] = self

	def get_path(self):
		container = self
		parent = getattr(self, "parent", None)
		path = []
		while parent is not None:
			parent_key = getattr(container, "_parent_key", None)
			if not parent_key:
				raise RuntimeError("Parent key for property %s in %s not found" % (container, parent))
			path.append(parent_key)
			container = parent
			parent = getattr(parent, "parent", None)
		return reversed(path)

	def pack_property(self):
		mailbox = getattr(self, "mailbox", None)
		states = self.__dict__.get("_ss_property_states")
		if mailbox is None or not states:
			return None

		patch = ssproperty_pb2.PropertyPatch(mailbox=mailbox)
		packed_states = []
		for name, prop in self._ss_properties.items():
			state = states.get(name)
			if state is not None and state.changed:
				change = patch.changes.add(value=prop.serialize(self))
				change.path.add(str_key=name)
				packed_states.append(state)

		if not packed_states:
			return None

		data = patch.SerializeToString()
		for state in packed_states:
			state.changed = False
		return data

	def apply_property_changes(self, changes):
		pass


class SyncDict(dict, PropertyHostMixin):
	"""
	同步字典，支持嵌套。支持通过path一次同步某个字段
	"""
	def __init__(self, *args, **kwargs):
		dict.__init__(self, *args, **kwargs)
		PropertyHostMixin.__init__(self)

	def __getattr__(self, key):
		return self[key]

	def __setattr__(self, key, value):
		if key in self:
			self[key] = value
		dict.__setattr__(self, key, value)

	def __getitem__(self, key):
		if key in self._ss_properties:
			return self._ss_properties[key]._get_state(self).value
		return dict.__getitem__(self, key)

	def __setitem__(self, key, value):
		if key in self._ss_properties:
			self._ss_properties[key].__set__(self, value)
		dict.__setitem__(self, key, value)


class SyncList(PropertyHostMixin):
	"""
	同步列表，支持嵌套。支持通过path一次同步某个字段
	"""


ALL_SS_PROPERTY_TYPES = ALL_TYPES.union({SyncDict, SyncList})