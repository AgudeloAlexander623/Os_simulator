# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

# Configuraciones para el simulador OS

# Scheduler
QUANTUM = 2
SCHEDULER_TYPE = 'round_robin'  # Opciones: 'fcfs', 'sjf', 'priority', 'round_robin'

# Memoria
MEMORY_CAPACITY = 500
PAGE_SIZE = 50

# File System
FS_CAPACITY = 1000

# Número de cores
NUM_CORES = 2

# Context switch overhead (en unidades de tiempo simulado)
CONTEXT_SWITCH_OVERHEAD = 0

# Logging level
LOG_LEVEL = 'INFO'