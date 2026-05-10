from __future__ import annotations
import pygame
from typing import TYPE_CHECKING, TypeAlias

from simulator.constants import (
    METRICS_LINE_THICKNESS,
    METRICS_SCALE_LABEL_MIN_WIDTH,
    UI_COLOUR_PANEL_INPUT_TEXT,
    UI_TEXT_COLLISION_SUFFIX,
    UI_TEXT_SCALE
)
from utils.draw_text import pygame_write

if TYPE_CHECKING:
    from simulator.sim import Simulation

Number: TypeAlias = int | float
Point: TypeAlias = tuple[Number, Number]
Dimensions: TypeAlias = tuple[Number, Number]
FontType: TypeAlias = pygame.font.Font

class FPS:
    __slots__ = ("__rect", "__font", "__setfps")

    def __init__(
        self,
        pos: Point,
        dimensions: Dimensions,
        font: FontType,
        setfps: int
    ) -> None:
        self.__rect: pygame.Rect = pygame.Rect(pos, dimensions)
        self.__font: FontType = font
        self.__setfps: int = setfps
    
    def draw(
        self,
        sim: "Simulation"
    ) -> None:
        actual_fps = str(int(sim.clock.get_fps()))
        pygame_write(sim.screen, actual_fps, self.__font, self.__rect, True, UI_COLOUR_PANEL_INPUT_TEXT)

    def get_cap(
        self
    ) -> int:
        return self.__setfps

    def cycle_cap(
        self,
        step: int,
        max_cap: int
    ) -> None:
        if self.__setfps < max_cap:
            self.__setfps += step
        else:
            self.__setfps = 0

class Scale:
    __slots__ = (
        "__pos",
        "zoom",
        "min_zoom",
        "__max_zoom",
        "__font",
        "__tip_end_y",
        "__text_rect"
    )

    def __init__(
        self,
        pos: Point,
        txt_pos: Point,
        tip_end_y: Number,
        zoom: Number,
        min_zoom: Number,
        max_zoom: Number,
        font: FontType
    ) -> None:
        self.__pos: Point = pos
        self.zoom: float = float(zoom)
        self.min_zoom: float = float(min_zoom)
        self.__max_zoom: float = float(max_zoom)

        self.__font: FontType = font
        self.__tip_end_y: float = float(tip_end_y)
        self.__text_rect: pygame.Rect = pygame.Rect(
            pos[0] - zoom, txt_pos[1], zoom, txt_pos[1] - pos[1]
        )
    
    def draw(
        self,
        sim: "Simulation"
    ) -> None:
        pygame.draw.line(sim.screen, UI_COLOUR_PANEL_INPUT_TEXT,
                     self.__pos,
                     (self.__pos[0] - self.zoom, self.__pos[1]), METRICS_LINE_THICKNESS)
        pygame.draw.line(sim.screen, UI_COLOUR_PANEL_INPUT_TEXT,
                        self.__pos,
                        (self.__pos[0], self.__tip_end_y))
        pygame.draw.line(sim.screen, UI_COLOUR_PANEL_INPUT_TEXT,
                        (self.__pos[0] - self.zoom, self.__pos[1]),
                        (self.__pos[0] - self.zoom, self.__tip_end_y))
        self.__text_rect.x, self.__text_rect.width = min(self.__pos[0] - self.zoom, self.__pos[0] - METRICS_SCALE_LABEL_MIN_WIDTH), max(self.zoom, METRICS_SCALE_LABEL_MIN_WIDTH)
        pygame_write(sim.screen, UI_TEXT_SCALE, self.__font, self.__text_rect, True, UI_COLOUR_PANEL_INPUT_TEXT)
    
    def handle_scroll(
        self,
        sim: "Simulation",
        scroll_direction: int,
        mouse_pos: Point
    ) -> None:
        self.zoom *= 1.1 if scroll_direction > 0 else 0.9  # Zooming in and out
        # Limiting scaling
        if self.zoom < self.min_zoom: self.zoom = self.min_zoom
        elif self.zoom > self.__max_zoom: self.zoom = self.__max_zoom

        sim.scroll_handled = True

class CollisionModeDisplay:
    __slots__ = ("__rect", "__font")

    def __init__(
        self,
        start: Point,
        dimensions: Dimensions,
        font: FontType
    ) -> None:
        self.__rect: pygame.Rect = pygame.Rect(start, dimensions)
        self.__font: FontType = font

    def draw(
        self,
        sim: "Simulation"
    ) -> None:
        pygame_write(
            sim.screen,
            f"{sim.world.get_collision_mode()} {UI_TEXT_COLLISION_SUFFIX}",
            self.__font,
            self.__rect,
            True,
            UI_COLOUR_PANEL_INPUT_TEXT
        )