from __future__ import annotations
from typing import TYPE_CHECKING, TypeAlias

from physics.collision_strategies import (
    BruteForceCollisionStrategy,
    CollisionStrategy,
    QuadtreeCollisionStrategy
)
from physics.quadtree import Quadtree
from physics.constants import (
    DEFAULT_COLLISION_MODE,
    DEFAULT_GRAVITY,
    DEFAULT_RESTITUTION
)

if TYPE_CHECKING:
    import pygame
    from physics.bodies import Particle, Plane, Rod, SimDynamicBody, SimStaticBody

Bounds: TypeAlias = tuple[float, float]
DynamicBodyCollection: TypeAlias = list["SimDynamicBody"]
StaticBodyCollection: TypeAlias = list["SimStaticBody"]

class World:
    __slots__ = [
        "dynamic_bodies",
        "static_bodies",
        "g",
        "e",
        "last_quadtree",
        "__collision_strategy",
        "__collision_strategy_by_mode"
    ]

    def __init__(
        self
    ) -> None:
        self.dynamic_bodies: DynamicBodyCollection = []
        self.static_bodies: StaticBodyCollection = []
        self.g: float = DEFAULT_GRAVITY
        self.e: float = DEFAULT_RESTITUTION

        quadtree_strategy = QuadtreeCollisionStrategy()
        brute_force_strategy = BruteForceCollisionStrategy()

        self.__collision_strategy_by_mode: dict[str, CollisionStrategy] = {
            quadtree_strategy.get_name(): quadtree_strategy,
            brute_force_strategy.get_name(): brute_force_strategy
        }
        self.__collision_strategy: CollisionStrategy = self.__create_collision_strategy(DEFAULT_COLLISION_MODE)
        
        self.last_quadtree: Quadtree | None = None

    def get_collision_mode(
        self
    ) -> str:
        return self.__collision_strategy.get_name()

    def __create_collision_strategy(
        self,
        mode: str
    ) -> CollisionStrategy:
        strategy = self.__collision_strategy_by_mode.get(mode)
        if strategy is None:
            raise ValueError(f"Unsupported collision type: {mode}")
        return strategy

    def toggle_collision_mode(
        self
    ) -> None:
        mode_order = tuple(self.__collision_strategy_by_mode.keys())
        if not mode_order:
            raise ValueError("No collision strategies configured.")

        current_mode = self.__collision_strategy.get_name()
        try:
            current_index = mode_order.index(current_mode)
        except ValueError:
            self.__collision_strategy = self.__collision_strategy_by_mode[mode_order[0]]
            return

        next_mode = mode_order[(current_index + 1) % len(mode_order)]
        self.__collision_strategy = self.__collision_strategy_by_mode[next_mode]

    def get_next_frame(
        self,
        dt: float
    ) -> None:
        for body in self.dynamic_bodies:
            body.update(dt, self.g)
        
        self.__handle_collisions()

    def delete_and_draw(
        self,
        screen: "pygame.Surface",
        screen_w: float,
        screen_h: float,
        bounds: Bounds,
        zoom: float,
        selected_pa: "Particle | None",
        selected_pl: "Plane | None",
        selected_r: "Rod | None"
    ) -> None:
        for body_type in (self.static_bodies, self.dynamic_bodies):
            for i in range(len(body_type) - 1, -1, -1):
                body = body_type[i]
                is_retained = (
                    body is selected_pa
                    or body is selected_pl
                    or body is selected_r
                )
                if body.outside_bounds(*bounds) and not is_retained:
                    del body_type[i]
                else:
                    body.draw(screen, screen_w, screen_h, zoom)

    def __handle_collisions(
        self
    ) -> None:
        self.last_quadtree = self.__collision_strategy.resolve_particle_collisions(
            self.dynamic_bodies,
            self.e
        )
    
        # Static body collisions
        for plane in self.static_bodies:
            for body in self.dynamic_bodies:
                for p in body.particles:
                    collision, dist2, closest_point = plane.collided_with(p)
                    if collision:
                        plane.handle_collision(p, p.sibling, dist2, closest_point)

    def reset_all_force_flags(
        self
    ) -> None:
        for body in self.dynamic_bodies:
            for particle in body.particles:
                particle.forces_changed = True