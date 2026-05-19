# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

from core.process import Process
from typing import List, Tuple

ProcessData = Tuple[int, int, int, int, int]


def sample_processes() -> List[ProcessData]:
    """Retorna la lista de procesos de ejemplo por defecto.

    Returns:
        Lista de tuplas (pid, burst_time, memory, priority, arrival_time).
    """
    return [
        (1, 10, 100, 1, 0),
        (2, 6, 200, 2, 2),
        (3, 8, 300, 0, 4),
    ]


def processes_from_tuples(data: List[ProcessData]) -> List[Process]:
    """Crea instancias de Process a partir de tuplas de datos.

    Args:
        data: Lista de tuplas (pid, burst_time, memory, priority, arrival_time).

    Returns:
        Lista de objetos Process.
    """
    processes = []
    for pid, burst, mem, pri, arrival in data:
        p = Process(pid, burst, mem, pri)
        p.arrival_time = arrival
        processes.append(p)
    return processes
