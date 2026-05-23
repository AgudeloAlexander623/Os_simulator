# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

"""Planificadores de CPU (schedulers).

Implementa cuatro algoritmos de planificación:
- FCFS: First-Come, First-Served, sin quantum
- SJF: Shortest Job First, prioriza el menor tiempo restante
- Priority: Prioridad (menor número = mayor prioridad)
- Round-Robin: Quantum fijo, turno circular

Todos heredan de Scheduler, que maneja la cola de listos, la cola de
I/O, el conteo de procesos activos y soporte para cancelación de
procesos por PID.
"""

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
        self.submission_complete = threading.Event()
        self.submission_complete.set()
        self._cancelled_pids: set[int] = set()

    @property
    def queue(self) -> Queue['Process']:
        if self._queue is None:
            self._queue = Queue()
        return self._queue

    def add_process(self, process: 'Process') -> None:
        with self._count_lock:
            self._active_count += 1
        self.enqueue(process)

    def enqueue(self, process: 'Process') -> None:
        self.queue.put(process)

    def _get_from_queue(self) -> Optional['Process']:
        while self._queue is not None and not self._queue.empty():
            p = self._queue.get()
            if p.pid not in self._cancelled_pids:
                return p
            with self._count_lock:
                self._active_count -= 1
        return None

    def _get_from_io(self) -> Optional['Process']:
        while not self.io_queue.empty():
            p = self.io_queue.get()
            if p.pid not in self._cancelled_pids:
                return p
            with self._count_lock:
                self._active_count -= 1
        return None

    def get_process(self) -> Optional['Process']:
        p = self._get_from_io()
        if p is not None:
            return p
        return self._get_from_queue()

    def has_processes(self) -> bool:
        if self._queue is None:
            return not self.io_queue.empty()
        return not self._queue.empty() or not self.io_queue.empty()

    def mark_terminated(self) -> None:
        with self._count_lock:
            self._active_count -= 1

    def has_active_processes(self) -> bool:
        with self._count_lock:
            return self._active_count > 0

    def add_to_io_queue(self, process: 'Process') -> None:
        self.io_queue.put(process)

    def has_io_processes(self) -> bool:
        return not self.io_queue.empty()

    def remove_process(self, pid: int) -> bool:
        if pid in self._cancelled_pids:
            return False
        self._cancelled_pids.add(pid)
        return True


class FCFSScheduler(Scheduler):
    """First-Come, First-Served: Procesa en orden de llegada, sin quantum."""
    def __init__(self):
        super().__init__(quantum=0)


class SJFScheduler(Scheduler):
    """Shortest Job First: Prioriza procesos con menor remaining_time."""

    def __init__(self, quantum: int):
        super().__init__(quantum)
        self.heap: list = []
        self._counter = 0

    def add_process(self, process: 'Process') -> None:
        with self._count_lock:
            self._active_count += 1
        self.enqueue(process)

    def enqueue(self, process: 'Process') -> None:
        self.heap = [(rt, c, p) for rt, c, p in self.heap if p.pid != process.pid]
        heapq.heapify(self.heap)
        self._counter += 1
        heapq.heappush(self.heap, (process.remaining_time, self._counter, process))

    def has_processes(self) -> bool:
        return len(self.heap) > 0 or self.has_io_processes()

    def get_process(self) -> Optional['Process']:
        if self.has_io_processes():
            p = self._get_from_io()
            if p is not None:
                return p
        while self.heap:
            _, _, p = heapq.heappop(self.heap)
            if p.pid not in self._cancelled_pids:
                return p
            with self._count_lock:
                self._active_count -= 1
        return None

    def remove_process(self, pid: int) -> bool:
        old_len = len(self.heap)
        self.heap = [(rt, c, p) for rt, c, p in self.heap if p.pid != pid]
        heapq.heapify(self.heap)
        if len(self.heap) < old_len:
            self._cancelled_pids.add(pid)
            return True
        return super().remove_process(pid)


class PriorityScheduler(Scheduler):
    """Priority Scheduling: Prioriza por prioridad (menor número = mayor prioridad)."""

    def __init__(self, quantum: int):
        super().__init__(quantum)
        self.heap: list = []
        self._counter = 0

    def add_process(self, process: 'Process') -> None:
        with self._count_lock:
            self._active_count += 1
        self.enqueue(process)

    def enqueue(self, process: 'Process') -> None:
        self.heap = [(pr, c, p) for pr, c, p in self.heap if p.pid != process.pid]
        heapq.heapify(self.heap)
        self._counter += 1
        priority = getattr(process, 'priority', 0)
        heapq.heappush(self.heap, (priority, self._counter, process))

    def has_processes(self) -> bool:
        return len(self.heap) > 0 or self.has_io_processes()

    def get_process(self) -> Optional['Process']:
        if self.has_io_processes():
            p = self._get_from_io()
            if p is not None:
                return p
        while self.heap:
            _, _, p = heapq.heappop(self.heap)
            if p.pid not in self._cancelled_pids:
                return p
            with self._count_lock:
                self._active_count -= 1
        return None

    def update_process_priority(self, process: 'Process', new_priority: int) -> None:
        self.heap = [(pr, c, p) for pr, c, p in self.heap if p.pid != process.pid]
        heapq.heapify(self.heap)
        setattr(process, 'priority', new_priority)
        self._counter += 1
        heapq.heappush(self.heap, (new_priority, self._counter, process))

    def remove_process(self, pid: int) -> bool:
        old_len = len(self.heap)
        self.heap = [(pr, c, p) for pr, c, p in self.heap if p.pid != pid]
        heapq.heapify(self.heap)
        if len(self.heap) < old_len:
            self._cancelled_pids.add(pid)
            return True
        return super().remove_process(pid)
        
class RoundRobinScheduler(Scheduler):
    """Round-Robin: Quantum fijo, como el original."""
    pass