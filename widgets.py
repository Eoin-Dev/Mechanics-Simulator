from __future__ import annotations
import pygame
from abc import ABC, abstractmethod
from collections.abc import Callable
from random import choice
from copy import deepcopy
from typing import TYPE_CHECKING, TypeAlias

from physics.constants import BODY_ACTIVE_COLOUR, SPAWN_PARTICLE_MASS
from physics.bodies import Particle, Rod, Plane
from physics.world import World
from physics.vector import Vector
from simulator.constants import (
    COLOURS,
    FORCE_WINDOW_ADDER_H_END_SCALE,
    FORCE_WINDOW_ADDER_H_START_SCALE,
    FORCE_WINDOW_ADDER_V_X_SCALE,
    FORCE_WINDOW_ADDER_V_Y_START_DIVISOR,
    FORCE_WINDOW_COMPONENT_GAP_SCALE,
    FORCE_WINDOW_CORNER_RADIUS,
    FORCE_WINDOW_ICON_THICKNESS,
    FORCE_WINDOW_LABEL_HEIGHT_RATIO,
    FORCE_WINDOW_LABEL_Y_SCALE,
    FORCE_WINDOW_ROW_GAP_SCALE,
    FORCE_WINDOW_SCROLL_STEP,
    FORCE_WINDOW_X_COMPONENT_Y_SCALE,
    FORCE_WINDOW_BOX_X_DIVISOR,
    PANEL_ROD_MIN_THICKNESS,
    PANEL_ROD_THICKNESS_SCALE,
    UI_COLOUR_BOTTOM_PANEL_INPUT_ACTIVE,
    UI_COLOUR_BOTTOM_PANEL_INPUT_BOX,
    UI_COLOUR_BOTTOM_PANEL_INPUT_LABEL,
    UI_COLOUR_BOTTOM_PANEL_INPUT_TEXT,
    UI_COLOUR_FORCE_ADDER_ICON,
    UI_COLOUR_PANEL_INPUT_LABEL,
    UI_TEXT_FORCES
)

from ui_elements.input_boxes import InputBox

from utils.click import check_click_on_circle
from utils.coord_conversion import to_cartesian
from utils.draw_text import pygame_write

if TYPE_CHECKING:
    from simulator.sim import Simulation

Number: TypeAlias = int | float
Point: TypeAlias = tuple[Number, Number]
Dimensions: TypeAlias = tuple[Number, Number]
MousePos: TypeAlias = tuple[int, int]
Colour: TypeAlias = str | tuple[int, int, int]
InputBoxesByParticle: TypeAlias = dict[int, list[InputBox]]
Fields: TypeAlias = dict[str, list[InputBox]]
EditableItem: TypeAlias = Particle | Plane | World

RuleConstraint: TypeAlias = Callable[[float], bool]
RuleAction: TypeAlias = Callable[[EditableItem], None]
RuleDefinition: TypeAlias = dict[str, RuleConstraint | RuleAction]
RuleSet: TypeAlias = dict[str, RuleDefinition]

class Widget(ABC):
    __slots__ = ()

    @abstractmethod
    def handle_click(
        self,
        sim: "Simulation",
        mouse_pos: MousePos
    ) -> None:
        raise NotImplementedError

class ForceWindow(Widget):
    __slots__ = (
        "__start",
        "__colour",
        "input_boxes",
        "__input_box_w",
        "__input_box_h",
        "__box_x_start",
        "__x_component_box_y_start",
        "__y_component_box_y_start",
        "__x_box_to_x_box_gap",
        "__adder_horizontal_start",
        "__adder_horizontal_end",
        "__adder_vertical_start",
        "__adder_vertical_end",
        "__rect",
        "__force_label_rect",
        "__force_adder_rect"
    )

    def __init__(
        self,
        start: Point,
        dimensions: Dimensions,
        colour: Colour,
        input_boxes: InputBoxesByParticle,
        input_box_width: Number,
        input_box_height: Number
    ) -> None:
        self.__start: Point = start
        self.__colour: Colour = colour
        self.input_boxes: InputBoxesByParticle = input_boxes
        self.__input_box_w: Number = input_box_width
        self.__input_box_h: Number = input_box_height

        self.__box_x_start = start[0] + (dimensions[0] - input_box_width) / FORCE_WINDOW_BOX_X_DIVISOR
        self.__x_component_box_y_start = self.__start[1] * FORCE_WINDOW_X_COMPONENT_Y_SCALE
        self.__y_component_box_y_start = self.__x_component_box_y_start + input_box_height * FORCE_WINDOW_COMPONENT_GAP_SCALE
        self.__x_box_to_x_box_gap = input_box_height * FORCE_WINDOW_ROW_GAP_SCALE

        self.__adder_horizontal_start = ((self.__start[0] + dimensions[0]) * FORCE_WINDOW_ADDER_H_START_SCALE, self.__x_component_box_y_start + input_box_height / 2)
        self.__adder_horizontal_end = ((self.__start[0] + dimensions[0]) * FORCE_WINDOW_ADDER_H_END_SCALE, self.__x_component_box_y_start + input_box_height / 2)
        self.__adder_vertical_start = ((self.__start[0] + dimensions[0]) * FORCE_WINDOW_ADDER_V_X_SCALE, self.__x_component_box_y_start + input_box_height / FORCE_WINDOW_ADDER_V_Y_START_DIVISOR)
        self.__adder_vertical_end = ((self.__start[0] + dimensions[0]) * FORCE_WINDOW_ADDER_V_X_SCALE, self.__x_component_box_y_start + input_box_height)

        self.__rect = pygame.Rect(start, dimensions)
        self.__force_label_rect = pygame.Rect(start[0], start[1] * FORCE_WINDOW_LABEL_Y_SCALE, dimensions[0], start[1] * FORCE_WINDOW_LABEL_HEIGHT_RATIO)
        self.__force_adder_rect = pygame.Rect(
            self.__adder_horizontal_start[0],
            self.__adder_vertical_start[1],
            self.__adder_horizontal_end[0] - self.__adder_horizontal_start[0],
            self.__adder_vertical_end[1] - self.__adder_vertical_start[1]
            )
    
    def draw(
        self,
        screen: pygame.Surface,
        selected_body: Particle,
        val: str,
        box_font: pygame.font.Font,
        label_font: pygame.font.Font
    ) -> None:
        pygame.draw.rect(screen, self.__colour, self.__rect, 0, FORCE_WINDOW_CORNER_RADIUS)
        screen.set_clip(self.__rect)
        if selected_body.id in self.input_boxes:
            boxes = self.input_boxes[selected_body.id]
            for i, box in enumerate(boxes):
                if not self.__rect.colliderect(box.rect):
                    pass
                else:
                    if i % 2 == 0:
                        box.draw(screen, str(round(selected_body.acting_forces[i // 2].x, 4)), val, box_font, label_font)
                    else:
                        box.draw(screen, str(round(selected_body.acting_forces[i // 2].y, 4)), val, box_font, label_font)

        screen.set_clip(None)

        pygame_write(screen, UI_TEXT_FORCES, label_font, self.__force_label_rect, True, UI_COLOUR_BOTTOM_PANEL_INPUT_LABEL)
        
        # Force adder icon
        pygame.draw.line(screen,
                         UI_COLOUR_FORCE_ADDER_ICON,
                         self.__adder_horizontal_start,
                         self.__adder_horizontal_end,
                         FORCE_WINDOW_ICON_THICKNESS)
        pygame.draw.line(screen,
                         UI_COLOUR_FORCE_ADDER_ICON,
                         self.__adder_vertical_start, 
                         self.__adder_vertical_end,
                         FORCE_WINDOW_ICON_THICKNESS)
    
    def handle_click(
        self,
        sim: "Simulation",
        mouse_pos: MousePos
    ) -> None:
        # Checks click on the force adder icon (green plus)
        if self.__force_adder_rect.collidepoint(mouse_pos):
            self.input_boxes.setdefault(sim.selection_state.selected_particle.id, []) # Creates selectedParticle:[], if its not already in dict
            x_box_previous_y_start = self.input_boxes[sim.selection_state.selected_particle.id][-2].rect.y if self.input_boxes[sim.selection_state.selected_particle.id] else self.__x_component_box_y_start - self.__x_box_to_x_box_gap
            y_box_previous_y_start = self.input_boxes[sim.selection_state.selected_particle.id][-1].rect.y if self.input_boxes[sim.selection_state.selected_particle.id] else self.__y_component_box_y_start - self.__x_box_to_x_box_gap

            self.input_boxes[sim.selection_state.selected_particle.id].append(InputBox(
                self.__box_x_start,
                x_box_previous_y_start + self.__x_box_to_x_box_gap,
                self.__input_box_w,
                self.__input_box_h,
                UI_COLOUR_BOTTOM_PANEL_INPUT_BOX,
                None,
                False,
                None,
                True,
                UI_COLOUR_BOTTOM_PANEL_INPUT_ACTIVE,
                UI_COLOUR_BOTTOM_PANEL_INPUT_TEXT
            ))
             
            self.input_boxes[sim.selection_state.selected_particle.id].append(InputBox(
                self.__box_x_start,
                y_box_previous_y_start + self.__x_box_to_x_box_gap,
                self.__input_box_w,
                self.__input_box_h, 
                UI_COLOUR_BOTTOM_PANEL_INPUT_BOX,
                None,
                False,
                active_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_ACTIVE,
                text_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_TEXT
            ))
            
            sim.selection_state.selected_particle.acting_forces.append(Vector(0, 0))
            sim.selection_state.click_handled = True
            return
        
        # Checks force inputs boxes
        elif sim.selection_state.selected_particle.id in self.input_boxes and self.__rect.collidepoint(mouse_pos):
            for i, box in enumerate(self.input_boxes[sim.selection_state.selected_particle.id]):
                # Checks clicks in the input boxes
                if box.clicked(mouse_pos):
                    sim.input_state.user_input['value_to_update'], sim.input_state.user_input['vector_component'], sim.input_state.user_input['force_index'] = 'acting_forces', ['x', 'y'][i % 2], i // 2
                    sim.input_state.selected_box = box
                    sim.selection_state.click_handled = True
                    return
                
                # Checks clicks on the delete button, remainder division used as only every other box has delete button
                elif i%2 == 0 and box.del_button_rect.collidepoint(mouse_pos):
                    # Updating the simulation
                    sim.selection_state.selected_particle.acting_forces.pop(i//2)
                    sim.selection_state.selected_particle.forces_changed = True

                    # Updating the sim
                    self.input_boxes[sim.selection_state.selected_particle.id].pop(i)
                    self.input_boxes[sim.selection_state.selected_particle.id].pop(i)
                    for force_box in self.input_boxes[sim.selection_state.selected_particle.id][i:]:
                        force_box.offset(0, -self.__x_box_to_x_box_gap)

                    sim.selection_state.click_handled = True
                    break
        return
    
    def scroll(
        self,
        sim: "Simulation",
        mouse_pos: MousePos,
        scroll_direction: int
    ) -> None:
        if sim.selection_state.selected_particle and self.__rect.collidepoint(mouse_pos) and sim.selection_state.selected_particle.id in self.input_boxes:
            if scroll_direction > 0:
                for force_box in self.input_boxes[sim.selection_state.selected_particle.id]:
                    force_box.offset(0, FORCE_WINDOW_SCROLL_STEP)
            elif scroll_direction < 0:
                for force_box in self.input_boxes[sim.selection_state.selected_particle.id]:
                    force_box.offset(0, -FORCE_WINDOW_SCROLL_STEP)
            sim.scroll_handled = True

    def update_attribute(
        self,
        sim: "Simulation",
        particle: Particle
    ) -> None:
        value = float(sim.input_state.val)
        force_index = sim.input_state.user_input["force_index"]
        vector_component = sim.input_state.user_input["vector_component"]

        if not isinstance(force_index, int):
            return
        if vector_component not in ("x", "y"):
            return
        if force_index < 0 or force_index >= len(particle.acting_forces):
            return

        target_force = particle.acting_forces[force_index]
        if vector_component == "x":
            target_force.x = value
        else:
            target_force.y = value
        particle.forces_changed = True

class AttributeEditor(Widget):
    __slots__ = (
        "__fields",
        "__rules",
        "__vector_attributes",
        "__scalar_attributes"
    )

    def __init__(
        self,
        fields: Fields,
        rules: RuleSet
    ) -> None:
        self.__fields: Fields = fields
        self.__rules: RuleSet = rules

        self.__vector_attributes: Fields = {}
        self.__scalar_attributes: Fields = {}
        for attribute, boxes in self.__fields.items():
            if len(boxes) == 2:
                self.__vector_attributes[attribute] = boxes
            else:
                self.__scalar_attributes[attribute] = boxes

    def draw(
        self,
        screen: pygame.Surface,
        selected_body: EditableItem,
        val: str,
        box_font: pygame.font.Font,
        label_font: pygame.font.Font
    ) -> None:
        for attribute, boxes in self.__fields.items():
            if attribute in self.__scalar_attributes:
                try:
                    scalar_value = getattr(selected_body, attribute)
                except AttributeError:
                    continue
                boxes[0].draw(screen, str(scalar_value), val, box_font, label_font)
                continue

            try:
                vector_value = self.__get_vector_value(selected_body, attribute)
            except KeyError:
                continue
            boxes[0].draw(screen, str(round(vector_value.x, 4)), val, box_font, label_font)
            boxes[1].draw(screen, str(round(vector_value.y, 4)), val, box_font)
    
    def handle_click(
        self,
        sim: "Simulation",
        mouse_pos: MousePos
    ) -> None:
        for attribute, boxes in self.__fields.items():
            for i, box in enumerate(boxes):
                if box.clicked(mouse_pos):
                    vector_component = None
                    if len(boxes) == 2:
                        vector_component = "x" if i == 0 else "y"

                    sim.input_state.selected_box = box
                    sim.input_state.user_input["value_to_update"] = attribute
                    sim.input_state.user_input["vector_component"] = vector_component
                    sim.input_state.user_input["force_index"] = None
                    sim.selection_state.click_handled = True
                    return

    def __get_vector_value(
        self,
        item: EditableItem,
        attribute: str
    ) -> Vector:
        if attribute not in self.__vector_attributes:
            raise KeyError(f"Unsupported vector attribute: {attribute}")

        try:
            vector_value = getattr(item, attribute)
        except AttributeError:
            raise KeyError(f"Unsupported vector attribute: {attribute}")

        if not isinstance(vector_value, Vector):
            raise KeyError(f"Attribute is not a vector: {attribute}")

        return vector_value

    def __set_scalar_value(
        self,
        item: EditableItem,
        attribute: str,
        value: float
    ) -> None:
        if attribute not in self.__scalar_attributes:
            raise KeyError(f"Unsupported scalar attribute: {attribute}")
        try:
            setattr(item, attribute, value)
        except AttributeError:
            raise KeyError(f"Unsupported scalar attribute: {attribute}")

    def __set_vector_component(
        self,
        item: EditableItem,
        attribute: str,
        component: str,
        value: float
    ) -> None:
        target_vector = self.__get_vector_value(item, attribute)
        if component not in ("x", "y"):
            raise KeyError(f"Unsupported vector component: {component}")

        if component == "x":
            target_vector.x = value
        else:
            target_vector.y = value

    def update_attribute(
        self,
        sim: "Simulation",
        item: EditableItem
    ) -> None:
        value_to_update = sim.input_state.user_input["value_to_update"]
        if not isinstance(value_to_update, str):
            return

        rule = self.__rules.get(value_to_update)
        value = float(sim.input_state.val)
        if not rule["constraint"](value):
            return

        try:
            if value_to_update in self.__scalar_attributes:
                self.__set_scalar_value(item, value_to_update, value)
            elif value_to_update in self.__vector_attributes:
                vector_component = sim.input_state.user_input["vector_component"]
                self.__set_vector_component(item, value_to_update, vector_component, value)
            else:
                return
        except KeyError:
            return

        rule["action"](item)

class PanelParticle(Widget):
    __slots__ = (
        "__pos",
        "__radius",
        "__new_particle_radius",
        "__colour"
    )

    def __init__(
        self,
        pos: Point,
        radius: Number,
        new_particle_radius: Number,
        colour: Colour
    ) -> None:
        self.__pos: Point = pos
        self.__radius: Number = radius
        self.__new_particle_radius: Number = new_particle_radius
        self.__colour: Colour = colour
    
    def draw(
        self,
        screen: pygame.Surface,
        _: pygame.font.Font
    ) -> None:
        pygame.draw.circle(screen, self.__colour, self.__pos, self.__radius)
    
    def handle_click(
        self,
        sim: "Simulation",
        mouse_pos: MousePos
    ) -> None:
        if check_click_on_circle(Vector(self.__pos[0], self.__pos[1]), self.__radius, Vector(mouse_pos[0], mouse_pos[1])):
            mouse = to_cartesian(mouse_pos, sim.screen_w, sim.screen_h, sim.scale.zoom)
            base_colour = choice(COLOURS)
            new_particle = Particle(
                SPAWN_PARTICLE_MASS,
                BODY_ACTIVE_COLOUR,
                base_colour,
                mouse,
                self.__new_particle_radius
                )
            sim.selection_state.selected_particle = new_particle
            sim.selection_state.dragging_particle = sim.selection_state.selected_particle
            sim.selection_state.click_handled = True
    
class PanelRod(Widget):
    __slots__ = (
        "__start",
        "__end",
        "__rect",
        "__radius",
        "__thickness",
        "__new_particle_radius",
        "__new_rod_length",
        "__p_colour",
        "__r_colour"
    )

    def __init__(
        self,
        start: Point,
        end: Point,
        radius: Number,
        new_particle_radius: Number,
        new_rod_length: Number,
        p_colour: Colour,
        r_colour: Colour
    ) -> None:
        self.__start: Point = start
        self.__end: Point = end
        self.__rect: pygame.Rect = pygame.Rect(start, (end[0] - start[0], end[1] - start[1]))
        self.__radius: Number = radius
        self.__thickness: int = int(max(radius * PANEL_ROD_THICKNESS_SCALE, PANEL_ROD_MIN_THICKNESS))
        self.__new_particle_radius: Number = new_particle_radius
        self.__new_rod_length: Number = new_rod_length
        self.__p_colour: Colour = p_colour
        self.__r_colour: Colour = r_colour
    
    def draw(
        self,
        screen: pygame.Surface,
        _: pygame.font.Font
    ) -> None:
        pygame.draw.line(screen, self.__r_colour, self.__start, self.__end, self.__thickness)
        pygame.draw.circle(screen, self.__p_colour, self.__start, self.__radius)
        pygame.draw.circle(screen, self.__p_colour, self.__end, self.__radius)
    
    def handle_click(
        self,
        sim: "Simulation",
        mouse_pos: MousePos
    ) -> None:
        if self.__rect.collidepoint(mouse_pos):
            mouse = to_cartesian(mouse_pos, sim.screen_w, sim.screen_h, sim.scale.zoom)

            p1_base_colour = choice(COLOURS)
            p2_base_colour = choice(COLOURS)
            rod_base_colour = choice(COLOURS)

            p1 = Particle(SPAWN_PARTICLE_MASS, p1_base_colour, p1_base_colour, mouse + Vector(-self.__new_rod_length, -self.__new_rod_length), self.__new_particle_radius)
            p2 = Particle(SPAWN_PARTICLE_MASS, p2_base_colour, p2_base_colour, mouse + Vector(self.__new_rod_length, self.__new_rod_length), self.__new_particle_radius)
            p1.sibling, p2.sibling = p2, p1

            new_rod = Rod(
                BODY_ACTIVE_COLOUR,
                rod_base_colour,
                p1,
                p2
                )
            sim.selection_state.selected_rod = new_rod
            sim.selection_state.dragging_rod = sim.selection_state.selected_rod
            sim.selection_state.click_handled = True

class PanelPlane(Widget):
    __slots__ = (
        "__start",
        "__end",
        "__rect",
        "__thickness",
        "__new_plane_length",
        "__colour"
    )

    def __init__(
        self,
        start: Point,
        end: Point,
        thickness: Number,
        new_plane_length: Number,
        colour: Colour
    ) -> None:
        self.__start: Point = start
        self.__end: Point = end
        self.__rect: pygame.Rect = pygame.Rect(start, (end[0] - start[0], end[1] - start[1]))
        self.__thickness: Number = thickness
        self.__new_plane_length: Number = new_plane_length
        self.__colour: Colour = colour
    
    def draw(
        self,
        screen: pygame.Surface,
        _: pygame.font.Font
    ) -> None:
        pygame.draw.line(screen, self.__colour, self.__start, self.__end, self.__thickness)
    
    def handle_click(
        self,
        sim: "Simulation",
        mouse_pos: MousePos
    ) -> None:
        if self.__rect.collidepoint(mouse_pos):
            mouse = to_cartesian(mouse_pos, sim.screen_w, sim.screen_h, sim.scale.zoom)
            plane_base_colour = choice(COLOURS)

            new_plane = Plane(
                BODY_ACTIVE_COLOUR,
                plane_base_colour,
                mouse + Vector(-self.__new_plane_length, 0),
                mouse + Vector(self.__new_plane_length, 0)
            )

            sim.selection_state.selected_plane = new_plane
            sim.selection_state.dragging_plane = sim.selection_state.selected_plane
            sim.world.static_bodies.insert(0, sim.selection_state.dragging_plane)
            sim.selection_state.click_handled = True

class PremadeWorld(Widget):
    __slots__ = (
        "__world",
        "__name",
        "__rect"
    )

    def __init__(
        self,
        world: "World",
        start: Point,
        dimensions: Dimensions,
        name: str
    ) -> None:
        self.__world: World = world
        self.__name: str = name
        self.__rect: pygame.Rect = pygame.Rect(start, dimensions)
    
    def draw(
        self,
        screen: pygame.Surface,
        font: pygame.font.Font
    ) -> None:
        pygame_write(screen, self.__name, font, self.__rect, True, UI_COLOUR_PANEL_INPUT_LABEL)
    
    def handle_click(
        self,
        sim: "Simulation",
        mouse_pos: MousePos
    ) -> None:
        if self.__rect.collidepoint(mouse_pos):
            sim.world = deepcopy(self.__world)
            sim.begin_sim = False
            sim.accumulator = 0
            sim.time_control.time = 0
            sim.world_at_start = None
            sim.forces_boxes_at_start = None
            sim.particle_bottom_panel.widgets[1].input_boxes = {}
            sim.selection_state.deselect_objects()
            sim.input_state.deselect_box()
            sim.selection_state.click_handled = True