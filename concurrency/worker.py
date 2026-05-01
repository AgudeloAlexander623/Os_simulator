import threading
import logging
from typing import TYPE_CHECKING
from core.states import ProcessState

if TYPE_CHECKING:
    from core.scheduler import Scheduler
    from core.memory import Memory


class CoreWorker(threading.Thread):
    def __init__(self, scheduler: 'Scheduler', memory: 'Memory'):
        super().__init__()
        self.scheduler = scheduler
        self.memory = memory

    def run(self) -> None:
        while self.scheduler.has_processes():
            process = self.scheduler.get_process()

            if process:
                executed = process.execute(self.scheduler.quantum)

                logging.info(
                    f"[{self.name}] PID={process.pid} ejecutó {executed} | restante={process.remaining_time}"
                )

                if process.state == ProcessState.TERMINATED:
                    self.memory.free(process)
                elif process.state == ProcessState.READY:
                    self.scheduler.add_process(process)