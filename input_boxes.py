from __future__ import annotations
import pygame
from typing import TypeAlias

from simulator.constants import (
    INPUT_BOX_CORNER_RADIUS,
    INPUT_BOX_DELETE_SIZE_RATIO,
    INPUT_BOX_DELETE_X_SCALE,
    INPUT_BOX_DELETE_Y_OFFSET_RATIO,
    INPUT_BOX_ICON_LINE_THICKNESS,
    INPUT_BOX_SIDE_LABEL_Y_OFFSET_RATIO,
    UI_COLOUR_PANEL_INPUT_ACTIVE,
    UI_COLOUR_PANEL_INPUT_TEXT
)
from utils.draw_text import pygame_write

Number: TypeAlias = int | float
MousePos: TypeAlias = tuple[int, int]
Colour: TypeAlias = str | tuple[int, int, int]
FontType: TypeAlias = pygame.font.Font

class InputBox:
    __slots__ = (
        "__startx",
        "__starty",
        "__width",
        "__height",
        "colour",
        "inactive_colour",
        "__text_colour",
        "_label",
        "__label_on_top",
        "_label_colour",
        "_del_button",
        "_active_colour",
        "rect",
        "del_button_rect",
        "_label_rect",
        "_label_text_in_middle"
    )

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
        active_colour: Colour = UI_COLOUR_PANEL_INPUT_ACTIVE,
        text_colour: Colour = UI_COLOUR_PANEL_INPUT_TEXT
    ) -> None:
        self.__startx: Number = startx
        self.__starty: Number = starty
        self.__width: Number = width
        self.__height: Number = height
        self.colour: Colour = colour
        self.inactive_colour: Colour = colour
        self.__text_colour: Colour = text_colour
        self._label: str | None = label
        self.__label_on_top: bool = label_on_top
        self._label_colour: Colour | None = label_colour
        self._del_button: bool = del_button
        self._active_colour: Colour = active_colour

        self.rect: pygame.Rect = pygame.Rect(self.__startx, self.__starty, self.__width, self.__height)
        self.del_button_rect: pygame.Rect | None = None
        self._label_rect: pygame.Rect | None = None
        self._label_text_in_middle: bool | None = None
        if del_button:
            self.del_button_rect = pygame.Rect(
                self.__startx * INPUT_BOX_DELETE_X_SCALE,
                self.__starty + self.__height * INPUT_BOX_DELETE_Y_OFFSET_RATIO,
                self.__height * INPUT_BOX_DELETE_SIZE_RATIO,
                self.__height * INPUT_BOX_DELETE_SIZE_RATIO
            )
        
        if not self._label:
            pass
        else:
            self._label_rect = self.rect.copy()
            if self.__label_on_top:
                self._label_rect.y -= self.__height
                self._label_text_in_middle = True
            else:
                self._label_rect.x -= self.__width
                self._label_rect.y += self.__height * INPUT_BOX_SIDE_LABEL_Y_OFFSET_RATIO
                self._label_text_in_middle = False

    def offset(
        self,
        offsetx: Number,
        offsety: Number
    ) -> None:
        self.rect.move_ip(offsetx, offsety)

        if self._del_button and self.del_button_rect is not None:
            self.del_button_rect.move_ip(offsetx, offsety)

    def draw(
        self,
        surface: pygame.Surface,
        text: str,
        current_text: str,
        box_font: FontType,
        label_font: FontType | None = None
    ) -> None:
        pygame.draw.rect(surface,
                         self.colour,
                         self.rect,
                         0,
                         INPUT_BOX_CORNER_RADIUS)
        
        if self.colour == self._active_colour:
            pygame_write(
                surface, current_text, box_font,
                self.rect, 
                False,
                self.__text_colour
                )
        else:
            pygame_write(
                surface, text, box_font,
                self.rect, 
                False,
                self.__text_colour
                )
        
        if self._label and self._label_rect is not None and self._label_text_in_middle is not None:
            pygame_write(surface, self._label, label_font, self._label_rect, self._label_text_in_middle, self._label_colour)
        
        if self._del_button and self.del_button_rect is not None:
            pygame.draw.line(surface,
                             self.__text_colour,
                             self.del_button_rect.topleft,
                             self.del_button_rect.bottomright,
                             INPUT_BOX_ICON_LINE_THICKNESS)
            pygame.draw.line(surface,
                             self.__text_colour,
                             self.del_button_rect.topright,
                             self.del_button_rect.bottomleft,
                             INPUT_BOX_ICON_LINE_THICKNESS)
    
    def clicked(
        self,
        mouse_pos: MousePos
    ) -> bool:
        if self.rect.collidepoint(mouse_pos):
            self.colour = self._active_colour
            return True
        return False