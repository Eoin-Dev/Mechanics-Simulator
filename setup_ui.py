from __future__ import annotations
from typing import TypeAlias
import pygame
from random import choice, uniform

from physics.world import World
from physics.bodies import Plane, Particle
from physics.vector import Vector
from physics.constants import (
    PREMADE_WORLD_CONFIGS,
    PREMADE_WORLD_GRAVITY,
    PREMADE_WORLD_PARTICLE_MASS_MAX,
    PREMADE_WORLD_PARTICLE_MASS_MIN,
    PREMADE_WORLD_PARTICLE_RADIUS_DIVISOR,
    PREMADE_WORLD_PARTICLE_VELOCITY_MAX,
    PREMADE_WORLD_PARTICLE_VELOCITY_MIN
)

from ui_elements.panels import Panel, ParticleBottomPanel, PlaneBottomPanel, RightPanel
from ui_elements.widgets import AttributeEditor, ForceWindow, PanelParticle, PanelRod, PanelPlane, PremadeWorld
from ui_elements.input_boxes import InputBox
from ui_elements.play_controls import PlayButton, TimeController, DeleteButton
from ui_elements.metrics import FPS, Scale, CollisionModeDisplay
from simulator.constants import (
    BOTTOM_PANEL_FIELD_X_STEP_1,
    BOTTOM_PANEL_FIELD_X_STEP_2,
    BOTTOM_PANEL_FIELD_X_STEP_3,
    BOTTOM_PANEL_FIELD_X_STEP_4,
    BOTTOM_PANEL_HEIGHT_RATIO,
    BOTTOM_PANEL_TOP_RATIO,
    BOTTOM_PANEL_Y_OFFSET,
    COLOURS,
    FORCE_WINDOW_HEIGHT_RATIO,
    FORCE_WINDOW_WIDTH_OFFSET,
    FORCE_WINDOW_X_OFFSET,
    FORCE_WINDOW_Y_OFFSET,
    FPS_INITIAL_CAP,
    INPUT_BOX_HEIGHT_RATIO,
    INPUT_BOX_VERTICAL_GAP_RATIO,
    INPUT_BOX_WIDTH_RATIO,
    INPUT_BOX_X_DIVISOR,
    INPUT_BOX_Y_OFFSET,
    LEFT_PANEL_HEIGHT_RATIO,
    LEFT_PANEL_ICON_RADIUS_X_FACTOR,
    LEFT_PANEL_ICON_RADIUS_Y_FACTOR,
    LEFT_PANEL_MIN_THICKNESS_PX,
    LEFT_PANEL_PARTICLE_RADIUS_RATIO,
    LEFT_PANEL_PLANE_THICKNESS_RATIO,
    LEFT_PANEL_ROD_PARTICLE_RADIUS_RATIO,
    LEFT_PANEL_START_X,
    LEFT_PANEL_START_Y,
    LEFT_PANEL_WIDGET_X_CENTER,
    LEFT_PANEL_WIDGET_Y_PARTICLE,
    LEFT_PANEL_WIDGET_Y_PLANE,
    LEFT_PANEL_WIDGET_Y_ROD,
    LEFT_PANEL_WIDTH_RATIO,
    METRICS_FONT_HEIGHT_RATIO,
    METRICS_FPS_HEIGHT_RATIO,
    METRICS_FPS_POS_X_RATIO,
    METRICS_FPS_POS_Y_RATIO,
    METRICS_FPS_WIDTH_RATIO,
    METRICS_MODE_HEIGHT_RATIO,
    METRICS_MODE_POS_X_RATIO,
    METRICS_MODE_POS_Y_RATIO,
    METRICS_MODE_WIDTH_RATIO,
    METRICS_SCALE_POS_X_RATIO,
    METRICS_SCALE_POS_Y_RATIO,
    METRICS_SCALE_TEXT_X_RATIO,
    METRICS_SCALE_TEXT_Y_RATIO,
    METRICS_SCALE_TIP_END_Y_RATIO,
    METRICS_SCALE_ZOOM_DEFAULT,
    METRICS_SCALE_ZOOM_MAX,
    METRICS_SCALE_ZOOM_MIN,
    NEW_PARTICLE_RADIUS,
    NEW_PLANE_LENGTH_RATIO,
    NEW_ROD_LENGTH_RATIO,
    PLAY_BUTTON_CENTER_X_RATIO,
    PLAY_BUTTON_HEIGHT_RATIO,
    PLAY_BUTTON_WIDTH_RATIO,
    RIGHT_BOTTOM_PANEL_Y_MULTIPLIER,
    RIGHT_TOP_PANEL_E_Y_RATIO,
    RIGHT_TOP_PANEL_G_Y_RATIO,
    RIGHT_PANEL_HEIGHT_RATIO,
    RIGHT_PANEL_START_X_RATIO,
    RIGHT_PANEL_START_Y_RATIO,
    RIGHT_PANEL_WIDTH_RATIO,
    TIME_CONTROL_WIDTH_SCALE,
    TIME_CONTROL_X_SCALE,
    TIME_FIELD_NAME,
    UI_COLOUR_BOTTOM_PANEL_INPUT_ACTIVE,
    UI_COLOUR_BOTTOM_PANEL_INPUT_BOX,
    UI_COLOUR_BOTTOM_PANEL_INPUT_LABEL,
    UI_COLOUR_BOTTOM_PANEL_INPUT_TEXT,
    UI_COLOUR_FORCE_WINDOW,
    UI_COLOUR_PANEL_INPUT_ACTIVE,
    UI_COLOUR_PANEL_INPUT_BOX,
    UI_COLOUR_PANEL_INPUT_LABEL,
    UI_COLOUR_PANEL_INPUT_TEXT,
    UI_COLOUR_PANEL_PARTICLE,
    UI_COLOUR_PANEL_PLANE,
    UI_COLOUR_PANEL_ROD,
    UI_COLOUR_PANEL_ROD_PARTICLE,
    UI_COLOUR_TIME_ACTIVE,
    UI_TEXT_ACCELERATION,
    UI_TEXT_END,
    UI_TEXT_GRAVITY,
    UI_TEXT_MASS,
    UI_TEXT_POSITION,
    UI_TEXT_PREMADE_WORLD_PREFIX,
    UI_TEXT_RADIUS,
    UI_TEXT_RESTITUTION,
    UI_TEXT_START,
    UI_TEXT_THICKNESS,
    UI_TEXT_VELOCITY,
    DELETE_BUTTON_X_OFFSET_RATIO,
    DELETE_BUTTON_Y_SCALE,
    DELETE_BUTTON_WIDTH_SCALE,
    DELETE_BUTTON_HEIGHT_SCALE
)

Number: TypeAlias = int | float
Point: TypeAlias = tuple[Number, Number]
Dimensions: TypeAlias = tuple[Number, Number]
FontType: TypeAlias = pygame.font.Font
EditableItem: TypeAlias = Particle | Plane | World

def create_particle_bottom_panel(
    screen_w: Number,
    screen_h: Number
) -> ParticleBottomPanel:
    start, dimensions = _create_bottom_panel_start_and_dimensions(screen_w, screen_h)
    input_box_w, input_box_h, box_x, x_box_y, y_box_y = _create_input_box_values(screen_w, screen_h)

    force_box_x = box_x + BOTTOM_PANEL_FIELD_X_STEP_4 * screen_w
    force_window_x = force_box_x - screen_w * FORCE_WINDOW_X_OFFSET
    force_window_y = x_box_y - screen_h * FORCE_WINDOW_Y_OFFSET
    force_window_w = input_box_w + screen_w * FORCE_WINDOW_WIDTH_OFFSET
    
    input_boxes = {
        'mass':[
            InputBox(box_x, x_box_y, input_box_w, input_box_h, UI_COLOUR_BOTTOM_PANEL_INPUT_BOX, UI_TEXT_MASS, False, UI_COLOUR_BOTTOM_PANEL_INPUT_LABEL, active_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_ACTIVE, text_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_TEXT)
        ],
        'radius':[
            InputBox(box_x, y_box_y, input_box_w, input_box_h, UI_COLOUR_BOTTOM_PANEL_INPUT_BOX, UI_TEXT_RADIUS, False, UI_COLOUR_BOTTOM_PANEL_INPUT_LABEL, active_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_ACTIVE, text_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_TEXT)
        ],
        'position':[
            InputBox(box_x + (screen_w * BOTTOM_PANEL_FIELD_X_STEP_1), x_box_y, input_box_w, input_box_h, UI_COLOUR_BOTTOM_PANEL_INPUT_BOX, UI_TEXT_POSITION, True, UI_COLOUR_BOTTOM_PANEL_INPUT_LABEL, active_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_ACTIVE, text_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_TEXT),
            InputBox(box_x + (screen_w * BOTTOM_PANEL_FIELD_X_STEP_1), y_box_y, input_box_w, input_box_h, UI_COLOUR_BOTTOM_PANEL_INPUT_BOX, None, False, active_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_ACTIVE, text_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_TEXT)
        ],
        'velocity':[
            InputBox(box_x + (screen_w * BOTTOM_PANEL_FIELD_X_STEP_2), x_box_y, input_box_w, input_box_h, UI_COLOUR_BOTTOM_PANEL_INPUT_BOX, UI_TEXT_VELOCITY, True, UI_COLOUR_BOTTOM_PANEL_INPUT_LABEL, active_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_ACTIVE, text_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_TEXT),
            InputBox(box_x + (screen_w * BOTTOM_PANEL_FIELD_X_STEP_2), y_box_y, input_box_w, input_box_h, UI_COLOUR_BOTTOM_PANEL_INPUT_BOX, None, False, active_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_ACTIVE, text_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_TEXT)
        ],
        'user_acceleration':[
            InputBox(box_x + (screen_w * BOTTOM_PANEL_FIELD_X_STEP_3), x_box_y, input_box_w, input_box_h, UI_COLOUR_BOTTOM_PANEL_INPUT_BOX, UI_TEXT_ACCELERATION, True, UI_COLOUR_BOTTOM_PANEL_INPUT_LABEL, active_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_ACTIVE, text_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_TEXT),
            InputBox(box_x + (screen_w * BOTTOM_PANEL_FIELD_X_STEP_3), y_box_y, input_box_w, input_box_h, UI_COLOUR_BOTTOM_PANEL_INPUT_BOX, None, False, active_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_ACTIVE, text_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_TEXT)
        ]
    }
    
    attribute_rules = {
        'mass': {
            'constraint': lambda x: 0 < x <= 9999999,
            'action': lambda item: setattr(item, "mass_changed", True)
        },
        'radius': {
            'constraint': lambda x: 0 < x <= 500,
            'action': lambda _: None
        },
        'position': {
            'constraint': lambda x: -1000 <= x <= 1000,
            'action': lambda _: None
        },
        'velocity': {
            'constraint': lambda x: -10000 <= x <= 10000,
            'action': lambda _: None
        },
        'user_acceleration': {
            'constraint': lambda x: -10000 <= x <= 10000,
            'action': lambda item: setattr(item, "acceleration_changed", True)
        }
    }
    
    widgets = [
        AttributeEditor(input_boxes, attribute_rules),
        ForceWindow((force_window_x, force_window_y), (force_window_w, FORCE_WINDOW_HEIGHT_RATIO * screen_h), UI_COLOUR_FORCE_WINDOW, {}, input_box_w, input_box_h)
        ]

    return ParticleBottomPanel(start, dimensions, widgets)

def create_plane_bottom_panel(
    screen_w: Number,
    screen_h: Number
) -> PlaneBottomPanel:
    start, dimensions = _create_bottom_panel_start_and_dimensions(screen_w, screen_h)
    input_box_w, input_box_h, box_x, x_box_y, y_box_y = _create_input_box_values(screen_w, screen_h)
    
    input_boxes = {
        'start':[
            InputBox(box_x, x_box_y, input_box_w, input_box_h, UI_COLOUR_BOTTOM_PANEL_INPUT_BOX, UI_TEXT_START, True, UI_COLOUR_BOTTOM_PANEL_INPUT_LABEL, active_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_ACTIVE, text_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_TEXT),
            InputBox(box_x, y_box_y, input_box_w, input_box_h, UI_COLOUR_BOTTOM_PANEL_INPUT_BOX, None, False, active_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_ACTIVE, text_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_TEXT)
        ],
        'end':[
            InputBox(box_x + (screen_w * BOTTOM_PANEL_FIELD_X_STEP_2), x_box_y, input_box_w, input_box_h, UI_COLOUR_BOTTOM_PANEL_INPUT_BOX, UI_TEXT_END, True, UI_COLOUR_BOTTOM_PANEL_INPUT_LABEL, active_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_ACTIVE, text_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_TEXT),
            InputBox(box_x + (screen_w * BOTTOM_PANEL_FIELD_X_STEP_2), y_box_y, input_box_w, input_box_h, UI_COLOUR_BOTTOM_PANEL_INPUT_BOX, None, False, active_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_ACTIVE, text_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_TEXT)
        ],
        'thickness':[
            InputBox(box_x + (screen_w * BOTTOM_PANEL_FIELD_X_STEP_4), x_box_y, input_box_w, input_box_h, UI_COLOUR_BOTTOM_PANEL_INPUT_BOX, UI_TEXT_THICKNESS, False, UI_COLOUR_BOTTOM_PANEL_INPUT_LABEL, active_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_ACTIVE, text_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_TEXT)
        ],
        'e':[
            InputBox(box_x + (screen_w * BOTTOM_PANEL_FIELD_X_STEP_4), y_box_y, input_box_w, input_box_h, UI_COLOUR_BOTTOM_PANEL_INPUT_BOX, UI_TEXT_RESTITUTION, False, UI_COLOUR_BOTTOM_PANEL_INPUT_LABEL, active_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_ACTIVE, text_colour=UI_COLOUR_BOTTOM_PANEL_INPUT_TEXT)
        ]
    }
    
    attribute_rules = {
        'start': {
            'constraint': lambda x: -1000 <= x <= 1000,
            'action': lambda item: item.refresh_geometry()
        },
        'end': {
            'constraint': lambda x: -1000 <= x <= 1000,
            'action': lambda item: item.refresh_geometry()
        },
        'thickness': {
            'constraint': lambda x: 0 < x <= 250,
            'action': lambda item: item.refresh_geometry()
        },
        'e': {
            'constraint': lambda x: 0 <= x <= 1,
            'action': lambda _: None
        }
    }

    widgets = [
        AttributeEditor(input_boxes, attribute_rules)
    ]

    return PlaneBottomPanel(start, dimensions, widgets)

def create_left_side_panel(
    screen_w: Number,
    screen_h: Number
) -> Panel:
    start = (LEFT_PANEL_START_X, LEFT_PANEL_START_Y)
    dimensions = LEFT_PANEL_WIDTH_RATIO * screen_w, LEFT_PANEL_HEIGHT_RATIO * screen_h

    panel_particle_pos = (
        dimensions[0] * LEFT_PANEL_WIDGET_X_CENTER + LEFT_PANEL_START_X,
        dimensions[1] * LEFT_PANEL_WIDGET_Y_PARTICLE + LEFT_PANEL_START_Y
    )
    panel_particle_radius = screen_h * LEFT_PANEL_PARTICLE_RADIUS_RATIO

    panel_rod_start = (
        dimensions[0] * LEFT_PANEL_WIDGET_X_CENTER + LEFT_PANEL_START_X - panel_particle_radius * LEFT_PANEL_ICON_RADIUS_X_FACTOR,
        dimensions[1] * LEFT_PANEL_WIDGET_Y_ROD + LEFT_PANEL_START_Y - panel_particle_radius * LEFT_PANEL_ICON_RADIUS_Y_FACTOR
    )
    panel_rod_end = (
        dimensions[0] * LEFT_PANEL_WIDGET_X_CENTER + LEFT_PANEL_START_X + panel_particle_radius * LEFT_PANEL_ICON_RADIUS_X_FACTOR,
        dimensions[1] * LEFT_PANEL_WIDGET_Y_ROD + LEFT_PANEL_START_Y + panel_particle_radius * LEFT_PANEL_ICON_RADIUS_Y_FACTOR
    )
    panel_rod_particle_radius = screen_h * LEFT_PANEL_ROD_PARTICLE_RADIUS_RATIO
    new_rod_length = screen_w * NEW_ROD_LENGTH_RATIO

    panel_plane_start = (
        dimensions[0] * LEFT_PANEL_WIDGET_X_CENTER + LEFT_PANEL_START_X - panel_particle_radius * LEFT_PANEL_ICON_RADIUS_X_FACTOR,
        dimensions[1] * LEFT_PANEL_WIDGET_Y_PLANE + LEFT_PANEL_START_Y - panel_particle_radius * LEFT_PANEL_ICON_RADIUS_Y_FACTOR
    )
    panel_plane_end = (
        dimensions[0] * LEFT_PANEL_WIDGET_X_CENTER + LEFT_PANEL_START_X + panel_particle_radius * LEFT_PANEL_ICON_RADIUS_X_FACTOR,
        dimensions[1] * LEFT_PANEL_WIDGET_Y_PLANE + LEFT_PANEL_START_Y + panel_particle_radius * LEFT_PANEL_ICON_RADIUS_Y_FACTOR
    )
    panel_plane_thickness = max(int(screen_h * LEFT_PANEL_PLANE_THICKNESS_RATIO), LEFT_PANEL_MIN_THICKNESS_PX)
    new_plane_length = screen_w * NEW_PLANE_LENGTH_RATIO

    widgets = [
        PanelParticle(panel_particle_pos, panel_particle_radius, NEW_PARTICLE_RADIUS, UI_COLOUR_PANEL_PARTICLE),
        PanelRod(panel_rod_start, panel_rod_end, panel_rod_particle_radius, NEW_PARTICLE_RADIUS, new_rod_length, UI_COLOUR_PANEL_ROD_PARTICLE, UI_COLOUR_PANEL_ROD),
        PanelPlane(panel_plane_start, panel_plane_end, panel_plane_thickness, new_plane_length, UI_COLOUR_PANEL_PLANE)
    ]
    
    return Panel(start, dimensions, widgets)

def create_right_top_panel(
    screen_w: Number,
    screen_h: Number
) -> RightPanel:
    input_box_w, input_box_h, _, _, _ = _create_input_box_values(screen_w, screen_h)
    start, dimensions = _create_right_panel_start_and_dimensions(screen_w, screen_h)

    input_boxes = {
        'g': [
            InputBox(start[0] + (dimensions[0] - input_box_w)/2, start[1] + dimensions[1] * RIGHT_TOP_PANEL_G_Y_RATIO, input_box_w, input_box_h, UI_COLOUR_PANEL_INPUT_BOX, UI_TEXT_GRAVITY, True, UI_COLOUR_PANEL_INPUT_LABEL, active_colour=UI_COLOUR_PANEL_INPUT_ACTIVE, text_colour=UI_COLOUR_PANEL_INPUT_TEXT)
        ],
        'e': [
            InputBox(start[0] + (dimensions[0] - input_box_w)/2, start[1] + dimensions[1] * RIGHT_TOP_PANEL_E_Y_RATIO, input_box_w, input_box_h, UI_COLOUR_PANEL_INPUT_BOX, UI_TEXT_RESTITUTION, True, UI_COLOUR_PANEL_INPUT_LABEL, active_colour=UI_COLOUR_PANEL_INPUT_ACTIVE, text_colour=UI_COLOUR_PANEL_INPUT_TEXT)
        ]
    }

    attribute_rules = {
        'g': {
            'constraint': lambda x: -1000 <= x <= 1000,
            'action': lambda item: item.reset_all_force_flags()
        },
        'e': {
            'constraint': lambda x: 0 <= x <= 1,
            'action': lambda _: None
        }
    }

    widgets = [
        AttributeEditor(input_boxes, attribute_rules)
    ]

    return RightPanel(start, dimensions, widgets)

def create_right_bottom_panel(
    screen_w: Number,
    screen_h: Number
) -> Panel:
    start, dimensions = _create_right_panel_start_and_dimensions(screen_w, screen_h)
    
    start = start[0], start[1] * RIGHT_BOTTOM_PANEL_Y_MULTIPLIER

    worlds = [
        _create_box_world(length, no_of_particles)
        for length, no_of_particles in PREMADE_WORLD_CONFIGS
    ]

    no_of_worlds = len(worlds)

    dimensions = dimensions[0], dimensions[1]*no_of_worlds/4

    widgets = []
    for world in worlds:
        widgets.append(
            PremadeWorld(
                world,
                (start[0], start[1] + dimensions[1] * len(widgets) / no_of_worlds),
                (dimensions[0], dimensions[1] / no_of_worlds),
                f'{UI_TEXT_PREMADE_WORLD_PREFIX} {len(widgets) + 1}'
            )
        )

    return Panel(start, dimensions, widgets)

def _create_box_world(
    length: Number,
    no_of_particles: int
) -> World:
    world = World()
    world.g = PREMADE_WORLD_GRAVITY

    plane_colour = choice(COLOURS)
    corners = [
        Vector(-length/2,  length/2),
        Vector( length/2,  length/2),
        Vector( length/2, -length/2),
        Vector(-length/2, -length/2)
    ]
    for i in range(4):
        tip1 = corners[(i + 1) % 4]
        tip2 = corners[i]
        world.static_bodies.append(
            Plane(plane_colour, plane_colour, tip1, tip2)
        )

    for i in range(no_of_particles):
        colour = choice(COLOURS)
        mass = round(uniform(PREMADE_WORLD_PARTICLE_MASS_MIN, PREMADE_WORLD_PARTICLE_MASS_MAX), 4)
        rad = round(mass / PREMADE_WORLD_PARTICLE_RADIUS_DIVISOR, 4)
        p = Particle(
            mass,
            colour,
            colour,
            Vector(
                uniform(-length/2 + rad, length/2 - rad),
                uniform(-length/2 + rad, length/2 - rad)
            ),
            rad
        )
        p.velocity = Vector(
            uniform(PREMADE_WORLD_PARTICLE_VELOCITY_MIN, PREMADE_WORLD_PARTICLE_VELOCITY_MAX),
            uniform(PREMADE_WORLD_PARTICLE_VELOCITY_MIN, PREMADE_WORLD_PARTICLE_VELOCITY_MAX)
        )
        world.dynamic_bodies.append(p)

    return world

def create_metrics(
    screen_w: Number,
    screen_h: Number
) -> tuple[FPS, Scale, CollisionModeDisplay]:
    fps_pos = screen_w * METRICS_FPS_POS_X_RATIO, screen_h * METRICS_FPS_POS_Y_RATIO
    fps_dimensions = screen_w * METRICS_FPS_WIDTH_RATIO, screen_h * METRICS_FPS_HEIGHT_RATIO
    fps_cap = FPS_INITIAL_CAP
    
    scale_pos = screen_w * METRICS_SCALE_POS_X_RATIO, screen_h * METRICS_SCALE_POS_Y_RATIO
    txt_pos = screen_w * METRICS_SCALE_TEXT_X_RATIO, screen_h * METRICS_SCALE_TEXT_Y_RATIO
    tip_end_y = scale_pos[1] * METRICS_SCALE_TIP_END_Y_RATIO
    zoom = METRICS_SCALE_ZOOM_DEFAULT
    min_zoom = METRICS_SCALE_ZOOM_MIN
    max_zoom = METRICS_SCALE_ZOOM_MAX

    mode_pos = screen_w * METRICS_MODE_POS_X_RATIO, screen_h * METRICS_MODE_POS_Y_RATIO
    mode_dimensions = screen_w * METRICS_MODE_WIDTH_RATIO, screen_h * METRICS_MODE_HEIGHT_RATIO

    font = pygame.font.SysFont(None, int(round(screen_h * METRICS_FONT_HEIGHT_RATIO, 0)))

    return (
        FPS(fps_pos, fps_dimensions, font, fps_cap),
        Scale(scale_pos, txt_pos, tip_end_y, zoom, min_zoom, max_zoom, font),
        CollisionModeDisplay(mode_pos, mode_dimensions, font)
    )

def _create_input_box_values(
    screen_w: Number,
    screen_h: Number
) -> tuple[float, float, float, float, float]:
    input_box_w = INPUT_BOX_WIDTH_RATIO * screen_w
    input_box_h = INPUT_BOX_HEIGHT_RATIO * screen_h

    box_x = (screen_w / INPUT_BOX_X_DIVISOR) - (input_box_w / 2)
    x_box_y = ((1 + BOTTOM_PANEL_TOP_RATIO) / 2 * screen_h + INPUT_BOX_Y_OFFSET) - input_box_h
    y_box_y = x_box_y + input_box_h * INPUT_BOX_VERTICAL_GAP_RATIO

    return input_box_w, input_box_h, box_x, x_box_y, y_box_y

def _create_bottom_panel_start_and_dimensions(
    screen_w: Number,
    screen_h: Number
) -> tuple[Point, Dimensions]:
    start = (0, (BOTTOM_PANEL_TOP_RATIO * screen_h) + BOTTOM_PANEL_Y_OFFSET)
    dimensions = (screen_w, BOTTOM_PANEL_HEIGHT_RATIO * screen_h)

    return start, dimensions

def _create_right_panel_start_and_dimensions(
    screen_w: Number,
    screen_h: Number
) -> tuple[Point, Dimensions]:
    start = screen_w * RIGHT_PANEL_START_X_RATIO, screen_h * RIGHT_PANEL_START_Y_RATIO
    dimensions = screen_w * RIGHT_PANEL_WIDTH_RATIO, screen_h * RIGHT_PANEL_HEIGHT_RATIO

    return start, dimensions

def create_play_controls(
    screen_w: Number,
    screen_h: Number
) -> tuple[DeleteButton, PlayButton, TimeController]:
    _, bottom_panel_dimensions = _create_bottom_panel_start_and_dimensions(screen_w, screen_h)
    input_box_w, input_box_h, _, _, _ = _create_input_box_values(screen_w, screen_h)

    play_button_width = screen_w * PLAY_BUTTON_WIDTH_RATIO
    play_button_height = screen_h * PLAY_BUTTON_HEIGHT_RATIO
    play_button_x = (screen_w - play_button_width) * PLAY_BUTTON_CENTER_X_RATIO
    play_button_y = screen_h - bottom_panel_dimensions[1] - play_button_height

    time_control_x = play_button_x * TIME_CONTROL_X_SCALE
    time_control_y = play_button_y
    time_control_box_width = input_box_w * TIME_CONTROL_WIDTH_SCALE
    
    return (
        DeleteButton(
            UI_COLOUR_PANEL_INPUT_TEXT,
            play_button_x + screen_w * DELETE_BUTTON_X_OFFSET_RATIO,
            play_button_y * DELETE_BUTTON_Y_SCALE,
            play_button_width * DELETE_BUTTON_WIDTH_SCALE,
            play_button_height * DELETE_BUTTON_HEIGHT_SCALE
        ),
        PlayButton(UI_COLOUR_PANEL_INPUT_TEXT, play_button_x, play_button_y, play_button_width, play_button_height),
        TimeController(
            time_control_x,
            time_control_y,
            time_control_box_width,
            input_box_h,
            UI_COLOUR_PANEL_INPUT_BOX,
            TIME_FIELD_NAME,
            False,
            UI_COLOUR_PANEL_INPUT_TEXT,
            False,
            UI_COLOUR_TIME_ACTIVE
        )
        )

def create_fonts(
    screen_w: Number,
    screen_h: Number
) -> tuple[FontType, FontType]:
    _, input_box_h, _, _, _ = _create_input_box_values(screen_w, screen_h)

    text_height = int(round(input_box_h * 1.23,0))

    box_font = pygame.font.SysFont(None, text_height)
    label_font = pygame.font.SysFont(None, text_height)

    return box_font, label_font