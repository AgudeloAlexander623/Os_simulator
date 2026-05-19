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
        self._queue: Optional[Queue['Process']] = None
        self.io_queue: Queue['Process'] = Queue()
        self._active_count = 0
        self._count_lock = threading.Lock()
        self.submission_complete = True

    @property
    def queue(self) -> Queue['Process']:
        """Cola de procesos listos. Se crea bajo demanda."""
        if self._queue is None:
            self._queue = Queue()
        return self._queue

    def add_process(self, process: 'Process') -> None:
        """Agrega un proceso nuevo a la cola (incrementa contador activo)."""
        with self._count_lock:
            self._active_count += 1
        self._enqueue(process)

    def _enqueue(self, process: 'Process') -> None:
        """Encola un proceso sin modificar el contador activo (para re-encolar)."""
        self.queue.put(process)

    def get_process(self) -> Optional['Process']:
        """Obtiene el próximo proceso.

        Prioriza procesos que vienen de la cola de I/O, ya que
        llevan esperando y es justo darles turno primero.
        """
        if not self.io_queue.empty():
            return self.io_queue.get()
        if self._queue is None or self._queue.empty():
            return None
        return self._queue.get()

    def has_processes(self) -> bool:
        """Verifica si hay procesos pendientes en la cola."""
        if self._queue is None:
            return not self.io_queue.empty()
        return not self._queue.empty() or not self.io_queue.empty()

    def mark_terminated(self) -> None:
        """Marca un proceso como terminado, decrementando el contador activo."""
        with self._count_lock:
            self._active_count -= 1

    def has_active_processes(self) -> bool:
        """Verifica si quedan procesos activos (en cola o ejecutando)."""
        with self._count_lock:
            return self._active_count > 0

    def add_to_io_queue(self, process: 'Process') -> None:
        """Agrega un proceso a la cola de I/O después de completar su operación."""
        self.io_queue.put(process)

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
        self.heap: list = []

    def add_process(self, process: 'Process') -> None:
        with self._count_lock:
            self._active_count += 1
        self._enqueue(process)

    def _enqueue(self, process: 'Process') -> None:
        # Actualizar el heap: remover proceso existente si ya está
        self.heap = [(rt, p) for rt, p in self.heap if p.pid != process.pid]
        heapq.heapify(self.heap)
        heapq.heappush(self.heap, (process.remaining_time, process))

    def has_processes(self) -> bool:
        return len(self.heap) > 0 or self.has_io_processes()

    def get_process(self) -> Optional['Process']:
        # Primero revisar la cola de I/O (procesos que ya esperaron)
        if self.has_io_processes():
            return self.io_queue.get()
        if not self.heap:
            return None
        return heapq.heappop(self.heap)[1]


class PriorityScheduler(Scheduler):
    """Priority Scheduling: Prioriza por prioridad (menor número = mayor prioridad)."""

    def __init__(self, quantum: int):
        super().__init__(quantum)
        self.heap: list = []

    def add_process(self, process: 'Process') -> None:
        with self._count_lock:
            self._active_count += 1
        self._enqueue(process)

    def _enqueue(self, process: 'Process') -> None:
        priority = getattr(process, 'priority', 0)
        heapq.heappush(self.heap, (priority, process))

    def has_processes(self) -> bool:
        return len(self.heap) > 0 or self.has_io_processes()

    def get_process(self) -> Optional['Process']:
        # Primero revisar la cola de I/O (procesos que ya esperaron)
        if self.has_io_processes():
            return self.io_queue.get()
        if not self.heap:
            return None
        return heapq.heappop(self.heap)[1]


class RoundRobinScheduler(Scheduler):
    """Round-Robin: Quantum fijo, como el original."""
    pass
