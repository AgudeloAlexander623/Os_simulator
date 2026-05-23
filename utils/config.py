# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

"""Configuraciones por defecto del simulador.

Acá están todos los valores que se usan cuando no se especifica otro
valor desde la GUI: tipo de scheduler, quantum, capacidad de memoria,
tamaño de página, capacidad del FS, número de cores, overhead de
context switch y nivel de logging.
"""

QUANTUM = 2
SCHEDULER_TYPE = 'round_robin'
MEMORY_CAPACITY = 500
PAGE_SIZE = 50
FS_CAPACITY = 1000
NUM_CORES = 2
CONTEXT_SWITCH_OVERHEAD = 0
LOG_LEVEL = 'INFO'
