from __future__ import annotations
from typing import TYPE_CHECKING, TypeAlias
import pygame
from copy import deepcopy

from physics.constants import BODY_ACTIVE_COLOUR, TIME_SCRUB_SUBSTEPS
from physics.world import World
from simulator.constants import (
    DELETE_BUTTON_CROSS_THICKNESS,
    INPUT_BOX_CORNER_RADIUS,
    INPUT_BOX_ICON_LINE_THICKNESS,
    TIME_FIELD_NAME,
    UI_COLOUR_PANEL_INPUT_TEXT,
    UI_COLOUR_TIME_ACTIVE
)

from ui_elements.input_boxes import InputBox

from utils.reset_colours import reset_object_colours
from utils.draw_text import pygame_write

if TYPE_CHECKING:
    from simulator.sim import Simulation

Number: TypeAlias = int | float
Point: TypeAlias = tuple[Number, Number]
Dimensions: TypeAlias = tuple[Number, Number]
MousePos: TypeAlias = tuple[int, int]
Colour: TypeAlias = str | tuple[int, int, int]

class DeleteButton:
    __slots__ = ("__colour", "__rect")

    def __init__(
        self,
        colour: Colour,
        startx: Number,
        starty: Number,
        width: Number,
        height: Number
    ) -> None:
        self.__colour: Colour = colour
        self.__rect: pygame.Rect = pygame.Rect(startx, starty, width, height)
    
    def draw(
        self,
        sim: "Simulation"
    ) -> None:
        pygame.draw.line(sim.screen,
                         self.__colour,
                         self.__rect.topleft,
                         self.__rect.bottomright,
                         DELETE_BUTTON_CROSS_THICKNESS)
        pygame.draw.line(sim.screen,
                         self.__colour,
                         self.__rect.topright,
                         self.__rect.bottomleft,
                         DELETE_BUTTON_CROSS_THICKNESS)
    
    def handle_click(
        self,
        sim: "Simulation",
        mouse_pos: MousePos
    ) -> None:
        if self.__rect.collidepoint(mouse_pos):
            sim.world = World()
            sim.begin_sim = False
            sim.accumulator = 0
            sim.time_control.time, sim.accumulator = 0, 0
            sim.world_at_start, sim.forces_boxes_at_start = None, None
            sim.particle_bottom_panel.widgets[1].input_boxes = {}
            sim.selection_state.deselect_objects()

            sim.selection_state.click_handled = True

class PlayButton:
    __slots__ = (
        "__colour",
        "__startx",
        "__starty",
        "__width",
        "__height",
        "__rect"
    )

    def __init__(
        self,
        colour: Colour,
        startx: Number,
        starty: Number,
        width: Number,
        height: Number
    ) -> None:
        self.__colour: Colour = colour
        self.__startx: Number = startx
        self.__starty: Number = starty
        self.__width: Number = width
        self.__height: Number = height
        self.__rect: pygame.Rect = pygame.Rect(startx, starty, width, height)
    
    def draw(
        self,
        sim: "Simulation"
    ) -> None:
        pygame.draw.polygon(sim.screen,
                            self.__colour,
                            ((self.__startx, self.__starty),
                             (self.__startx, self.__starty+self.__height),
                             (self.__startx+self.__width, self.__starty+(0.5*self.__height))),
                            2)
    
    def handle_click(
        self,
        sim: "Simulation",
        mouse_pos: MousePos
    ) -> None:
        if self.__rect.collidepoint(mouse_pos):
            if not sim.world_at_start:
                selected_body = sim.selection_state.selected_particle if sim.selection_state.selected_particle else sim.selection_state.selected_rod if sim.selection_state.selected_rod else sim.selection_state.selected_plane if sim.selection_state.selected_plane else None
                if selected_body:
                    reset_object_colours(sim)
                    sim.world_at_start = deepcopy(sim.world)
                    selected_body.colour = BODY_ACTIVE_COLOUR
                else:
                    sim.world_at_start = deepcopy(sim.world)
                    
                # Copies the dictionary containing the force input boxes that the Force window widget uses to draw from.
                # This dictionary is dynamic (unlike the one used by attribute editor) and reflects the forces on 
                # the particles and so must be preserved.
                sim.forces_boxes_at_start = deepcopy(sim.particle_bottom_panel.widgets[1].input_boxes)
            
            sim.begin_sim = not sim.begin_sim
            sim.selection_state.click_handled = True
        
class TimeController(InputBox):
    __slots__ = "time"

    def __init__(
        self,
        startx: Number,
        starty: Number,
        width: Number,
        height: Number,
        colour: Colour,
        label: str | None,
        label_on_top: bool,
        label_colour: Colour | None = None,
        del_button: bool = False,
        active_colour: Colour = UI_COLOUR_TIME_ACTIVE
    ) -> None:
        super().__init__(
            startx,
            starty,
            width,
            height,
            colour,
            label,
            label_on_top,
            label_colour,
            del_button,
            active_colour
        )
        self._active_colour = active_colour
        self.time: float = 0

    def draw(
        self,
        sim: "Simulation"
    ) -> None:
        pygame.draw.rect(sim.screen,
                         self.colour,
                         self.rect,
                         0,
                         INPUT_BOX_CORNER_RADIUS)
        
        if self.colour == self._active_colour:
            pygame_write(
                sim.screen, sim.input_state.val, sim.box_font,
                self.rect, 
                False,
                UI_COLOUR_PANEL_INPUT_TEXT
                )
        else:
            pygame_write(
                sim.screen, str(round(self.time, 2)), sim.box_font,
                self.rect, 
                False,
                UI_COLOUR_PANEL_INPUT_TEXT
                )
        
        pygame_write(sim.screen, self._label, sim.label_font, self._label_rect, self._label_text_in_middle, self._label_colour)

    def handle_click(
        self,
        sim: "Simulation",
        mouse_pos: MousePos
    ) -> None:
        if self.rect.collidepoint(mouse_pos):
            self.colour = self._active_colour
            sim.input_state.selected_box = self
            sim.input_state.user_input['value_to_update'] = TIME_FIELD_NAME
            sim.selection_state.deselect_objects()
            sim.selection_state.click_handled = True
    
    def jump_to_time(
        self,
        sim: "Simulation"
    ) -> None:
        new_time = float(sim.input_state.val)
        if new_time < 0:
            return
        
        if sim.world_at_start is None:
            if sim.world.dynamic_bodies == []:
                return
            
            else:
                sim.world_at_start = deepcopy(sim.world)
                sim.forces_boxes_at_start = deepcopy(sim.particle_bottom_panel.widgets[1].input_boxes)
        
        sim.selection_state.deselect_objects()

        sim.begin_sim = True
        sim.world = deepcopy(sim.world_at_start) 
        sim.particle_bottom_panel.widgets[1].input_boxes = deepcopy(sim.forces_boxes_at_start)
        self.time = 0
        sim.accumulator = 0

        sim.update_world(new_time)        
        if sim.accumulator > 0:
            dt = sim.accumulator / TIME_SCRUB_SUBSTEPS
            for _ in range(TIME_SCRUB_SUBSTEPS):
                sim.world.get_next_frame(dt)
            self.time += sim.accumulator
            sim.accumulator = 0

        sim.begin_sim = False