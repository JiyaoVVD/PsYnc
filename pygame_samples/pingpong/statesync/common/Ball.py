# -*- coding: utf-8 -*-

import pygame

from net.rpc.RpcEntity import RpcCallableMixin, RpcMethod

class SSProperty:
	def __init__(self, type=None, default=None, cond=None):
		self.type = type
		self.default = default
		self.cond = cond

	def __get__(self, instance, owner):
		return self


class SyncCond:
	NONE = 0
	OWNER_ONLY = 1
	OWNER_EXCEPT = 2
	ALL = 3


class Ball(RpcCallableMixin):

	x = SSProperty(
		type = int,
		default = 0,
		cond = SyncCond.NONE
	)
	y = SSProperty(
		type = int,
		default = 0,
		cond = SyncCond.NONE,
	)
	vx = SSProperty(
		type = int,
		default = 0,
		cond = SyncCond.NONE,
	)
	vy = SSProperty(
		type = int,
		default = 0,
		cond = SyncCond.NONE,
	)

	def tick(self, delta_time):
		self.x += self.vx * delta_time
		self.y += self.vy * delta_time
