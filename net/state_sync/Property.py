# -*- coding: utf-8 -*-
from net.protos import ssproperty_pb2

class SyncCond:
	NONE = 0
	OWNER_ONLY = 1
	OWNER_EXCEPT = 2
	ALL = 3


class Property(object):

	def __init__(self, type=None, default=None, cond=None):
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
		if self.value != value:
			self.changed = True
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
		

