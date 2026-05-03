from typing import List, Dict, Optional
from core.process import Process


class GanttChart:
    """Genera un diagrama de Gantt text-based para la simulación."""

    def __init__(self):
        self.timeline: List[Dict[int, Optional[int]]] = []

    def record(self, time_step: int, core_id: int, pid: Optional[int]) -> None:
        """Registra qué proceso corre en un core en un momento dado."""
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
                if pid == prev_pid and pid is not None:
                    count += 1
                else:
                    if prev_pid is not None:
                        if count > 1:
                            row.append(f"P{prev_pid}" + "─" * (count * 2))
                        else:
                            row.append(f"P{prev_pid}")
                    prev_pid = pid
                    count = 1

            if prev_pid is not None:
                if count > 1:
                    row.append(f"P{prev_pid}" + "─" * (count * 2))
                else:
                    row.append(f"P{prev_pid}")

            lines.append(f"Core {core_id}: " + "".join(row))

        return "\n".join(lines)


def build_gantt_from_processes(processes: List[Process], num_cores: int, total_time: int) -> GanttChart:
    """Construye un Gantt chart aproximado a partir de los tiempos de los procesos.

    Nota: Esto es una aproximación basada en completion_time. Para un Gantt
    preciso, se debe usar GanttChart.record() durante la simulación.

    Args:
        processes: Lista de procesos completados.
        num_cores: Número de cores.
        total_time: Tiempo total de simulación.

    Returns:
        GanttChart renderizable.
    """
    chart = GanttChart()
    sorted_procs = sorted(processes, key=lambda p: p.start_time if p.start_time >= 0 else float('inf'))

    for i, proc in enumerate(sorted_procs):
        core_id = i % num_cores
        if proc.start_time >= 0 and proc.completion_time >= 0:
            for t in range(proc.start_time, proc.completion_time):
                chart.record(t, core_id, proc.pid)

    return chart
