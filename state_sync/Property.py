# -*- coding: utf-8 -*-
from net.protos import ssproperty_pb2
from net.protocol.Types import ALL_TYPES, Int, serialize_by_type

class SyncCond:
	NONE = 0
	OWNER_ONLY = 1
	OWNER_EXCEPT = 2
	ALL = 3


_MISSING = object()


def _wrap_value(owner, name, value):
	if isinstance(value, list) and not isinstance(value, SyncList):
		return _HookedList(owner, name, value)
	if isinstance(value, dict) and not isinstance(value, SyncDict):
		return _HookedDict(owner, name, value)
	return value


class _HookedList(list):
	def __init__(self, owner, name, values=(), /):
		self.owner = owner
		self.name = name
		super().__init__(_wrap_value(owner, name, value) for value in values)

	def __setitem__(self, key, value):
		if isinstance(key, slice):
			value = [_wrap_value(self.owner, self.name, item) for item in value]
		elif self[key] is not value:
			value = _wrap_value(self.owner, self.name, value)
		super().__setitem__(key, value)
		self.owner._make_dirty(self.name)

	def __delitem__(self, key):
		super().__delitem__(key)
		self.owner._make_dirty(self.name)

	def __iadd__(self, values):
		self.extend(values)
		return self

	def __imul__(self, count):
		super().__imul__(count)
		self.owner._make_dirty(self.name)
		return self

	def append(self, value, /):
		super().append(_wrap_value(self.owner, self.name, value))
		self.owner._make_dirty(self.name)

	def extend(self, values, /):
		wrapped = [_wrap_value(self.owner, self.name, value) for value in values]
		if wrapped:
			super().extend(wrapped)
			self.owner._make_dirty(self.name)

	def insert(self, index, value, /):
		super().insert(index, _wrap_value(self.owner, self.name, value))
		self.owner._make_dirty(self.name)

	def pop(self, index=-1, /):
		value = super().pop(index)
		self.owner._make_dirty(self.name)
		return value

	def remove(self, value, /):
		super().remove(value)
		self.owner._make_dirty(self.name)

	def clear(self):
		if self:
			super().clear()
			self.owner._make_dirty(self.name)

	def reverse(self):
		super().reverse()
		self.owner._make_dirty(self.name)

	def sort(self, *, key=None, reverse=False):
		values = sorted(self, key=key, reverse=reverse)
		super().__setitem__(slice(None), values)
		self.owner._make_dirty(self.name)


class _HookedDict(dict):
	def __init__(self, owner, name, /, *args, **kwargs):
		self.owner = owner
		self.name = name
		values = dict(*args, **kwargs)
		super().__init__({key: _wrap_value(self.owner, self.name, value) for key, value in values.items()})

	def __setitem__(self, key, value):
		if self.get(key, _MISSING) is not value:
			value = _wrap_value(self.owner, self.name, value)
		super().__setitem__(key, value)
		self.owner._make_dirty(self.name)

	def __delitem__(self, key):
		super().__delitem__(key)
		self.owner._make_dirty(self.name)

	def __ior__(self, values):
		self.update(values)
		return self

	def pop(self, key, default=_MISSING, /):
		value = super().pop(key, _MISSING)
		if value is _MISSING:
			if default is _MISSING:
				raise KeyError(key)
			return default
		self.owner._make_dirty(self.name)
		return value

	def popitem(self):
		item = super().popitem()
		self.owner._make_dirty(self.name)
		return item

	def clear(self):
		if self:
			super().clear()
			self.owner._make_dirty(self.name)

	def setdefault(self, key, default=None, /):
		value = self.get(key, _MISSING)
		if value is not _MISSING:
			return value
		self[key] = default
		return self[key]

	def update(self, *args, **kwargs):
		values = dict(*args, **kwargs)
		if values:
			wrapped = {key: _wrap_value(self.owner, self.name, value) for key, value in values.items()}
			super().update(wrapped)
			self.owner._make_dirty(self.name)


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

	def _get_value(self, instance):
		if "_ss_property_values" not in instance.__dict__:
			instance._ss_property_values = {}
		return instance._ss_property_values.get(self.name, self.default)

	def _set_value(self, instance, value):
		if "_ss_property_values" not in instance.__dict__:
			instance._ss_property_values = {}
		value = _wrap_value(instance, self.name, value)
		value = instance._preprocess_property(value)
		instance._ss_property_values[self.name] = value

	def __get__(self, instance, owner=None):
		if instance is None:
			return self
		return self._get_value(instance)

	def __set__(self, instance, value):
		if not self._codec.check(value):
			raise RuntimeError("Property %s value type incompatible: %s, should be %s" %
				(self.name, type(value).__name__, self.type.__name__))
		old_value = self._get_value(instance)
		if value is old_value:
			return
		self._set_value(instance, value)
		instance._make_dirty(self.name)

	def serialize(self, instance):
		return self._codec.serialize(self._get_value(instance))


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
		self.owner = self
		self.parent = None
		self._parent_key = None

		# 记录脏属性，用于打包
		# python3.7之后的dict遍历按照插入顺序遍历
		self._ss_property_dirty = {}
		self._path = None	# path lazy init，用于记录当前对象的路径

	def _preprocess_property(self, value):
		return value

	def _set_property(self, owner, parent, key):
		self.owner = owner
		self.parent = parent
		self._parent_key = key
		# 重新被设置为属性时需要清空path缓存
		self._path = None

	def _make_dirty(self, name):
		owner = getattr(self, "owner", None)
		if owner is self:
			key = (None, name)
			value = None
		else:
			key = (id(self), name)
			value = self
		if key in owner._ss_property_dirty:
			# 重复设置时先删再加，保证属性修改的迭代顺序
			owner._ss_property_dirty.pop(key)
		owner._ss_property_dirty[key] = value

	def _get_path_as_property(self):
		if self._path is not None:
			return self._path
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
		self._path = path = list(reversed(path))
		return path

	def pack_property(self):
		mailbox = getattr(self, "mailbox", 0)

		patch = ssproperty_pb2.PropertyPatch(mailbox=mailbox)
		if not self._ss_property_dirty:
			return None
		for key, ref in self._ss_property_dirty.items():
			prop_id, name = key
			if prop_id is None:
				prop = self._ss_properties[name]
				change = patch.changes.add(value=prop.serialize(self))
				change.path.add(str_key=name)
			else:
				path = ref._get_path_as_property()
				change = patch.changes.add(value=serialize_by_type(ref[name]))
				for key in path + [name]:
					key_type = type(key)
					if key_type is str:
						change.path.add(str_key=key)
					elif key_type is int:
						change.path.add(int_key=key)
					elif key_type is bool:
						change.path.add(bool_key=key)
					else:
						raise RuntimeError("Unsupported key type: %s" % key_type.__name__)
		self._ss_property_dirty.clear()
		data = patch.SerializeToString()
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
			return self._ss_properties[key]._get_value(self)
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


if __name__ == "__main__":
	class TestEntity(PropertyHostMixin):
		a = Property(
			type = Int,
			default = 1,
			cond = SyncCond.ALL,
		)

	e = TestEntity()

	e.a = 3
	print(e.pack_property())