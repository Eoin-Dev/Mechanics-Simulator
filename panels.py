from __future__ import annotations
import pygame
from typing import TYPE_CHECKING, TypeAlias

from simulator.constants import PANEL_CORNER_RADIUS, UI_COLOUR_PANEL_BG

if TYPE_CHECKING:
    from physics.bodies import Particle, Plane
    from simulator.sim import Simulation
    from ui_elements.widgets import (
        AttributeEditor,
        ForceWindow,
        PanelParticle,
        PanelPlane,
        PanelRod,
        PremadeWorld
    )

Number: TypeAlias = int | float
Point: TypeAlias = tuple[Number, Number]
Dimensions: TypeAlias = tuple[Number, Number]
MousePos: TypeAlias = tuple[int, int]
PanelWidget: TypeAlias = (
    "PanelParticle | PanelRod | PanelPlane | PremadeWorld | AttributeEditor | ForceWindow"
)

class Panel:
    __slots__ = (
        "_start",
        "__dimensions",
        "widgets",
        "rect",
        "_surface"
    )

    def __init__(
        self,
        start: Point,
        dimensions: Dimensions,
        widgets: list[PanelWidget]
    ) -> None:
        self._start: Point = start
        self.__dimensions: Dimensions = dimensions
        self.widgets: list[PanelWidget] = widgets

        self.rect: pygame.Rect = pygame.Rect(self._start, self.__dimensions)
        self._surface: pygame.Surface = pygame.Surface(self.__dimensions, pygame.SRCALPHA)
    
    def draw(
        self,
        sim: "Simulation"
    ) -> None:
        pygame.draw.rect(
            self._surface,
            UI_COLOUR_PANEL_BG,
            self._surface.get_rect(),
            border_radius=PANEL_CORNER_RADIUS
        )
        sim.screen.blit(self._surface, self._start)
        for widget in self.widgets:
            widget.draw(sim.screen, sim.label_font)
    
    def handle_click(
        self,
        sim: "Simulation",
        mouse_pos: MousePos
    ) -> None:
        if self.rect.collidepoint(mouse_pos):
            sim.selection_state.deselect_objects()
            for widget in self.widgets:
                widget.handle_click(sim, mouse_pos)
                if sim.selection_state.click_handled: return

class ParticleBottomPanel(Panel):
    __slots__ = ()

    def draw(
        self,
        sim: "Simulation"
    ) -> None:
        if sim.selection_state.selected_particle:
            pygame.draw.rect(
                self._surface,
                UI_COLOUR_PANEL_BG,
                self._surface.get_rect(),
                border_radius=PANEL_CORNER_RADIUS
            )
            sim.screen.blit(self._surface, self._start)

            for widget in self.widgets:
                widget.draw(sim.screen, sim.selection_state.selected_particle, sim.input_state.val, sim.box_font, sim.label_font)

    def handle_click(
        self,
        sim: "Simulation",
        mouse_pos: MousePos
    ) -> None:
        if sim.selection_state.selected_particle and self.rect.collidepoint(mouse_pos):
            for widget in self.widgets:
                widget.handle_click(sim, mouse_pos)
                if sim.selection_state.click_handled: return
            sim.selection_state.click_handled = True

    def handle_scroll(
        self,
        sim: "Simulation",
        scroll_direction: int,
        mouse_pos: MousePos
    ) -> None:
        for widget in self.widgets:
            if hasattr(widget, "scroll"):
                widget.scroll(sim, mouse_pos, scroll_direction)
                if sim.scroll_handled:
                    return

    def update_attribute(
        self,
        ui: "Simulation",
        body: "Particle"
    ) -> None:
        if ui.input_state.user_input['value_to_update'] == 'acting_forces':
            self.widgets[1].update_attribute(ui, body)
        else:
            self.widgets[0].update_attribute(ui, body)

class PlaneBottomPanel(Panel):
    __slots__ = ()

    def draw(
        self,
        sim: "Simulation"
    ) -> None:
        if sim.selection_state.selected_plane:
            pygame.draw.rect(
                self._surface,
                UI_COLOUR_PANEL_BG,
                self._surface.get_rect(),
                border_radius=PANEL_CORNER_RADIUS
            )
            sim.screen.blit(self._surface, self._start)

            for widget in self.widgets:
                widget.draw(sim.screen, sim.selection_state.selected_plane, sim.input_state.val, sim.box_font, sim.label_font)

    def handle_click(
        self,
        sim: "Simulation",
        mouse_pos: MousePos
    ) -> None:
        if sim.selection_state.selected_plane and self.rect.collidepoint(mouse_pos):
            for widget in self.widgets:
                widget.handle_click(sim, mouse_pos)
                if sim.selection_state.click_handled: return
            sim.selection_state.click_handled = True

    def update_attribute(
        self,
        ui: "Simulation",
        body: "Plane"
    ) -> None:
        self.widgets[0].update_attribute(ui, body)

class RightPanel(Panel):
    __slots__ = ()

    def draw(
        self,
        sim: "Simulation"
    ) -> None:
        pygame.draw.rect(
                        self._surface,
                        UI_COLOUR_PANEL_BG,
                        self._surface.get_rect(),
                        border_radius=PANEL_CORNER_RADIUS
                    )
        sim.screen.blit(self._surface, self._start)

        for widget in self.widgets:
            widget.draw(sim.screen, sim.world, sim.input_state.val, sim.box_font, sim.label_font)

    def update_attribute(
        self,
        ui: "Simulation"
    ) -> None:
        self.widgets[0].update_attribute(ui, ui.world)