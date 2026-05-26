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
import logging

from core.states import ProcessState

if TYPE_CHECKING:
    from core.process import Process

logger = logging.getLogger(__name__)


class Scheduler:
    """Clase base para schedulers de procesos.

    Gestiona una cola FIFO de procesos listos, una cola separada para
    procesos que vienen de operaciones de I/O y un mecanismo de
    cancelación por PID que permite reutilizar el mismo PID más adelante
    sin bloquear el nuevo proceso.
    """

    def __init__(self, quantum: int):
        """Inicializa el scheduler con un quantum dado.

        Args:
            quantum: Unidades de tiempo por ejecución (0 = FCFS).
        """
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
        """Agrega un proceso al scheduler.

        Si el PID estaba previamente cancelado, se limpia esa marca
        para permitir la reutilización del PID, y se drena cualquier
        instancia vieja del mismo PID que aún esté en la cola.

        Args:
            process: Proceso a agregar.
        """
        with self._count_lock:
            self._active_count += 1

        if process.pid in self._cancelled_pids:
            self._cancelled_pids.discard(process.pid)
            self._drain_pid_from_queue(process.pid)

        self.enqueue(process)

    def _drain_pid_from_queue(self, pid: int) -> None:
        """Elimina todas las instancias viejas de un PID de la cola de listos.

        Es necesario cuando se reutiliza un PID: las instancias viejas
        del proceso cancelado aún pueden estar en la cola, y al drenarlas
        nos aseguramos de que no sean despachadas en lugar del nuevo proceso.

        Args:
            pid: PID a eliminar de la cola.
        """
        if self._queue is None:
            return
        remaining = []
        while not self._queue.empty():
            p = self._queue.get()
            if p.pid == pid:
                with self._count_lock:
                    self._active_count -= 1
            else:
                remaining.append(p)
        for p in remaining:
            self._queue.put(p)

    def enqueue(self, process: 'Process') -> None:
        """Encola un proceso en la cola de listos.

        Args:
            process: Proceso a encolar.
        """
        self.queue.put(process)

    def _get_from_queue(self) -> Optional['Process']:
        """Obtiene el siguiente proceso de la cola de listos.

        Salta aquellos procesos cuyo PID esté en el conjunto de
        cancelados y descuenta su conteo activo.

        Returns:
            Proceso siguiente o None si la cola está vacía.
        """
        while self._queue is not None and not self._queue.empty():
            p = self._queue.get()
            if p.pid not in self._cancelled_pids:
                return p
            with self._count_lock:
                self._active_count -= 1
        return None

    def _get_from_io(self) -> Optional['Process']:
        """Obtiene el siguiente proceso de la cola de I/O.

        Solo retorna procesos cuyo ``io_block_remaining`` haya llegado a 0.
        Por cada unidad de tiempo que el scheduler consulta la cola, se
        descuenta 1 del tiempo de bloqueo restante, permitiendo que otros
        procesos se ejecuten mientras tanto.

        Returns:
            Proceso listo o None si la cola está vacía o ningún proceso
            ha completado su I/O.
        """
        temp: list['Process'] = []
        ready: Optional['Process'] = None

        while not self.io_queue.empty():
            p = self.io_queue.get()
            if p.pid in self._cancelled_pids:
                with self._count_lock:
                    self._active_count -= 1
                continue
            if p.io_block_remaining > 0:
                p.io_block_remaining -= 1
                p.io_elapsed += 1
                temp.append(p)
            elif ready is None:
                ready = p
            else:
                temp.append(p)

        for p in temp:
            self.io_queue.put(p)

        if ready is not None:
            ready.state = ProcessState.READY

        return ready

    def get_process(self) -> Optional['Process']:
        """Obtiene el siguiente proceso a ejecutar.

        Primero revisa la cola de I/O (los procesos bloqueados tienen
        prioridad), luego la cola de listos.

        Returns:
            Proceso a ejecutar o None si no hay procesos disponibles.
        """
        p = self._get_from_io()
        if p is not None:
            return p
        return self._get_from_queue()

    def has_processes(self) -> bool:
        """Indica si hay procesos en alguna de las colas (listos o I/O).

        Returns:
            True si al menos una cola tiene elementos.
        """
        if self._queue is None:
            return not self.io_queue.empty()
        return not self._queue.empty() or not self.io_queue.empty()

    def mark_terminated(self) -> None:
        """Marca un proceso como terminado, decrementando el conteo activo."""
        with self._count_lock:
            self._active_count -= 1

    def has_active_processes(self) -> bool:
        """Indica si hay procesos activos (encolados + en ejecución).

        Returns:
            True si _active_count > 0.
        """
        with self._count_lock:
            return self._active_count > 0

    def add_to_io_queue(self, process: 'Process') -> None:
        """Envía un proceso a la cola de I/O.

        Args:
            process: Proceso que se bloquea por I/O.
        """
        self.io_queue.put(process)

    def has_io_processes(self) -> bool:
        """Indica si hay procesos esperando en la cola de I/O.

        Returns:
            True si la cola de I/O tiene elementos.
        """
        return not self.io_queue.empty()

    def remove_process(self, pid: int) -> bool:
        """Cancela un proceso por su PID.

        No utiliza señales reales del SO (como os.kill), sino un
        mecanismo interno de cancelación: el PID se agrega a un
        conjunto de cancelados, y al momento de despachar desde las
        colas se salta cualquier proceso con ese PID.

        Si el PID ya estaba cancelado, retorna False.

        Args:
            pid: PID del proceso a cancelar.

        Returns:
            True si se marcó como cancelado, False si ya lo estaba.
        """
        if pid <= 0:
            raise ValueError(f"PID invalido para cancelar: {pid}")

        if pid in self._cancelled_pids:
            logger.warning(f"PID {pid} ya esta marcado como cancelado")
            return False

        self._cancelled_pids.add(pid)
        logger.info(f"PID {pid} marcado como cancelado")
        return True

    def _drain_pid_from_heap(self, pid: int) -> int:
        """Elimina todas las entradas de un PID del heap y retorna cuántas se quitaron.

        Ajusta ``_active_count`` por cada entrada removida para mantener
        la coherencia del conteo de procesos activos. Es segura de llamar
        incluso en schedulers sin heap (FCFS, Round-Robin) — en ese caso
        retorna 0 inmediatamente.

        Args:
            pid: PID a eliminar del heap.

        Returns:
            int: Número de entradas eliminadas del heap.
        """
        heap = getattr(self, 'heap', None)
        if heap is None:
            return 0
        old_len = len(heap)
        heap = [(rt, c, p) for rt, c, p in heap if p.pid != pid]
        heapq.heapify(heap)
        self.heap = heap
        removed = old_len - len(heap)
        if removed > 0:
            with self._count_lock:
                self._active_count -= removed
        return removed


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

        if process.pid in self._cancelled_pids:
            self._cancelled_pids.discard(process.pid)
            self._drain_pid_from_heap(process.pid)

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
        removed = self._drain_pid_from_heap(pid)
        if removed > 0:
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

        if process.pid in self._cancelled_pids:
            self._cancelled_pids.discard(process.pid)
            self._drain_pid_from_heap(process.pid)

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
        removed = self._drain_pid_from_heap(pid)
        if removed > 0:
            self._cancelled_pids.add(pid)
            return True
        return super().remove_process(pid)


class RoundRobinScheduler(Scheduler):
    """Round-Robin: Quantum fijo, como el original."""
    pass
