from __future__ import annotations

import pygame
from typing import TypeAlias

Colour: TypeAlias = str | tuple[int, int, int]
FontType: TypeAlias = pygame.font.Font

def pygame_write(
    surface: pygame.Surface,
    txt: str,
    font: FontType,
    pos_rect: pygame.Rect,
    txt_in_middle: bool,
    colour: Colour
) -> None:
    text_img = font.render(txt, True, colour)
    if txt_in_middle:
        text_rect = text_img.get_rect(center=pos_rect.center)
    else:
        text_rect = text_img.get_rect(
            midright=(pos_rect.right-5, pos_rect.centery)
        )
    surface.blit(text_img, text_rect)