from __future__ import annotations
from typing import TYPE_CHECKING, TypeAlias
import pygame

from simulator.constants import (
    FPS_MAX,
    FPS_STEP,
    KEY_CYCLE_FPS_CAP,
    KEY_QUIT,
    KEY_TOGGLE_COLLISION_MODE,
    KEY_TOGGLE_QUADTREE_BOUNDS,
    MOUSE_PRIMARY_BUTTON,
    TIME_FIELD_NAME
)
from simulator.interaction_handler import InteractionHandler

from utils.number_validation import is_valid_number

if TYPE_CHECKING:
    from simulator.sim import Simulation

MousePos: TypeAlias = tuple[int, int]

class InputHandler:
    __slots__ = "__interaction_handler"

    def __init__(
        self,
        interaction_handler: InteractionHandler
    ) -> None:
        self.__interaction_handler = interaction_handler

    # Detects user input and calls approprate methods, occurs once per frame
    def handle_events(
        self,
        sim: "Simulation",
        mouse_pos: MousePos
    ) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sim.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == MOUSE_PRIMARY_BUTTON:
                self.__handle_mouse_button_down(sim, mouse_pos)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == MOUSE_PRIMARY_BUTTON:
                self.__handle_mouse_button_up(sim, mouse_pos)

            elif event.type == pygame.MOUSEMOTION:
                self.__handle_mouse_motion(sim, event)

            elif event.type == pygame.KEYDOWN:
                self.__handle_key_down(sim, event)

            elif event.type == pygame.MOUSEWHEEL:
                self.__handle_mouse_wheel(sim, event, mouse_pos)

    def __handle_mouse_button_down(
        self,
        sim: "Simulation",
        mouse_pos: MousePos
    ) -> None:
        sim.selection_state.click_handled = False
        # Always deselects box, then reselects again later if needed.
        sim.input_state.deselect_box()

        self.__interaction_handler.check_clickable_ui_items(sim, mouse_pos)
        self.__interaction_handler.check_clickable_world_items(sim, mouse_pos)

    def __handle_mouse_button_up(
        self,
        sim: "Simulation",
        mouse_pos: MousePos
    ) -> None:
        self.__interaction_handler.disable_dragging(sim)
        self.__interaction_handler.delete_in_left_panel(sim, mouse_pos)

    def __handle_mouse_motion(
        self,
        sim: "Simulation",
        event: pygame.event.Event
    ) -> None:
        self.__interaction_handler.drag_item(sim, event)

    def __handle_key_down(
        self,
        sim: "Simulation",
        event: pygame.event.Event
    ) -> None:
        if sim.input_state.user_input["value_to_update"]:
            if event.unicode.isdigit() or event.unicode == "." or event.unicode == "-":
                sim.input_state.val += event.unicode

            elif event.key == pygame.K_BACKSPACE:
                sim.input_state.val = sim.input_state.val[:-1]

            elif event.key == pygame.K_RETURN and is_valid_number(sim.input_state.val):
                if sim.input_state.user_input["value_to_update"] == TIME_FIELD_NAME:
                    sim.time_control.jump_to_time(sim)

                elif sim.selection_state.selected_particle:
                    sim.particle_bottom_panel.update_attribute(sim, sim.selection_state.selected_particle)

                elif sim.selection_state.selected_plane:
                    sim.plane_bottom_panel.update_attribute(sim, sim.selection_state.selected_plane)

                else:
                    sim.right_top_panel.update_attribute(sim)

                sim.input_state.deselect_box()

        elif event.key == KEY_TOGGLE_QUADTREE_BOUNDS:
            sim.show_quadtree_bounds = not sim.show_quadtree_bounds

        elif event.key == KEY_TOGGLE_COLLISION_MODE:
            sim.world.toggle_collision_mode()

        elif event.key == KEY_CYCLE_FPS_CAP:
            sim.fps.cycle_cap(FPS_STEP, FPS_MAX)

        elif event.key == KEY_QUIT:
            sim.running = False

    def __handle_mouse_wheel(
        self,
        sim: "Simulation",
        event: pygame.event.Event,
        mouse_pos: MousePos
    ) -> None:
        sim.scroll_handled = False
        self.__interaction_handler.check_scrollable_ui_items(sim, event.y, mouse_pos)