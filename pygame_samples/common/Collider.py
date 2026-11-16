# -*- coding: utf-8 -*-
"""
简单的碰撞体和全局碰撞管理
"""
from itertools import combinations

from pygame_samples.common.MathUtils import Vector2


class Shape:
	CIRCLE = 1
	AABB = 2

	SHAPE_CLASSES = {}

	@classmethod
	def shape_class(cls, shape):
		def _wrapper(shape_class):
			shape_class.shape = shape
			cls.SHAPE_CLASSES[shape] = shape_class
			return shape_class
		return _wrapper


class ShapeBase(object):

	def check(self, self_pos, other_pos, other_shape):
		"""有重叠时返回 (接触点, 自身分离单位法向, 对方分离单位法向)。

		圆以圆心定位，AABB 以最小坐标点定位。分离或恰好相切时返回 None。
		"""
		collide = _COLLISION_CHECKS[self.shape, other_shape.shape]
		return collide(self, self_pos, other_pos, other_shape)


def circle_with_aabb(circle_pos, radius, aabb_min, aabb_max):
	point = Vector2(
		max(aabb_min.x, min(circle_pos.x, aabb_max.x)),
		max(aabb_min.y, min(circle_pos.y, aabb_max.y)),
	)
	offset = circle_pos - point
	distance_squared = offset.dot(offset)
	if distance_squared >= radius * radius:
		return None
	if distance_squared > 0:
		normal = offset / (distance_squared ** 0.5)
		return point, normal, -normal

	# 圆心在框内或边上时，沿最近的面把圆移出。
	distance, normal = min((
		(circle_pos.x - aabb_min.x, Vector2(-1, 0)),
		(aabb_max.x - circle_pos.x, Vector2(1, 0)),
		(circle_pos.y - aabb_min.y, Vector2(0, -1)),
		(aabb_max.y - circle_pos.y, Vector2(0, 1)),
	), key=lambda face: face[0])
	point = circle_pos + normal * distance
	return point, normal, -normal


@Shape.shape_class(Shape.CIRCLE)
class Circle(ShapeBase):

	def __init__(self, radius=1):
		if radius <= 0:
			raise ValueError("Circle radius must be positive")
		self.radius = radius

	def collide_with_circle(self, self_pos: Vector2, other_pos: Vector2, other_shape: ShapeBase):
		offset = other_pos - self_pos
		distance_squared = offset.dot(offset)
		radius_sum = self.radius + other_shape.radius
		if distance_squared >= radius_sum * radius_sum:
			return None

		distance = distance_squared ** 0.5
		axis = offset / distance if distance else Vector2(1, 0)
		# 取圆心连线上重叠区间的中点，包含关系下也落在两个圆内。
		overlap_min = max(-self.radius, distance - other_shape.radius)
		overlap_max = min(self.radius, distance + other_shape.radius)
		point = self_pos + axis * ((overlap_min + overlap_max) / 2)
		return point, -axis, axis

	def collide_with_aabb(self, self_pos: Vector2, other_pos: Vector2, other_shape: ShapeBase):
		other_max = other_pos + Vector2(other_shape.width, other_shape.height)
		return circle_with_aabb(self_pos, self.radius, other_pos, other_max)


@Shape.shape_class(Shape.AABB)
class AABB(ShapeBase):

	def __init__(self, width=1, height=1):
		if width <= 0 or height <= 0:
			raise ValueError("AABB width and height must be positive")
		self.width = width
		self.height = height

	def collide_with_aabb(self, self_pos: Vector2, other_pos: Vector2, other_shape: ShapeBase):
		self_max = self_pos + Vector2(self.width, self.height)
		other_max = other_pos + Vector2(other_shape.width, other_shape.height)
		left = self_max.x - other_pos.x
		right = other_max.x - self_pos.x
		up = self_max.y - other_pos.y
		down = other_max.y - self_pos.y
		distance_x = min(left, right)
		distance_y = min(up, down)
		if distance_x <= 0 or distance_y <= 0:
			return None

		# 比较移出所需的距离，重叠区间长度在包含关系下不足以选轴。
		if distance_x <= distance_y:
			normal = Vector2(-1 if left <= right else 1, 0)
		else:
			normal = Vector2(0, -1 if up <= down else 1)
		point = Vector2(
			(max(self_pos.x, other_pos.x) + min(self_max.x, other_max.x)) / 2,
			(max(self_pos.y, other_pos.y) + min(self_max.y, other_max.y)) / 2,
		)
		return point, normal, -normal

	def collide_with_circle(self, self_pos: Vector2, other_pos: Vector2, other_shape: ShapeBase):
		collision = other_shape.collide_with_aabb(other_pos, self_pos, self)
		if collision is None:
			return None
		point, circle_normal, aabb_normal = collision
		return point, aabb_normal, circle_normal


_COLLISION_CHECKS = {
	(Shape.CIRCLE, Shape.CIRCLE): Circle.collide_with_circle,
	(Shape.CIRCLE, Shape.AABB): Circle.collide_with_aabb,
	(Shape.AABB, Shape.CIRCLE): AABB.collide_with_circle,
	(Shape.AABB, Shape.AABB): AABB.collide_with_aabb,
}


class CollisionBody(object):
	def __init__(self, pos, shape, **kwargs):
		self.pos = pos
		self.shape = Shape.SHAPE_CLASSES[shape](**kwargs)

		self.on_collide_cbs = []

	def register_on_collide(self, callback):
		"""注册 callback(other_body, point, normal)，法向用于分离当前物体。"""
		if callback not in self.on_collide_cbs:
			self.on_collide_cbs.append(callback)

	def unregister_on_collide(self, callback):
		if callback in self.on_collide_cbs:
			self.on_collide_cbs.remove(callback)


class PhysicsManager(object):
	def __init__(self):
		self.bodies = {}

	def add_body(self, body: CollisionBody):
		self.bodies[body] = None

	def remove_body(self, body: CollisionBody):
		self.bodies.pop(body, None)

	def check_collision(self):
		# 只枚举本轮开始时已有的物体，回调移除的物体跳过后续检测。
		for body1, body2 in combinations(self.bodies, 2):
			if body1 not in self.bodies or body2 not in self.bodies:
				continue
			collision = body1.shape.check(body1.pos, body2.pos, body2.shape)
			if collision is None:
				continue
			point, normal1, normal2 = collision
			callbacks1 = tuple(body1.on_collide_cbs)
			callbacks2 = tuple(body2.on_collide_cbs)
			for cb in callbacks1:
				cb(body2, point, normal1)
			for cb in callbacks2:
				cb(body1, point, normal2)

	def update(self):
		self.check_collision()
