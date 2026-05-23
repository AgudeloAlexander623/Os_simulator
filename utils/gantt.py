# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

from typing import List, Dict, Optional


class GanttChart:
    """Genera un diagrama de Gantt text-based para la simulación."""

    def __init__(self):
        self.timeline: List[Dict[int, Optional[int]]] = []

    def record(self, time_step: int, core_id: int, pid: Optional[int]) -> None:
        """Registra qué proceso corre en un core en un momento dado."""
        if not isinstance(time_step, int) or not isinstance(core_id, int):
            raise ValueError("time_step and core_id must be integers")
        if time_step < 0 or core_id < 0:
            raise ValueError("time_step and core_id must be non-negative")
        while len(self.timeline) <= time_step:
            self.timeline.append({})
        self.timeline[time_step][core_id] = pid

    def render(self, num_cores: int) -> str:
        """Renderiza el Gantt chart como texto.

        Args:
            num_cores: Número de cores a mostrar.

        Returns:
            str: Gantt chart en formato texto.
        """
        if not self.timeline:
            return "(vacío)"

        lines = []
        for core_id in range(num_cores):
            row = []
            prev_pid = None
            count = 0

            for step in range(len(self.timeline)):
                pid = self.timeline[step].get(core_id)
                if pid == prev_pid:
                    count += 1
                else:
                    if prev_pid is not None or count > 0:
                        label = f"P{prev_pid}" if prev_pid is not None else "idle"
                        if count > 1:
                            row.append(label + "─" * ((count - 1) * 2))
                        else:
                            row.append(label)
                    prev_pid = pid
                    count = 1 if pid is not None else 0

            if prev_pid is not None or count > 0:
                label = f"P{prev_pid}" if prev_pid is not None else "idle"
                if count > 1:
                    row.append(label + "─" * ((count - 1) * 2))
                else:
                    row.append(label)

            lines.append(f"Core {core_id}: " + "".join(row))

        return "\n".join(lines)
