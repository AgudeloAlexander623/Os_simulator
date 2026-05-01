import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.process import Process


class Memory:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.used = 0

    def allocate(self, process: 'Process') -> bool:
        if self.used + process.memory <= self.capacity:
            self.used += process.memory
            logging.info(f"[RAM] asignado PID={process.pid}")
            return True
        else:
            logging.info(f"[RAM] SIN espacio para PID={process.pid}")
            return False

    def free(self, process: 'Process') -> None:
        self.used -= process.memory
        logging.info(f"[RAM] liberado PID={process.pid}")