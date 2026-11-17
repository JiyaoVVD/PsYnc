# -*- coding: utf-8 -*-

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
			owner._ss_properties = {}
		owner._ss_properties[name] = self

	def __get__(self, instance, owner):
		return self.value

	def __set__(self, instance, value):
		if self.value != value:
			self.changed = True
		self.value = value

