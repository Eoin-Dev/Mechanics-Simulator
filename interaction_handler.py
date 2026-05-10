from __future__ import annotations
from typing import TYPE_CHECKING, TypeAlias
import pygame

from utils.coord_conversion import to_cartesian

if TYPE_CHECKING:
    from physics.bodies import BodyInteractionResult, Particle, Plane, Rod, SimDynamicBody, SimStaticBody
    from simulator.sim import Simulation

MousePos: TypeAlias = tuple[int, int]

# Applies world interaction caused muattions to sim class, delegates ui interaction casued mutations to sim class, to ui objects
class InteractionHandler:
    __slots__ = ()

    def check_clickable_ui_items(
        self,
        sim: "Simulation",
        mouse_pos: MousePos
    ) -> None:
        for item in sim.clickable_ui_items:
            item.handle_click(sim, mouse_pos)
            if sim.selection_state.click_handled:
                break

    def __apply_world_interaction(
        self,
        sim: "Simulation",
        source_body: "SimDynamicBody | SimStaticBody",
        interaction: "BodyInteractionResult"
    ) -> None:
        if not interaction.get("click_handled"):
            return

        remove_dynamic_body = interaction.get("remove_dynamic_body")
        if remove_dynamic_body and source_body in sim.world.dynamic_bodies:
            sim.world.dynamic_bodies.remove(source_body)

        active_body = interaction.get("active_body")
        if active_body is not None:
            active_body.colour = active_body.active_colour

        for key, value in interaction.items():
            if key not in ("remove_dynamic_body", "active_body"):
                setattr(sim.selection_state, key, value)

    def check_clickable_world_items(
        self,
        sim: "Simulation",
        mouse_pos: MousePos
    ) -> None:
        if sim.selection_state.click_handled:
            return

        ordered_bodies: list[list["Rod | Particle | Plane | SimDynamicBody | SimStaticBody | None"]] = [
            [sim.selection_state.selected_rod, sim.selection_state.selected_particle, sim.selection_state.selected_plane],
            sim.world.dynamic_bodies,
            sim.world.static_bodies
        ]

        for body_group in ordered_bodies:
            for body in body_group:
                if body is None:
                    continue

                clicked_body = body.clicked(sim, mouse_pos)
                if not clicked_body:
                    continue

                sim.selection_state.deselect_objects()
                interaction = body.handle_click(clicked_body)
                self.__apply_world_interaction(sim, body, interaction)
                return

        sim.selection_state.deselect_objects()

    def check_scrollable_ui_items(
        self,
        sim: "Simulation",
        scroll_direction: int,
        mouse_pos: MousePos
    ) -> None:
        for item in sim.scrollable_ui_items:
            item.handle_scroll(sim, scroll_direction, mouse_pos)
            if sim.scroll_handled:
                return

    def disable_dragging(
        self,
        sim: "Simulation"
    ) -> None:
        if sim.selection_state.dragging_particle:
            if not sim.selection_state.selected_rod:
                # Insert maintains stack data structure.
                sim.world.dynamic_bodies.insert(0, sim.selection_state.dragging_particle)
            else:
                sim.world.dynamic_bodies.insert(0, sim.selection_state.selected_rod)
            sim.selection_state.dragging_particle = None

        elif sim.selection_state.dragging_rod:
            sim.world.dynamic_bodies.insert(0, sim.selection_state.dragging_rod)
            sim.selection_state.dragging_rod = None

        elif sim.selection_state.dragging_plane:
            sim.selection_state.dragging_plane = None

    def delete_in_left_panel(
        self,
        sim: "Simulation",
        mouse_pos: MousePos
    ) -> None:
        # If particle is released on the left panel, it is deleted.
        if sim.selection_state.selected_particle and not sim.selection_state.selected_rod:
            if sim.left_side_panel.rect.collidepoint(mouse_pos):
                sim.world.dynamic_bodies.remove(sim.selection_state.selected_particle)
                sim.selection_state.selected_particle = None
        # If rod is dragged onto the left panel, it is deleted.
        elif sim.selection_state.selected_rod:
            if sim.left_side_panel.rect.collidepoint(mouse_pos):
                sim.world.dynamic_bodies.remove(sim.selection_state.selected_rod)
                sim.selection_state.selected_rod = None
        # If plane is dragged onto left panel, it is deleted.
        elif sim.selection_state.selected_plane:
            if sim.left_side_panel.rect.collidepoint(mouse_pos):
                sim.world.static_bodies.remove(sim.selection_state.selected_plane)
                sim.selection_state.selected_plane = None

    def drag_item(
        self,
        sim: "Simulation",
        event: pygame.event.Event
    ) -> None:
        # Screen width and height are passed as 0 because this is a vector conversion.
        rel = to_cartesian(event.rel, 0, 0, sim.scale.zoom)

        for draggable in [sim.selection_state.dragging_rod, sim.selection_state.dragging_particle, sim.selection_state.dragging_plane]:
            if draggable is not None:
                draggable.move(rel)