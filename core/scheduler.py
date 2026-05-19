# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

from queue import Queue
from typing import Optional, TYPE_CHECKING
import heapq
import threading

if TYPE_CHECKING:
    from core.process import Process


class Scheduler:
    """Clase base para schedulers de procesos."""

    def __init__(self, quantum: int):
        """Inicializa el scheduler."""
        self.quantum = quantum
        self.queue: Queue['Process'] = Queue()
        self.io_queue: Queue['Process'] = Queue()
        self._active_count = 0
        self._count_lock = threading.Lock()
        self.submission_complete = False

    def add_process(self, process: 'Process') -> None:
        """Agrega un proceso nuevo a la cola (incrementa contador activo)."""
        with self._count_lock:
            self._active_count += 1
        self._enqueue(process)

    def _enqueue(self, process: 'Process') -> None:
        """Encola un proceso sin modificar el contador activo (para re-encolar)."""
        self.queue.put(process)

    def get_process(self) -> Optional['Process']:
        """Obtiene el próximo proceso."""
        if self.queue.empty():
            return None
        return self.queue.get()

    def has_processes(self) -> bool:
        """Verifica si hay procesos pendientes en la cola."""
        return not self.queue.empty()

    def mark_terminated(self) -> None:
        """Marca un proceso como terminado, decrementando el contador activo."""
        with self._count_lock:
            self._active_count -= 1

    def has_active_processes(self) -> bool:
        """Verifica si quedan procesos activos (en cola o ejecutando)."""
        with self._count_lock:
            return self._active_count > 0

    def add_to_io_queue(self, process: 'Process') -> None:
        """Agrega un proceso a la cola de I/O."""
        self.io_queue.put(process)

    def get_io_process(self) -> Optional['Process']:
        """Obtiene el próximo proceso de la cola de I/O."""
        if self.io_queue.empty():
            return None
        return self.io_queue.get()

    def has_io_processes(self) -> bool:
        """Verifica si hay procesos en la cola de I/O."""
        return not self.io_queue.empty()


class FCFSScheduler(Scheduler):
    """First-Come, First-Served: Procesa en orden de llegada, sin quantum."""
    def __init__(self):
        super().__init__(quantum=0)


class SJFScheduler(Scheduler):
    """Shortest Job First: Prioriza procesos con menor remaining_time."""
    def __init__(self, quantum: int):
        super().__init__(quantum)
        self.heap = []

    def add_process(self, process: 'Process') -> None:
        with self._count_lock:
            self._active_count += 1
        self._enqueue(process)

    def _enqueue(self, process: 'Process') -> None:
        self.heap = [(rt, p) for rt, p in self.heap if p.pid != process.pid]
        heapq.heappush(self.heap, (process.remaining_time, process))

    def has_processes(self) -> bool:
        return len(self.heap) > 0

    def get_process(self) -> Optional['Process']:
        if not self.heap:
            return None
        return heapq.heappop(self.heap)[1]


class PriorityScheduler(Scheduler):
    """Priority Scheduling: Prioriza por prioridad (menor número = mayor prioridad)."""
    def __init__(self, quantum: int):
        super().__init__(quantum)
        self.heap = []

    def add_process(self, process: 'Process') -> None:
        with self._count_lock:
            self._active_count += 1
        self._enqueue(process)

    def _enqueue(self, process: 'Process') -> None:
        priority = getattr(process, 'priority', 0)
        heapq.heappush(self.heap, (priority, process))

    def has_processes(self) -> bool:
        return len(self.heap) > 0

    def get_process(self) -> Optional['Process']:
        if not self.heap:
            return None
        return heapq.heappop(self.heap)[1]


class RoundRobinScheduler(Scheduler):
    """Round-Robin: Quantum fijo, como el original."""
    pass
