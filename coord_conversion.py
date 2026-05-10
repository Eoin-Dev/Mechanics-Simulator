from __future__ import annotations

from typing import TypeAlias

from physics.vector import Vector

Number: TypeAlias = int | float
Point: TypeAlias = tuple[Number, Number]

# takes a list/tuple of pygame coordinates and returns a Vector in cartesian space
def to_cartesian(
    pos: Point,
    screen_w: Number,
    screen_h: Number,
    zoom: Number
) -> Vector:
    return Vector((pos[0] - screen_w/2)/zoom, (-pos[1] + screen_h/2)/zoom)

# takes a Vector in cartesian space and returns a tuple of pygame coordinates
def to_pygame(
    pos: Vector,
    screen_w: Number,
    screen_h: Number,
    zoom: Number
) -> tuple[float, float]:
    return (pos.x)*zoom + screen_w/2, -(pos.y)*zoom + screen_h/2