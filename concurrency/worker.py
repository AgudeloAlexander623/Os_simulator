import threading
import logging
from typing import TYPE_CHECKING
from core.states import ProcessState

if TYPE_CHECKING:
    from core.scheduler import Scheduler
    from core.memory import Memory


class CoreWorker(threading.Thread):
    """Trabajador que ejecuta procesos en un núcleo simulado."""

    def __init__(self, scheduler: 'Scheduler', memory: 'Memory'):
        """Inicializa el worker.

        Args:
            scheduler (Scheduler): Scheduler para obtener procesos.
            memory (Memory): Memoria para liberar procesos terminados.
        """
        super().__init__()
        self.scheduler = scheduler
        self.memory = memory
        self.current_time = 0

    def run(self) -> None:
        """Ejecuta el loop de procesamiento de procesos."""
        while self.scheduler.has_processes():
            process = self.scheduler.get_process()

            if process:
                # Setear start_time si es la primera ejecución
                if process.start_time == -1:
                    process.start_time = self.current_time

                executed = process.execute(self.scheduler.quantum)

                self.current_time += executed

                logging.info(
                    f"[{self.name}] PID={process.pid} ejecutó {executed} | restante={process.remaining_time}"
                )

                if process.state == ProcessState.TERMINATED:
                    process.completion_time = self.current_time
                    self.memory.free(process)
                elif process.state == ProcessState.READY:
                    self.scheduler.add_process(process)