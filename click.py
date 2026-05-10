from __future__ import annotations

from typing import TypeAlias

from physics.vector import Vector
from utils.coord_conversion import to_pygame

Number: TypeAlias = int | float
MousePos: TypeAlias = tuple[int, int]

def check_click_on_rectangle(
    p1: Vector,
    p2: Vector,
    thickness: Number,
    mouse_pos: MousePos,
    screen_w: Number,
    screen_h: Number,
    zoom: Number
) -> bool:
    mouse = Vector(mouse_pos[0], mouse_pos[1])

    start_on_screen = Vector(*to_pygame(p1, screen_w, screen_h, zoom))
    end_on_screen   = Vector(*to_pygame(p2,   screen_w, screen_h, zoom))

    segment = end_on_screen - start_on_screen
    start_to_mouse = mouse - start_on_screen

    segment_length_sq = segment.mag2()
    if segment_length_sq == 0:
        return False

    # Projection factor
    t = start_to_mouse.dot(segment) / segment_length_sq

    # Reject if mouse is beyond the endpoints
    if t < 0 or t > 1:
        return False

    # Closest point on the segment
    closest = start_on_screen + segment * t

    # Perpendicular distance
    distance = (mouse - closest).mag()

    click_radius = thickness/1.7 * zoom

    return distance <= click_radius

def check_click_on_circle(
    center: Vector,
    radius: Number,
    mouse_pos: Vector
) -> bool:
    mouse_to_centre = mouse_pos - center
    return mouse_to_centre.mag2() <= radius**2