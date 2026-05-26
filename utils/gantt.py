# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

"""Generación de diagramas de Gantt en texto.

Registra qué proceso se ejecuta en cada core en cada unidad de tiempo
y renderiza una representación visual tipo::

    Core 0: P1────P2idle──P1
    Core 1: idle──P3────P3
"""

from typing import List, Dict, Optional


class GanttChart:
    """Genera un diagrama de Gantt text-based para la simulación."""

    def __init__(self):
        self.timeline: List[Dict[int, Optional[int]]] = []

    def record(self, time_step: int, core_id: int, pid: Optional[int]) -> None:
        """Registra qué proceso corre en un core en un momento dado.

        Args:
            time_step: Unidad de tiempo (entero >= 0).
            core_id: Identificador del core (entero >= 0).
            pid: PID del proceso que se ejecuta, o None si idle.
        """
        if not isinstance(time_step, int) or not isinstance(core_id, int):
            raise ValueError("time_step and core_id must be integers")
        if time_step < 0 or core_id < 0:
            raise ValueError("time_step and core_id must be non-negative")
        while len(self.timeline) <= time_step:
            self.timeline.append({})
        self.timeline[time_step][core_id] = pid

    def _render_core(self, core_id: int) -> str:
        """Renderiza la línea de un solo core comprimiendo ráfagas consecutivas.

        Comprime ejecuciones consecutivas del mismo PID o idle en
        segmentos etiquetados, asegurando que los periodos idle nunca
        se pierdan en la representación visual (fix del bug donde idle
        desaparecía al alternar idle → proceso → idle → proceso).

        Args:
            core_id: Core a renderizar.

        Returns:
            str: Línea formateada del core, p.ej. 'P1──idleP2'.
        """
        row = []
        prev_pid = None
        count = 0

        for step in range(len(self.timeline)):
            current_pid = self.timeline[step].get(core_id)
            if current_pid == prev_pid:
                count += 1
            else:
                self._flush_segment(row, prev_pid, count)
                prev_pid = current_pid
                count = 1

        self._flush_segment(row, prev_pid, count)
        return "".join(row)

    @staticmethod
    def _flush_segment(row: List[str], pid: Optional[int], count: int) -> None:
        """Agrega un segmento (proceso o idle) a la fila si hay algo que emitir.

        Args:
            row: Lista de segmentos a la que agregar.
            pid: PID del segmento anterior (None si idle).
            count: Duración del segmento en unidades de tiempo.
        """
        if count == 0:
            return
        label = f"P{pid}" if pid is not None else "idle"
        if count > 1:
            row.append(label + "─" * ((count - 1) * 2))
        else:
            row.append(label)

    def render(self, num_cores: int) -> str:
        """Renderiza el Gantt chart como texto.

        Args:
            num_cores: Número de cores a mostrar.

        Returns:
            str: Gantt chart en formato texto.
        """
        if not self.timeline:
            return "(vacío)"

        lines = [
            f"Core {core_id}: {self._render_core(core_id)}"
            for core_id in range(num_cores)
        ]
        return "\n".join(lines)
    
