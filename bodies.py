from math import sin, cos # used in the rod class
import pygame 
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from physics.vector import Vector
from physics.constants import (
    DEFAULT_RESTITUTION,
    MIN_DRAW_RADIUS_PX,
    MIN_DRAW_THICKNESS_PX,
    MMOI_ZERO_NUDGE,
    OVERLAP_CORRECTION_PERCENT,
    OVERLAP_CORRECTION_THRESHOLD,
    PARTICLE_RESTING_SPEED_THRESHOLD,
    PLANE_DEFAULT_THICKNESS,
    PLANE_RESTING_SPEED_THRESHOLD,
    PLANE_ZERO_LENGTH_NUDGE,
    RESTITUTION_CORRECTION,
    ROD_DRAW_THICKNESS_SCALE,
    ROD_MIN_CLICK_THICKNESS,
    ROD_SMALL_ANGLE_THRESHOLD,
    ZERO_DISTANCE_FALLBACK,
    BODY_ACTIVE_COLOUR
)

from utils.coord_conversion import to_pygame
from utils.click import check_click_on_rectangle, check_click_on_circle
from utils.bounds import point_outside_bounds, circle_outside_bounds

if TYPE_CHECKING:
    from simulator.sim import Simulation

BodyInteractionResult = dict[str, object]

class SimDynamicBody(ABC):
    __slots__ = ()

    @abstractmethod
    def outside_bounds(
        self,
        max_x: float,
        max_y: float
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def draw(
        self,
        screen: pygame.Surface,
        screen_w: float,
        screen_h: float,
        zoom: float
    ) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def clicked(
        self,
        sim: "Simulation",
        mouse_pos: tuple[int, int]
    ) -> "SimDynamicBody | None":
        raise NotImplementedError

    @abstractmethod
    def handle_click(
        self,
        clicked_body: "SimDynamicBody | SimStaticBody | None"
    ) -> BodyInteractionResult:
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        dt: float,
        g: float
    ) -> None:
        raise NotImplementedError

class SimStaticBody(ABC):
    __slots__ = ()

    @abstractmethod
    def refresh_geometry(
        self
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def draw(
        self,
        screen: pygame.Surface,
        screen_w: float,
        screen_h: float,
        zoom: float
    ) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def clicked(
        self,
        sim: "Simulation",
        mouse_pos: tuple[int, int]
    ) -> "SimStaticBody | None":
        raise NotImplementedError

    @abstractmethod
    def handle_click(
        self,
        clicked_body: "SimDynamicBody | SimStaticBody | None"
    ) -> BodyInteractionResult:
        raise NotImplementedError

    @abstractmethod
    def collided_with(
        self,
        p: "Particle"
    ) -> tuple[bool, float, Vector]:
        raise NotImplementedError

    @abstractmethod
    def handle_collision(
        self,
        p: "Particle",
        psibling: "Particle | None",
        dist2: float,
        closest_point: Vector
    ) -> None:
        raise NotImplementedError

class Particle(SimDynamicBody):
    __slots__ = (
        "id",
        "particles",
        "sibling",
        "mass",
        "position",
        "radius",
        "velocity",
        "acceleration",
        "user_acceleration",
        "acting_forces",
        "resultant_force",
        "forces_changed",
        "acceleration_changed",
        "mass_changed",
        "active_colour",
        "colour",
        "base_colour"
    )

    next_id = 0
    def __init__(
        self,
        mass: float,
        colour: str,
        base_colour: str,
        position: Vector,
        radius: float
    ) -> None:
        self.id = Particle.next_id
        Particle.next_id += 1

        self.particles = [self]
        self.sibling = None

        self.mass = mass
        self.position = position
        self.radius = radius

        self.velocity = Vector(0,0)
        self.acceleration = Vector(0,0)
        self.user_acceleration = Vector(0,0)
        self.acting_forces = []
        self.resultant_force = Vector(0,0)

        self.forces_changed = False
        self.acceleration_changed = True
        self.mass_changed = False

        self.active_colour = BODY_ACTIVE_COLOUR
        self.colour = colour
        self.base_colour = base_colour

    def draw(
        self,
        screen: pygame.Surface,
        screen_w: float,
        screen_h: float,
        zoom: float
    ) -> None:
        pygame.draw.circle(
            screen, self.colour,
            to_pygame(self.position, screen_w, screen_h, zoom),
            max(self.radius*zoom, MIN_DRAW_RADIUS_PX)
            )

    def move(
        self,
        displacement: Vector
    ) -> None:
        self.position += displacement

    # Returns a boolean indicating if the particle lies outsife the maximum view distance, used for particle culling
    def outside_bounds(
        self,
        max_x: float,
        max_y: float
    ) -> bool:
        return circle_outside_bounds(self.position, self.radius, max_x, max_y)
    
    def clicked(
        self,
        sim: "Simulation",
        mouse_pos: tuple[int, int]
    ) -> "Particle | None":
        px, py = to_pygame(self.position, sim.screen_w, sim.screen_h, sim.scale.zoom)
        return self if check_click_on_circle(
            Vector(px, py),
            self.radius * sim.scale.zoom,
            Vector(mouse_pos[0], mouse_pos[1])
            ) else None

    # Returns a dict of infomation used by the interaction handler to mutate the sim calss to represent the changes caused by the click
    def handle_click(
        self,
        clicked_body: "SimDynamicBody | SimStaticBody | None"
    ) -> BodyInteractionResult:
        if not clicked_body:
            return {'click_handled': False}

        return {
            'click_handled': True,
            'remove_dynamic_body': True,
            'active_body': self,
            'selected_particle': self,
            'selected_rod': None,
            'selected_plane': None,
            'dragging_particle': self,
            'dragging_rod': None,
            'dragging_plane': None
        }

    def update(
        self,
        dt: float,
        g: float
    ) -> None:
        if dt == 0: return

        if self.forces_changed or self.mass_changed or self.acceleration_changed:
            self.calculate_resultant_force(g)
            self.__calculate_acceleration()
            self.forces_changed, self.acceleration_changed, self.mass_changed = False, False, False

        # Analytic integration with constant acceleration (SUVAT)
        self.position = self.position + self.velocity * dt + self.acceleration * (0.5 * dt * dt)
        self.velocity = self.velocity + self.acceleration * dt
    
    def calculate_resultant_force(
        self,
        g: float
    ) -> None:
        # User accelerations are dealt with by turning them into their corresponding ofrces and including them in the final resultant force, which is used to find the acceleration
        self.resultant_force = self.user_acceleration * self.mass + Vector(0, -self.mass * g) #weight force is always applied
        for newforce in self.acting_forces:
            self.resultant_force = self.resultant_force + newforce
    
    def __calculate_acceleration(
        self
    ) -> None:
        try:
            self.acceleration = self.resultant_force / self.mass
        except ZeroDivisionError:
            print('Division by 0. Mass is 0.')

    # Boolean return indicating if 2 particles did or didnt collide
    def collided_with(
        self,
        other: "Particle"
    ) -> bool:
        separation = other.position - self.position
        return separation.mag2() < (self.radius + other.radius)**2

    # Uses elastic collision equations, contains numeric falllbacks, thresholds and overlap correction to imporve stability
    def handle_collision(
        self,
        self_sibling: "Particle | None",
        other: "Particle",
        other_sibling: "Particle | None",
        e: float
    ) -> None:
        cut_off_threshold = PARTICLE_RESTING_SPEED_THRESHOLD

        self_group_mass = self.mass + (
            self_sibling.mass if self_sibling else 0
        )
        other_group_mass = other.mass + (
            other_sibling.mass if other_sibling else 0
        )
        m_sum_total = self_group_mass + other_group_mass

        line_of_centres = other.position - self.position
        d = line_of_centres.mag()
        overlap = (self.radius + other.radius) - d
        
        if d == 0:
            line_of_centres = Vector(ZERO_DISTANCE_FALLBACK, 0)
            overlap /= 2
            d = ZERO_DISTANCE_FALLBACK

        normal = line_of_centres / d
        self_norm_vel = self.velocity.dot(normal)
        other_norm_vel = other.velocity.dot(normal)
        if abs(self_norm_vel) <= cut_off_threshold and abs(other_norm_vel) <= cut_off_threshold:
            self.velocity = self.velocity - normal * self_norm_vel
            other.velocity = other.velocity - normal * other_norm_vel

        delta_velocity = other.velocity - self.velocity

        #skip collision if particles are already moving apart or in the same direction at same speed and also moves them out of each other
        if delta_velocity.dot(line_of_centres) >= 0:
            if overlap > 0: 
                self.__fix_overlap(
                    self_sibling,
                    other,
                    other_sibling,
                    overlap,
                    line_of_centres,
                    d,
                    self_group_mass,
                    other_group_mass,
                    m_sum_total
                )
            return
        
        e = max(e - RESTITUTION_CORRECTION, 0)

        s_f = (1 + e) * delta_velocity.dot(line_of_centres) / \
             (d * d * m_sum_total)

        impulse = line_of_centres * s_f
        self.velocity = self.velocity + impulse * other_group_mass

        other.velocity = other.velocity - impulse * self_group_mass

        self.__fix_overlap(
            self_sibling,
            other,
            other_sibling,
            overlap,
            line_of_centres,
            d,
            self_group_mass,
            other_group_mass,
            m_sum_total
        )

    # Mass wieghting overlap correction, more massive particle move less to correct overlap, also moves sibling particle(other partilce in rod object)
    def __fix_overlap(
        self,
        self_sibling: "Particle | None",
        other: "Particle",
        other_sibling: "Particle | None",
        overlap: float,
        line_of_centres: Vector,
        d: float,
        self_group_mass: float,
        other_group_mass: float,
        m_sum: float
    ) -> None:
        percent = OVERLAP_CORRECTION_PERCENT
        overlapthreshold = OVERLAP_CORRECTION_THRESHOLD

        # Only correct if deep enough overlap occurs
        correction_mag = max(overlap - overlapthreshold, 0.0) * percent
        if correction_mag <= 0:
            return

        normal = line_of_centres / d

        # Mass-weighted correction uses whole body masses (particle + sibling, if any).
        self_correction = correction_mag * (other_group_mass / m_sum)
        other_correction = correction_mag * (self_group_mass / m_sum)

        self.position = self.position - normal * self_correction
        if self_sibling:
            self_sibling.position = self_sibling.position - normal * self_correction

        other.position = other.position + normal * other_correction
        if other_sibling:
            other_sibling.position = other_sibling.position + normal * other_correction

class Rod(SimDynamicBody):
    __slots__ = (
        "particles",
        "active_colour",
        "colour",
        "base_colour",
        "__p1",
        "__p2",
        "__centre_of_mass",
        "__com_to_p1",
        "__com_to_p2",
        "__length2",
        "__resultant_force",
        "__total_mass",
        "__acceleration",
        "__velocity",
        "__resultant_torque",
        "__mmoi",
        "__angular_acceleration",
        "__angular_velocity"
    )

    def __init__(
        self,
        colour: str,
        base_colour: str,
        p1: Particle,
        p2: Particle
    ) -> None:
        # This exists in SimStaticBody objects to make collision checking logic simpler
        self.particles = [p1,p2]

        self.active_colour = BODY_ACTIVE_COLOUR
        self.colour = colour
        self.base_colour = base_colour

        self.__p1 = p1 
        self.__p2 = p2

        self.__centre_of_mass = Vector(0,0)
        
        #vectors from the centre of mass to p1 and p2
        self.__com_to_p1 = Vector(0,0)
        self.__com_to_p2 = Vector(0,0)

        # Squared diameter of rod
        self.__length2 = (self.__p2.position - self.__p1.position).mag2()

        self.__resultant_force = Vector(0,0)
        self.__total_mass = self.__p1.mass + self.__p2.mass #total mass of both particles in the rod
        self.__acceleration = Vector(0,0)
        self.__velocity = Vector(0,0)

        self.__resultant_torque = 0
        self.__mmoi = 0
        self.__angular_acceleration = 0
        self.__angular_velocity = 0
        #inital calcuaaiton of angular acceleration as it always is skipped on the first frame, particle resolves this using acc_changed flag
        self.__calculate_centre_of_mass()
        self.__calculate_radius_vectors()
        self.__calculate_mass_moment_of_inertia()
        self.__calculate_angular_acceleration()

    def draw(
        self,
        screen: pygame.Surface,
        screen_w: int,
        screen_h: int,
        zoom: float
    ) -> None:
        pygame.draw.line(
            screen, self.colour,
            to_pygame(self.__p1.position, screen_w, screen_h, zoom),
            to_pygame(self.__p2.position, screen_w, screen_h, zoom),
            max(int(zoom*ROD_DRAW_THICKNESS_SCALE), MIN_DRAW_THICKNESS_PX)
            )
        self.__p1.draw(screen, screen_w, screen_h, zoom)
        self.__p2.draw(screen, screen_w, screen_h, zoom)

    def move(
        self,
        displacement: Vector
    ) -> None:
        for p in [self.__p1, self.__p2]:
            p.move(displacement)

    # True if both particles are outisde bounds, used for rod culling
    def outside_bounds(
        self,
        max_x: float,
        max_y: float
    ) -> bool:
        return self.__p1.outside_bounds(max_x, max_y) and self.__p2.outside_bounds(max_x, max_y)

    def clicked(
        self,
        sim: "Simulation",
        mouse_pos: tuple[int, int]
    ) -> "Particle | Rod | None":
        return (
            self.__p2 if self.__p2.clicked(sim, mouse_pos) else
            self.__p1 if self.__p1.clicked(sim, mouse_pos) else
            self if check_click_on_rectangle(self.__p1.position, self.__p2.position, max(ROD_MIN_CLICK_THICKNESS, 1/sim.scale.zoom), mouse_pos, sim.screen_w, sim.screen_h, sim.scale.zoom) else
            None
            )

    # Returns a dict of infomation used by the interaction handler to mutate the sim calss to represent the changes caused by the click
    def handle_click(
        self,
        clicked_body: "SimDynamicBody | SimStaticBody | None"
    ) -> BodyInteractionResult:
        if isinstance(clicked_body, Particle):
            # Swaps particles to bring clicked particle to the front by making clicked particle p2 as p2 is always drawn last on top of everything.
            if clicked_body != self.__p2:
                self.__p1, self.__p2 = self.__p2, self.__p1

            return {
                'click_handled': True,
                'remove_dynamic_body': True,
                'active_body': clicked_body,
                'selected_particle': clicked_body,
                'selected_rod': self,
                'selected_plane': None,
                'dragging_particle': clicked_body,
                'dragging_rod': None,
                'dragging_plane': None
            }

        if clicked_body:
            return {
                'click_handled': True,
                'remove_dynamic_body': True,
                'active_body': self,
                'selected_particle': None,
                'selected_rod': self,
                'selected_plane': None,
                'dragging_particle': None,
                'dragging_rod': self,
                'dragging_plane': None
            }

        return {'click_handled': False}

    def update(
        self,
        dt: float,
        g: float
    ) -> None:
        if dt == 0:
            return

        mass_changed = self.__refresh_mass_and_geometry()
        self.__recompute_translation_data_if_needed(g, mass_changed)
        self.__integrate_com_translation(dt)

        self.__recompute_rotation_data()
        self.__integrate_rotation(dt)
        
        self.__sync_particle_kinematics_for_ui()

    def __refresh_mass_and_geometry(
        self
    ) -> bool:
        mass_changed = self.__p1.mass_changed or self.__p2.mass_changed

        if mass_changed:
            self.__total_mass = self.__p1.mass + self.__p2.mass
            self.__p1.mass_changed, self.__p2.mass_changed = False, False

        self.__calculate_centre_of_mass()
        self.__calculate_radius_vectors()

        current_length2 = (self.__p2.position - self.__p1.position).mag2()
        if mass_changed or current_length2 != self.__length2:
            self.__calculate_mass_moment_of_inertia()
            current_length2 = (self.__p2.position - self.__p1.position).mag2()
            self.__length2 = current_length2

        return mass_changed

    def __recompute_translation_data_if_needed(
        self,
        g: float,
        mass_changed: bool
    ) -> None:
        if (
            mass_changed
            or self.__p1.forces_changed
            or self.__p2.forces_changed
            or self.__p1.acceleration_changed
            or self.__p2.acceleration_changed
        ):
            self.__calculate_resultant_force(g)
            self.__calculate_acceleration()
            self.__p1.forces_changed, self.__p2.forces_changed = False, False
            self.__p1.acceleration_changed, self.__p2.acceleration_changed = False, False

        self.__velocity = (
            self.__p1.velocity * self.__p1.mass +
            self.__p2.velocity * self.__p2.mass
        ) / self.__total_mass

    def __integrate_com_translation(
        self,
        dt: float
    ) -> None:
        self.__centre_of_mass = self.__centre_of_mass + self.__velocity * dt + self.__acceleration * (0.5 * dt * dt)
        self.__velocity = self.__velocity + self.__acceleration * dt

    def __recompute_rotation_data(
        self
    ) -> None:
        self.__calculate_resultant_torque()
        self.__calculate_angular_acceleration()

        cross1 = self.__com_to_p1.cross(self.__p1.velocity)
        cross2 = self.__com_to_p2.cross(self.__p2.velocity)
        self.__angular_velocity = (cross1 * self.__p1.mass + cross2 * self.__p2.mass) / self.__mmoi

    def __integrate_rotation(
        self,
        dt: float
    ) -> None:
        delta_angle = self.__angular_velocity * dt + 0.5 * self.__angular_acceleration * dt * dt
        self.__angular_velocity += self.__angular_acceleration * dt

        if abs(delta_angle) <= ROD_SMALL_ANGLE_THRESHOLD:
            sin_da = delta_angle
            cos_da = 1 - (delta_angle * delta_angle / 2)
        else:
            sin_da = sin(delta_angle)
            cos_da = cos(delta_angle)

        self.__p1.position = self.__com_to_p1.rotated_by(sin_da, cos_da) + self.__centre_of_mass
        self.__p2.position = self.__com_to_p2.rotated_by(sin_da, cos_da) + self.__centre_of_mass

    def __sync_particle_kinematics_for_ui(
        self
    ) -> None:
        # Updating particle velocity and acceleration, not needed for calcuulation but needed to display the attributes to user
        for p, r in ((self.__p1, self.__com_to_p1), (self.__p2, self.__com_to_p2)):
            r_perp = r.perp()
            tangential = r_perp * self.__angular_acceleration
            centripetal = r * (self.__angular_velocity ** 2)
            p.acceleration = self.__acceleration - centripetal + tangential
            p.velocity = self.__velocity + r_perp * self.__angular_velocity

    def __calculate_resultant_force(
        self,
        g: float
    ) -> None:
        self.__p1.calculate_resultant_force(g)
        self.__p2.calculate_resultant_force(g)

        self.__resultant_force = self.__p1.resultant_force + self.__p2.resultant_force
        
    def __calculate_acceleration(
        self
    ) -> None:
        try:
            self.__acceleration = self.__resultant_force / self.__total_mass
        except ZeroDivisionError:
            print('Division by 0. Total mass is 0.')

    def __calculate_resultant_torque(
        self
    ) -> None:
        self.__resultant_torque = 0
        # calculates resultant moment (aka torque) by utilising cross product
        # moment = FD, where d is the distance from the pivot and f is the perpendicular component of the
        # force on the rod. Distance from pivot = |com_to_p|, then the perpendicular component of the force 
        # is |f|sin(theta), where theta is the angle between the force and rod. Therefore, 
        # moment on rod = |com_to_p||f|sin(theta), this is equal to the magnitude of the cross product 
        # of the 2 vectors.
        self.__resultant_torque += self.__com_to_p1.cross(self.__p1.resultant_force)
        self.__resultant_torque += self.__com_to_p2.cross(self.__p2.resultant_force)

    def __calculate_mass_moment_of_inertia(
        self
    ) -> None:
        # formula to calculate mmoi for 1 particel is I = mr^2 where r is the distance from the pivot
        self.__mmoi = self.__p1.mass * self.__com_to_p1.mag2() + (
                    self.__p2.mass * self.__com_to_p2.mag2()
                    )
        
        if self.__mmoi == 0:
            self.__p2.position += Vector(MMOI_ZERO_NUDGE, 0)
            self.__calculate_centre_of_mass()
            self.__calculate_radius_vectors()
            self.__calculate_mass_moment_of_inertia()

    def __calculate_angular_acceleration(
        self
    ) -> None:
        self.__angular_acceleration = self.__resultant_torque/self.__mmoi

    def __calculate_radius_vectors(
        self
    ) -> None:
        self.__com_to_p1 = self.__p1.position - self.__centre_of_mass
        self.__com_to_p2 = self.__p2.position - self.__centre_of_mass

    def __calculate_centre_of_mass(
        self
    ) -> None:
        self.__centre_of_mass = (
            (self.__p1.position * self.__p1.mass) + (self.__p2.position * self.__p2.mass)
        ) / self.__total_mass

class Plane(SimStaticBody):
    __slots__ = (
        "start",
        "end",
        "thickness",
        "e",
        "colour",
        "base_colour",
        "active_colour",
        "__center",
        "__half_length",
        "__half_thickness",
        "__dir",
        "__normal",
        "__c1",
        "__c2",
        "__c3",
        "__c4"
    )

    def __init__(
        self,
        colour: str,
        base_colour: str,
        start: Vector,
        end: Vector
    ) -> None:
        self.start = start
        self.end = end

        self.thickness = PLANE_DEFAULT_THICKNESS
        self.e = DEFAULT_RESTITUTION

        self.colour = colour
        self.base_colour = base_colour
        self.active_colour = BODY_ACTIVE_COLOUR

        self.refresh_geometry()

    # Recomputes physical data about the plane based on its start and end and thickness
    def refresh_geometry(
        self
    ) -> None:
        direction = self.end - self.start

        self.__center = (self.start + self.end) * 0.5

        length = direction.mag()
        self.__half_length = length / 2
        self.__half_thickness = self.thickness / 2

        if length == 0:
            self.end = self.end + Vector(PLANE_ZERO_LENGTH_NUDGE, 0)
            direction = self.end - self.start
            length = direction.mag()
            self.__half_length = length / 2

        self.__dir = direction / length
        self.__normal = self.__dir.perp()

        self.__c1 = self.start + self.__normal * self.__half_thickness
        self.__c2 = self.start - self.__normal * self.__half_thickness
        self.__c3 = self.end - self.__normal * self.__half_thickness
        self.__c4 = self.end + self.__normal * self.__half_thickness

    def draw(
        self,
        screen: pygame.Surface,
        screen_w: float,
        screen_h: float,
        zoom: float
    ) -> None:
        pygame.draw.polygon(
            screen,
            self.colour,
            [
                to_pygame(self.__c1, screen_w, screen_h, zoom),
                to_pygame(self.__c2, screen_w, screen_h, zoom),
                to_pygame(self.__c3, screen_w, screen_h, zoom),
                to_pygame(self.__c4, screen_w, screen_h, zoom)
            ]
        )

    def move(
        self,
        displacement: Vector
    ) -> None:
        self.start += displacement
        self.end += displacement
        self.refresh_geometry()

    def outside_bounds(
        self,
        max_x: float,
        max_y: float
    ) -> bool:
        return point_outside_bounds(self.start, max_x, max_y) and point_outside_bounds(self.end, max_x, max_y)

    def clicked(
        self,
        sim: "Simulation",
        mouse_pos: tuple[int, int]
    ) -> "Plane | None":
        return self if check_click_on_rectangle(self.start, self.end, self.thickness, mouse_pos, sim.screen_w, sim.screen_h, sim.scale.zoom) else None
    
    def handle_click(
        self,
        clicked_body: "SimDynamicBody | SimStaticBody | None"
    ) -> BodyInteractionResult:
        if not clicked_body:
            return {'click_handled': False}

        return {
            'click_handled': True,
            'remove_dynamic_body': False,
            'active_body': self,
            'selected_particle': None,
            'selected_rod': None,
            'selected_plane': self,
            'dragging_particle': None,
            'dragging_rod': None,
            'dragging_plane': self
        }
    
    # Tuple indicates if collision occurred, and has some values needed for collision maths to avoid calculation redundancy
    def collided_with(
        self,
        p: Particle
    ) -> tuple[bool, float, Vector]:
        dist2, closest_point = self.__get_collision_info(p)
        return dist2 <= p.radius * p.radius, dist2, closest_point

    # Elastic collision with numeric fallbacks, thresholds and overlap correction
    def handle_collision(
        self,
        p: Particle,
        psibling: "Particle | None",
        dist2: float,
        closest_point: Vector
    ) -> None:
        normal = self.__determine_normal(p, closest_point)

        if normal.mag2() == 0:
            return

        cut_off_threshold = PLANE_RESTING_SPEED_THRESHOLD
        vn = p.velocity.dot(normal)

        overlap = p.radius - (dist2 ** 0.5)

        if overlap <= 0:
            return

        if vn > 0:
            self.__fix_overlap(p, psibling, normal, overlap)
            return

        if abs(vn) < cut_off_threshold:
            p.velocity = p.velocity - normal * vn
        else:
            e = max(self.e - RESTITUTION_CORRECTION, 0)
            dvn = -(1 + e) * vn
            p.velocity = p.velocity + normal * dvn

        self.__fix_overlap(p, psibling, normal, overlap)
    
    def __determine_normal(
        self,
        p: Particle,
        closest_point: Vector
    ) -> Vector:
        offset = p.position - closest_point
        mag = offset.mag()

        if mag == 0:
            return self.__normal

        return offset / mag

    def __get_collision_info(
        self,
        p: Particle
    ) -> tuple[float, Vector]:
        particle_to_center = p.position - self.__center

        local_coords = Vector(
            particle_to_center.dot(self.__dir),
            particle_to_center.dot(self.__normal)
        )

        clamp_min = Vector(-self.__half_length, -self.__half_thickness)
        clamp_max = Vector(self.__half_length, self.__half_thickness)
        clamped_local = local_coords.component_max(clamp_min).component_min(clamp_max)

        closest_point = self.__center + self.__dir * clamped_local.x + self.__normal * clamped_local.y

        delta = p.position - closest_point

        return delta.mag2(), closest_point

    # Plane has infinite weight, does not move, only particle is moved
    def __fix_overlap(
        self,
        p: Particle,
        psibling: "Particle | None",
        normal: Vector,
        overlap: float
    ) -> None:
        percent = OVERLAP_CORRECTION_PERCENT
        overlapthreshold = OVERLAP_CORRECTION_THRESHOLD

        correction_mag = max(overlap - overlapthreshold, 0.0) * percent
        if correction_mag <= 0:
            return

        correction = normal * correction_mag
        p.position = p.position + correction
        if psibling:
            psibling.position = psibling.position + correction
