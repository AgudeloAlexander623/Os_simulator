# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

"""Fábrica de procesos de ejemplo para la simulación.

Genera una lista de procesos precargados con distintos burst times,
memoria, prioridades y tiempos de llegada, útiles para hacer pruebas
rápidas sin tener que agregarlos a mano.
"""

from typing import List, Tuple

ProcessData = Tuple[int, int, int, int, int, int]


def sample_processes() -> List[ProcessData]:
    """Retorna la lista de procesos de ejemplo por defecto.

    Returns:
        Lista de tuplas (pid, burst_time, memory, priority, arrival_time, io_time).
    """
    return [
        (1, 10, 100, 1, 0, 0),
        (2, 6, 200, 2, 2, 0),
        (3, 8, 150, 0, 4, 0),
    ]
