from queue import Queue
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.process import Process


class Scheduler:
    def __init__(self, quantum: int):
        self.quantum = quantum
        self.queue: Queue['Process'] = Queue()

    def add_process(self, process: 'Process') -> None:
        self.queue.put(process)

    def get_process(self) -> Optional['Process']:
        if self.queue.empty():
            return None
        return self.queue.get()

    def has_processes(self) -> bool:
        return not self.queue.empty()