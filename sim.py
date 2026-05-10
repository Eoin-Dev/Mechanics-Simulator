from __future__ import annotations
from typing import TypeAlias
import pygame

from physics.constants import PHYSICS_DT, WORLD_BOUNDS_MARGIN
from physics.world import World

from ui_elements.input_boxes import InputBox
from ui_elements.metrics import CollisionModeDisplay, FPS, Scale
from ui_elements.panels import Panel, ParticleBottomPanel, PlaneBottomPanel, RightPanel
from ui_elements.play_controls import DeleteButton, PlayButton, TimeController
from ui_elements.setup_ui import create_particle_bottom_panel, create_plane_bottom_panel, create_left_side_panel, create_right_top_panel, create_right_bottom_panel, create_play_controls, create_fonts, create_metrics

from simulator.input_handler import InputHandler
from simulator.interaction_handler import InteractionHandler
from simulator.renderer import Renderer
from simulator.state import InputState, SelectionState
from simulator.world_updater import WorldUpdater
from simulator.constants import (
    UI_COLOUR_BACKGROUND,
    WINDOW_HEIGHT,
    WINDOW_TITLE,
    WINDOW_WIDTH
)

from utils.coord_conversion import to_cartesian

MousePos: TypeAlias = tuple[int, int]
UiItem: TypeAlias = (
    Panel
    | ParticleBottomPanel
    | PlaneBottomPanel
    | RightPanel
    | DeleteButton
    | PlayButton
    | TimeController
    | FPS
    | Scale
    | CollisionModeDisplay
)
ClickableUiItem: TypeAlias = (
    Panel
    | ParticleBottomPanel
    | PlaneBottomPanel
    | RightPanel
    | DeleteButton
    | PlayButton
    | TimeController
)
ScrollableUiItem: TypeAlias = ParticleBottomPanel | Scale
ForceInputBoxesState: TypeAlias = dict[int, list[InputBox]]
FontType: TypeAlias = pygame.font.Font

class Simulation:
    __slots__ = (
        "screen_w",
        "screen_h",
        "screen",
        "particle_bottom_panel",
        "plane_bottom_panel",
        "left_side_panel",
        "right_top_panel",
        "__right_bottom_panel",
        "delete_button",
        "play_button",
        "time_control",
        "fps",
        "scale",
        "collision_mode_display",
        "ui_items",
        "box_font",
        "label_font",
        "running",
        "clock",
        "max_x",
        "max_y",
        "input_state",
        "selection_state",
        "__interaction_handler",
        "__input_handler",
        "__world_updater",
        "__renderer",
        "clickable_ui_items",
        "scrollable_ui_items",
        "scroll_handled",
        "world_at_start",
        "forces_boxes_at_start",
        "world",
        "dt_physics",
        "accumulator",
        "begin_sim",
        "show_quadtree_bounds"
    )

    def __init__(
        self
    ) -> None:
        self.screen_w: int = WINDOW_WIDTH
        self.screen_h: int = WINDOW_HEIGHT
        self.screen: pygame.Surface = pygame.display.set_mode((self.screen_w, self.screen_h))
        pygame.display.set_caption(WINDOW_TITLE)

        self.particle_bottom_panel = create_particle_bottom_panel(self.screen_w, self.screen_h)
        self.plane_bottom_panel = create_plane_bottom_panel(self.screen_w, self.screen_h)
        self.left_side_panel = create_left_side_panel(self.screen_w, self.screen_h)
        self.right_top_panel = create_right_top_panel(self.screen_w, self.screen_h)
        self.__right_bottom_panel = create_right_bottom_panel(self.screen_w, self.screen_h)
        self.delete_button, self.play_button, self.time_control, = create_play_controls(self.screen_w, self.screen_h)
        self.fps, self.scale, self.collision_mode_display = create_metrics(self.screen_w, self.screen_h)
        self.ui_items: list[UiItem] = [
            self.particle_bottom_panel,
            self.plane_bottom_panel,
            self.delete_button,
            self.time_control,
            self.play_button,
            self.left_side_panel,
            self.right_top_panel,
            self.__right_bottom_panel,
            self.fps,
            self.scale,
            self.collision_mode_display
        ]

        self.box_font: FontType
        self.label_font: FontType
        self.box_font, self.label_font = create_fonts(self.screen_w, self.screen_h)

        self.running: bool = True
        self.clock: pygame.time.Clock = pygame.time.Clock()

        max_corner = to_cartesian((self.screen_w, self.screen_h), self.screen_w, self.screen_h, self.scale.min_zoom)
        self.max_x: float = max_corner.x + WORLD_BOUNDS_MARGIN
        self.max_y: float = -max_corner.y + WORLD_BOUNDS_MARGIN

        self.input_state: InputState = InputState()
        self.selection_state: SelectionState = SelectionState()

        self.__interaction_handler: InteractionHandler = InteractionHandler()
        self.__input_handler: InputHandler = InputHandler(self.__interaction_handler)
        self.__world_updater: WorldUpdater = WorldUpdater()
        self.__renderer: Renderer = Renderer()

        self.clickable_ui_items: list[ClickableUiItem] = [
            self.particle_bottom_panel,
            self.plane_bottom_panel,
            self.delete_button,
            self.time_control,
            self.play_button,
            self.left_side_panel,
            self.right_top_panel,
            self.__right_bottom_panel
        ]

        self.scrollable_ui_items: list[ScrollableUiItem] = [
            self.particle_bottom_panel,
            self.scale
        ]
        self.scroll_handled: bool = False

        self.world_at_start: World | None = None
        self.forces_boxes_at_start: ForceInputBoxesState | None = None

        self.world: World = World()
        self.dt_physics: float = PHYSICS_DT
        self.accumulator: float = 0.0

        self.begin_sim: bool = False

        self.show_quadtree_bounds: bool = False

    def start(
        self
    ) -> None:
        while self.running:
            self.screen.fill(UI_COLOUR_BACKGROUND)
            dt_frame = self.clock.tick(self.fps.get_cap())/1000
            mouse_pos: MousePos = pygame.mouse.get_pos()

            self.__handle_events(mouse_pos)
            self.update_world(dt_frame)
            self.__render()

            pygame.display.flip() # Flip causes all changes to occur at once.

    def __handle_events(
            self,
            mouse_pos: MousePos
    ) -> None:
        self.__input_handler.handle_events(self, mouse_pos)

    def update_world(
        self,
        dt_frame: float
    ) -> None:
        self.__world_updater.update_world(self, dt_frame)
    
    def __render(
        self
    ) -> None:
        self.__renderer.draw(self)