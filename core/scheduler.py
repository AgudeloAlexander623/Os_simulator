from queue import Queue
from typing import Optional, TYPE_CHECKING
import heapq

if TYPE_CHECKING:
    from core.process import Process


class Scheduler:
    """Clase base para schedulers de procesos."""

    def __init__(self, quantum: int):
        """Inicializa el scheduler.

        Args:
            quantum (int): Quantum para ejecución.
        """
        self.quantum = quantum
        self.queue: Queue['Process'] = Queue()

    def add_process(self, process: 'Process') -> None:
        """Agrega un proceso a la cola.

        Args:
            process (Process): Proceso a agregar.
        """
        self.queue.put(process)

    def get_process(self) -> Optional['Process']:
        """Obtiene el próximo proceso.

        Returns:
            Optional[Process]: Próximo proceso o None.
        """
        if self.queue.empty():
            return None
        return self.queue.get()

    def has_processes(self) -> bool:
        """Verifica si hay procesos pendientes.

        Returns:
            bool: True si hay procesos.
        """
        return not self.queue.empty()


class FCFSScheduler(Scheduler):
    """First-Come, First-Served: Procesa en orden de llegada, sin quantum."""
    def __init__(self):
        super().__init__(quantum=0)

    def get_process(self) -> Optional['Process']:
        return super().get_process()


class SJFScheduler(Scheduler):
    """Shortest Job First: Prioriza procesos con menor remaining_time."""
    def __init__(self, quantum: int):
        super().__init__(quantum)
        self.heap = []  # (remaining_time, process)

    def add_process(self, process: 'Process') -> None:
        # Remover entrada vieja si el proceso ya está en el heap
        self.heap = [(rt, p) for rt, p in self.heap if p.pid != process.pid]
        heapq.heappush(self.heap, (process.remaining_time, process))

    def get_process(self) -> Optional['Process']:
        if not self.heap:
            return None
        return heapq.heappop(self.heap)[1]

    def has_processes(self) -> bool:
        return len(self.heap) > 0


class PriorityScheduler(Scheduler):
    """Priority Scheduling: Prioriza por prioridad (menor número = mayor prioridad)."""
    def __init__(self, quantum: int):
        super().__init__(quantum)
        self.heap = []  # (priority, process) - asumir priority en Process

    def add_process(self, process: 'Process') -> None:
        priority = getattr(process, 'priority', 0)  # Default priority
        heapq.heappush(self.heap, (priority, process))

    def get_process(self) -> Optional['Process']:
        if not self.heap:
            return None
        return heapq.heappop(self.heap)[1]

    def has_processes(self) -> bool:
        return len(self.heap) > 0


class RoundRobinScheduler(Scheduler):
    """Round-Robin: Quantum fijo, como el original."""
    pass