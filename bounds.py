from physics.vector import Vector

def point_outside_bounds(
    position: Vector,
    max_x: float,
    max_y: float
) -> bool:
    return (
        position.x < -max_x
        or position.x > max_x
        or position.y < -max_y
        or position.y > max_y
    )

def circle_outside_bounds(
    position: Vector,
    radius: float,
    max_x: float,
    max_y: float
) -> bool:
    return (
        position.x + radius < -max_x
        or position.x - radius > max_x
        or position.y + radius < -max_y
        or position.y - radius > max_y
    )