# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

import threading
import logging
import time
from typing import TYPE_CHECKING, Optional
from core.states import ProcessState
from concurrency.lock import scheduler_lock, memory_lock

if TYPE_CHECKING:
    from core.scheduler import Scheduler
    from core.memory import Memory
    from utils.gantt import GanttChart


class CoreWorker(threading.Thread):
    """Trabajador que ejecuta procesos en un núcleo simulado."""

    def __init__(
        self,
        scheduler: 'Scheduler',
        memory: 'Memory',
        context_switch_overhead: int = 0,
        core_id: int = 0,
        gantt_chart: Optional['GanttChart'] = None,
    ):
        """Inicializa el worker.

        Args:
            scheduler (Scheduler): Scheduler para obtener procesos.
            memory (Memory): Memoria para liberar procesos terminados.
            context_switch_overhead (int): Costo en tiempo de context switch.
            core_id (int): ID del core (para Gantt chart).
            gantt_chart (Optional[GanttChart]): Gantt chart para registrar ejecución.
        """
        super().__init__()
        self.scheduler = scheduler
        self.memory = memory
        self.context_switch_overhead = context_switch_overhead
        self.core_id = core_id
        self.gantt_chart = gantt_chart
        self.current_time = 0

    def run(self) -> None:
        """Ejecuta el loop de procesamiento de procesos."""
        while True:
            # Obtener proceso del scheduler (sección crítica breve)
            with scheduler_lock:
                if not self.scheduler.has_active_processes():
                    break
                process = self.scheduler.get_process()

            if process:
                # Aplicar context switch overhead (excepto en la primera ejecución del core)
                if self.current_time > 0 and self.context_switch_overhead > 0:
                    self.current_time += self.context_switch_overhead

                # Setear start_time y first_scheduled_time si es la primera ejecución
                if process.start_time == -1:
                    process.start_time = self.current_time
                    process.first_scheduled_time = self.current_time

                # Ejecutar FUERA del lock (cores corren en paralelo)
                executed = process.execute(self.scheduler.quantum)

                # Registrar en Gantt chart
                if self.gantt_chart:
                    for t in range(self.current_time, self.current_time + executed):
                        self.gantt_chart.record(t, self.core_id, process.pid)

                self.current_time += executed

                logging.info(
                    f"[{self.name}] PID={process.pid} ejecutó {executed} | restante={process.remaining_time}"
                )

                if process.state == ProcessState.TERMINATED:
                    process.completion_time = self.current_time
                    self.scheduler.mark_terminated()
                    with memory_lock:
                        self.memory.free(process)
                elif process.state == ProcessState.READY:
                    with scheduler_lock:
                        self.scheduler._enqueue(process)
            else:
                # Queue vacía temporalmente, otro worker va a re-encolar
                time.sleep(0.001)

    def get_total_time(self) -> int:
        """Retorna el tiempo total de simulación de este core."""
        return self.current_time
