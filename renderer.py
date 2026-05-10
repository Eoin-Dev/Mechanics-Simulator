from __future__ import annotations
from typing import TYPE_CHECKING

from physics.quadtree import draw_quadtree_bounds

if TYPE_CHECKING:
    from simulator.sim import Simulation

class Renderer:
    __slots__ = ()

    def draw(
        self,
        sim: "Simulation"
    ) -> None:
        sim.world.delete_and_draw(
            sim.screen,
            sim.screen_w,
            sim.screen_h,
            (sim.max_x, sim.max_y),
            sim.scale.zoom,
            sim.selection_state.selected_particle,
            sim.selection_state.selected_plane,
            sim.selection_state.selected_rod
        )

        # Draw the dragging item.
        if sim.selection_state.dragging_particle and not sim.selection_state.selected_rod:
            sim.selection_state.dragging_particle.draw(sim.screen, sim.screen_w, sim.screen_h, sim.scale.zoom)
        elif sim.selection_state.dragging_particle and sim.selection_state.selected_rod:
            sim.selection_state.selected_rod.draw(sim.screen, sim.screen_w, sim.screen_h, sim.scale.zoom)
        elif sim.selection_state.dragging_rod:
            sim.selection_state.dragging_rod.draw(sim.screen, sim.screen_w, sim.screen_h, sim.scale.zoom)
        elif sim.selection_state.dragging_plane:
            sim.selection_state.dragging_plane.draw(sim.screen, sim.screen_w, sim.screen_h, sim.scale.zoom)

        if sim.show_quadtree_bounds and sim.world.last_quadtree is not None:
            draw_quadtree_bounds(sim.screen, sim.world.last_quadtree, sim.screen_w, sim.screen_h, sim.scale.zoom)

        for item in sim.ui_items:
            item.draw(sim)