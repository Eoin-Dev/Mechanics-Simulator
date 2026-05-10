from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeAlias

from physics.constants import (
    COLLISION_MODE_BRUTE_FORCE,
    COLLISION_MODE_QUADTREE,
    QUADTREE_PAD_EPSILON,
)
from physics.quadtree import Quadtree, Rect
from physics.vector import Vector

if TYPE_CHECKING:
    from physics.bodies import Particle, SimDynamicBody

DynamicBodyCollection: TypeAlias = list["SimDynamicBody"]
ParticleCollection: TypeAlias = list["Particle"]

class CollisionStrategy(ABC):
    __slots__ = ()

    @abstractmethod
    def get_name(
        self
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def resolve_particle_collisions(
        self,
        dynamic_bodies: DynamicBodyCollection,
        restitution: float
    ) -> Quadtree | None:
        raise NotImplementedError

class QuadtreeCollisionStrategy(CollisionStrategy):
    __slots__ = ()

    def get_name(
        self
    ) -> str:
        return COLLISION_MODE_QUADTREE

    # Creates a quadtree every frame, and queries it with search radius around the particle being checked, reducing no of chekcs, only for particle particle collisions
    def resolve_particle_collisions(
        self,
        dynamic_bodies: DynamicBodyCollection,
        restitution: float
    ) -> Quadtree | None:
        particles: ParticleCollection = []
        for body in dynamic_bodies:
            for particle in body.particles:
                particles.append(particle)

        if not particles:
            return None

        first_particle = particles[0]
        min_corner = first_particle.position.copy()
        max_corner = first_particle.position.copy()
        max_radius = first_particle.radius

        for particle in particles[1:]:
            position = particle.position
            radius = particle.radius

            min_corner.component_min_ip(position)
            max_corner.component_max_ip(position)
            if radius > max_radius:
                max_radius = radius

        pad = max_radius + QUADTREE_PAD_EPSILON
        bounds = Rect(
            min_corner - Vector(pad, pad),
            max_corner + Vector(pad, pad)
        )

        quadtree = Quadtree(bounds)
        quadtree.build_from(particles)

        for particle in particles:
            search_radius = particle.radius + QUADTREE_PAD_EPSILON
            search_offset = Vector(search_radius, search_radius)
            query_rect = Rect(
                particle.position - search_offset,
                particle.position + search_offset
            )
            candidates = quadtree.query(query_rect)
            for candidate in candidates:
                if candidate is particle:
                    continue
                if candidate.id <= particle.id:
                    continue
                if particle.sibling is candidate or candidate.sibling is particle:
                    continue
                if particle.collided_with(candidate):
                    particle.handle_collision(
                        particle.sibling,
                        candidate,
                        candidate.sibling,
                        restitution
                    )

        return quadtree

class BruteForceCollisionStrategy(CollisionStrategy):
    __slots__ = ()

    def get_name(
        self
    ) -> str:
        return COLLISION_MODE_BRUTE_FORCE

    # Checks collisions between every particle, particle -particle collisions only
    def resolve_particle_collisions(
        self,
        dynamic_bodies: DynamicBodyCollection,
        restitution: float
    ) -> Quadtree | None:
        for i, body_a in enumerate(dynamic_bodies):
            for particle in body_a.particles:
                for body_b in dynamic_bodies[i + 1 :]:
                    for candidate in body_b.particles:
                        if particle.collided_with(candidate):
                            particle.handle_collision(
                                particle.sibling,
                                candidate,
                                candidate.sibling,
                                restitution
                            )
        return None