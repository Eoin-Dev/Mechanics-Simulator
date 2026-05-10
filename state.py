from __future__ import annotations
from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from physics.bodies import Particle, Plane, Rod
    from ui_elements.input_boxes import InputBox
    from ui_elements.play_controls import TimeController

UserInputState: TypeAlias = dict[str, str | int | None]
SelectedBoxItem: TypeAlias = "InputBox | TimeController"

class SelectionState:
    __slots__ = (
        "selected_particle",
        "selected_rod",
        "selected_plane",
        "dragging_particle",
        "dragging_rod",
        "dragging_plane",
        "click_handled"
    )

    def __init__(
        self
    ) -> None:
        self.selected_particle: Particle | None = None
        self.selected_rod: Rod | None = None
        self.selected_plane: Plane | None = None

        self.dragging_particle: Particle | None = None
        self.dragging_rod: Rod | None = None
        self.dragging_plane: Plane | None = None

        self.click_handled: bool = False

    def deselect_objects(
        self
    ) -> None:
        if self.selected_particle:
            self.selected_particle.colour = self.selected_particle.base_colour
            self.selected_particle = None

        if self.selected_rod:
            self.selected_rod.colour = self.selected_rod.base_colour
            self.selected_rod = None

        if self.selected_plane:
            self.selected_plane.colour = self.selected_plane.base_colour
            self.selected_plane = None

class InputState:
    __slots__ = (
        "selected_box",
        "val",
        "user_input"
    )

    def __init__(
        self
    ) -> None:
        self.selected_box: SelectedBoxItem | None = None
        self.val: str = ""
        self.user_input: UserInputState = {
            "value_to_update": None,
            "vector_component": None,
            "force_index": None
        }

    def deselect_box(
        self
    ) -> None:
        if self.selected_box:
            self.selected_box.colour = self.selected_box.inactive_colour

        self.selected_box = None
        self.val = ""
        self.user_input = {
            "value_to_update": None,
            "vector_component": None,
            "force_index": None
        }