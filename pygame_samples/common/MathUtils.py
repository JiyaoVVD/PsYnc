# -*- coding: utf-8 -*-
import math

PI = 3.141592653589793


def deg2rad(deg):
	return deg * PI / 180

def rad2deg(rad):
	return rad * 180 / PI


class Vector2(object):
	def __init__(self, x=0, y=0):
		self.x = x
		self.y = y

	def __add__(self, other):
		return Vector2(self.x + other.x, self.y + other.y)

	def __sub__(self, other):
		return Vector2(self.x - other.x, self.y - other.y)

	def __mul__(self, other):
		return Vector2(self.x * other, self.y * other)

	def __div__(self, other):
		return Vector2(self.x / other, self.y / other)

	def __truediv__(self, other):
		return Vector2(self.x / other, self.y / other)

	def __neg__(self):
		return Vector2(-self.x, -self.y)

	def __eq__(self, other):
		return self.x == other.x and self.y == other.y

	def __ne__(self, other):
		return self.x != other.x or self.y != other.y

	def __str__(self):
		return "Vector2(%s, %s)" % (self.x, self.y)

	def __repr__(self):
		return "Vector2(%s, %s)" % (self.x, self.y)

	def length(self):
		return (self.x ** 2 + self.y ** 2) ** 0.5

	def normalize(self):
		length = self.length()
		if length == 0:
			return Vector2(0, 0)
		return Vector2(self.x / length, self.y / length)

	def dot(self, other):
		return self.x * other.x + self.y * other.y

	def cross(self, other):
		return self.x * other.y - self.y * other.x

	def angle_rad(self, other):
		return math.acos(self.dot(other) / (self.length() * other.length()))

	def angle_deg(self, other):
		return rad2deg(self.angle_rad(other))

	def rotate(self, angle):
		return Vector2(
			self.x * math.cos(angle) - self.y * math.sin(angle),
			self.x * math.sin(angle) + self.y * math.cos(angle))

	def rotate_deg(self, angle):
		return self.rotate(deg2rad(angle))

	def rotate_rad(self, angle):
		return self.rotate(angle)

	def project(self, other):
		return other * self.dot(other) / other.length() ** 2
