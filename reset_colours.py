from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simulator.sim import Simulation

def reset_object_colours(
    sim: "Simulation"
) -> None:
    if sim.selection_state.selected_particle:
        sim.selection_state.selected_particle.colour = sim.selection_state.selected_particle.base_colour

    elif sim.selection_state.selected_rod:
        sim.selection_state.selected_rod.colour = sim.selection_state.selected_rod.base_colour
        
    elif sim.selection_state.selected_plane:
        sim.selection_state.selected_plane.colour = sim.selection_state.selected_plane.base_colour