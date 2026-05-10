from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simulator.sim import Simulation

class WorldUpdater:
    __slots__ = ()

    def update_world(
        self,
        sim: "Simulation",
        dt_frame: float
    ) -> None:
        if sim.begin_sim:
            sim.accumulator += dt_frame
            while sim.accumulator >= sim.dt_physics:
                sim.world.get_next_frame(sim.dt_physics)
                sim.time_control.time += sim.dt_physics
                sim.accumulator -= sim.dt_physics