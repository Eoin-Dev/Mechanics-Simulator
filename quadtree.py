import pygame

from physics.bodies import Particle
from physics.constants import (
    QUADTREE_DEBUG_COLOUR,
    QUADTREE_DEBUG_THICKNESS,
    QUADTREE_DEFAULT_CAPACITY,
    QUADTREE_DEFAULT_MAX_DEPTH
)
from physics.vector import Vector

from utils.coord_conversion import to_pygame

# Helper class for qaudtree bounds and intersection checks
class Rect:
    __slots__ = ("min", "max")

    def __init__(
        self,
        min_corner: Vector,
        max_corner: Vector
    ) -> None:
        self.min = min_corner.component_min(max_corner)
        self.max = min_corner.component_max(max_corner)

    # Check if rect fully contains a circle
    def contains_circle(
        self,
        center: Vector,
        radius: float
    ) -> bool:
        return (
            (center.x - radius) >= self.min.x and
            (center.x + radius) <= self.max.x and
            (center.y - radius) >= self.min.y and
            (center.y + radius) <= self.max.y
        )

    # Check if rect intersects another rect
    def intersects_rect(
        self,
        other: 'Rect'
    ) -> bool:
        return not (other.min.x > self.max.x or other.max.x < self.min.x or other.min.y > self.max.y or other.max.y < self.min.y)

    # Check if rect intersects with a circle
    def intersects_circle(
        self,
        center: Vector,
        radius: float
    ) -> bool:
        closest_point = center.component_max(self.min).component_min(self.max)
        delta = center - closest_point
        return delta.mag2() <= radius*radius

class QuadtreeNode:
    __slots__ = (
        "__bounds",
        "__capacity",
        "__depth",
        "__max_depth",
        "__particles",
        "__children"
    )

    def __init__(
        self,
        bounds: Rect,
        capacity: int = QUADTREE_DEFAULT_CAPACITY,
        depth: int = 0,
        max_depth: int = QUADTREE_DEFAULT_MAX_DEPTH
    ) -> None:
        self.__bounds: Rect = bounds
        self.__capacity: int = capacity
        self.__depth: int = depth
        self.__max_depth: int = max_depth

        self.__particles: list[Particle] = []
        self.__children: tuple["QuadtreeNode", "QuadtreeNode", "QuadtreeNode", "QuadtreeNode"] | None = None

    # Adds 4 children to current node, dividing the space
    def __subdivide(
        self
    ) -> None:
        mx = (self.__bounds.min.x + self.__bounds.max.x) / 2
        my = (self.__bounds.min.y + self.__bounds.max.y) / 2

        top_left = Rect(Vector(self.__bounds.min.x, my), Vector(mx, self.__bounds.max.y))
        top_right = Rect(Vector(mx, my), Vector(self.__bounds.max.x, self.__bounds.max.y))
        bottom_left = Rect(Vector(self.__bounds.min.x, self.__bounds.min.y), Vector(mx, my))
        bottom_right = Rect(Vector(mx, self.__bounds.min.y), Vector(self.__bounds.max.x, my))

        self.__children = (
            QuadtreeNode(top_left, self.__capacity, self.__depth+1, self.__max_depth),
            QuadtreeNode(top_right, self.__capacity, self.__depth+1, self.__max_depth),
            QuadtreeNode(bottom_left, self.__capacity, self.__depth+1, self.__max_depth),
            QuadtreeNode(bottom_right, self.__capacity, self.__depth+1, self.__max_depth)
        )

    # Creates the quadtree by inserting particles one by one, creates child nodes as needed, which subdivides recursesively until max depth or capacity is reached
    # Particles on boundary between nodes are kept in the parent node to avoid duplicates
    def insert(
        self,
        p: Particle
    ) -> bool:
        center = p.position
        radius = p.radius

        # If particle doesn't intersect this node, skip
        if not self.__bounds.intersects_circle(center, radius):
            return False

        # If node is a leaf
        if self.__children is None:
            self.__particles.append(p)
            if len(self.__particles) > self.__capacity and self.__depth < self.__max_depth:
                self.__subdivide()
                old = self.__particles
                self.__particles = []
                for op in old:
                    # Try to push into newly created children children fully contain the circle, this loop is where the recursion ahppens
                    pushed = False
                    for c in self.__children:
                        if c.__bounds.contains_circle(op.position, op.radius):
                            c.insert(op)
                            pushed = True
                            break
                    if not pushed:
                        self.__particles.append(op)
            return True

        for c in self.__children:
            if c.__bounds.contains_circle(center, radius):
                return c.insert(p)

        # Otherwise keep particle here in parent node
        self.__particles.append(p)
        return True

    # Recursively queries the quadtree and adds particles within the rangeRect to found list and returns this list, which can be used for collision checking
    def query(
        self,
        range_rect: Rect,
        found: list[Particle] | None = None
    ) -> list[Particle]:
        if found is None:
            found = []

        if not self.__bounds.intersects_rect(range_rect):
            return found

        # Check particles stored at this node
        for p in self.__particles:
            if range_rect.intersects_circle(p.position, p.radius):
                found.append(p)

        # Recursivley queries children
        if self.__children is not None:
            for c in self.__children:
                c.query(range_rect, found)
        return found

    # Recursively gets the Rect bounds of this node and all child nodes, used to draw quadtree for debugging
    def get_all_bounds(
        self,
        out: list[Rect] | None = None
    ) -> list[Rect]:
        if out is None:
            out = []
        out.append(self.__bounds)
        if self.__children is not None:
            for c in self.__children:
                c.get_all_bounds(out)
        return out

class Quadtree:
    __slots__ = "__root"

    def __init__(
        self,
        bounds: Rect,
        capacity: int = QUADTREE_DEFAULT_CAPACITY,
        max_depth: int = QUADTREE_DEFAULT_MAX_DEPTH
    ) -> None:
        self.__root: QuadtreeNode = QuadtreeNode(bounds, capacity, 0, max_depth)

    # Creates the quadtree from a list of partices by calling a recursive method
    def __insert(
        self,
        p: Particle
    ) -> bool:
        return self.__root.insert(p)

    # Sequentailly adds particles to the quadtree
    def build_from(
        self,
        particles: list[Particle]
    ) -> None:
        for p in particles:
            self.__insert(p)

    def query(
        self,
        range_rect: Rect
    ) -> list[Particle]:
        return self.__root.query(range_rect)

    def get_all_bounds(
        self
    ) -> list[Rect]:
        return self.__root.get_all_bounds()

def draw_quadtree_bounds(
    screen: pygame.Surface,
    qt: Quadtree | None,
    screen_w: float,
    screen_h: float,
    zoom: float,
    colour: tuple[int, int, int] = QUADTREE_DEBUG_COLOUR,
    thickness: int = QUADTREE_DEBUG_THICKNESS
) -> None:
    if qt is None:
        return

    for rect in qt.get_all_bounds():
        p1 = to_pygame(rect.min, screen_w, screen_h, zoom)
        p2 = to_pygame(rect.max, screen_w, screen_h, zoom)

        left = int(min(p1[0], p2[0]))
        top = int(min(p1[1], p2[1]))
        width = int(abs(p2[0] - p1[0]))
        height = int(abs(p2[1] - p1[1]))

        pygame.draw.rect(screen, colour, (left, top, width, height), thickness)
