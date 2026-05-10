from __future__ import annotations

from math import sqrt
from typing import TypeAlias

Number: TypeAlias = int | float

class Vector:
    __slots__ = ("x", "y")
    def __init__(
        self,
        x: Number | None = None,
        y: Number | None = None
    ) -> None:
        self.x = float(x) if x is not None else 0.0
        self.y = float(y) if y is not None else 0.0

    def __sub__(
        self,
        other: Vector
    ) -> Vector:
        return Vector(self.x - other.x, self.y - other.y)

    def __add__(
        self,
        other: Vector
    ) -> Vector:
        return Vector(self.x + other.x, self.y + other.y)

    def __iadd__(
        self,
        other: Vector
    ) -> Vector:
        self.x += other.x
        self.y += other.y
        return self

    def __mul__(
        self,
        scalar: Number
    ) -> Vector:
        return Vector(self.x * scalar, self.y * scalar)

    def __truediv__(
        self,
        scalar: Number
    ) -> Vector:
        return Vector(self.x / scalar, self.y / scalar)

# For debugging
    def __repr__(
        self
    ) -> str:
        #:.2f means it is convertig it to a floating point number and rounding to 2dp
        return f"({self.x:.2f}, {self.y:.2f})"

    def copy(
        self
    ) -> Vector:
        return Vector(self.x, self.y)

    def component_min(
        self,
        other: Vector
    ) -> Vector:
        return Vector(min(self.x, other.x), min(self.y, other.y))

    def component_max(
        self,
        other: Vector
    ) -> Vector:
        return Vector(max(self.x, other.x), max(self.y, other.y))

    def component_min_ip(
        self,
        other: Vector
    ) -> Vector:
        self.x = min(self.x, other.x)
        self.y = min(self.y, other.y)
        return self

    def component_max_ip(
        self,
        other: Vector
    ) -> Vector:
        self.x = max(self.x, other.x)
        self.y = max(self.y, other.y)
        return self

    def dot(
        self,
        other: Vector
    ) -> float:
        return self.x * other.x + self.y * other.y

    def cross(
        self,
        other: Vector
    ) -> float:
        # 2D vector cross product returns scalar z-component
        return self.x * other.y - self.y * other.x

    def mag(
        self
    ) -> float:
        return sqrt(self.x * self.x + self.y * self.y)

    def mag2(
        self
    ) -> float:
        return self.x * self.x + self.y * self.y

    def perp(
        self
    ) -> Vector:
        return Vector(-self.y, self.x)

    def rotated_by(
        self,
        sin_a: float,
        cos_a: float
    ) -> Vector:
        return Vector(self.x * cos_a - self.y * sin_a, self.x * sin_a + self.y * cos_a)