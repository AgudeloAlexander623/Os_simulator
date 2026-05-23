# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

"""Estados de un proceso en el simulador.

Un proceso siempre está en uno de estos cuatro estados:
- READY: listo para ejecutar, esperando en la cola del scheduler
- RUNNING: ejecutándose en un core
- BLOCKED: esperando una operación de I/O
- TERMINATED: ejecución completada
"""

from enum import Enum


class ProcessState(Enum):
    READY = "READY"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    TERMINATED = "TERMINATED"
