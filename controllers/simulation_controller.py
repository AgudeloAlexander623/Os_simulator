import logging
import threading
from typing import List, Callable
from core.process import Process
from core.scheduler import Scheduler, FCFSScheduler, SJFScheduler, PriorityScheduler, RoundRobinScheduler
from core.memory import Memory
from concurrency.worker import CoreWorker
from utils import config
from utils.gantt import GanttChart


class SimulationController:
    """Controlador para la lógica de simulación (MVC)."""

    def __init__(self, scheduler_type: str, quantum: int, memory_cap: int, num_cores: int):
        """Inicializa el controlador.

        Args:
            scheduler_type (str): Tipo de scheduler.
            quantum (int): Quantum.
            memory_cap (int): Capacidad de memoria.
            num_cores (int): Número de cores.
        """
        self.scheduler = self._create_scheduler(scheduler_type, quantum)
        self.memory = Memory(memory_cap)
        self.num_cores = num_cores
        self.processes: List[Process] = []
        self.on_simulation_end: Callable[[dict], None] = None

    def _create_scheduler(self, sched_type: str, quantum: int) -> Scheduler:
        """Crea el scheduler basado en tipo."""
        if sched_type == 'fcfs':
            return FCFSScheduler()
        elif sched_type == 'sjf':
            return SJFScheduler(quantum)
        elif sched_type == 'priority':
            return PriorityScheduler(quantum)
        elif sched_type == 'round_robin':
            return RoundRobinScheduler(quantum)
        else:
            raise ValueError(f"Tipo de scheduler desconocido: {sched_type}")

    def add_process(self, pid: int, burst: int, mem: int, pri: int = 0) -> None:
        """Agrega un proceso.

        Args:
            pid (int): PID.
            burst (int): Burst time.
            mem (int): Memoria.
            pri (int): Prioridad.
        """
        process = Process(pid, burst, mem, pri)
        self.processes.append(process)

    def start_simulation(self) -> dict:
        """Inicia la simulación en un thread.

        Returns:
            dict: Estadísticas calculadas al final de la simulación.
        """
        loaded_processes = []

        # Cargar procesos
        for p in self.processes:
            try:
                self.memory.allocate(p)
                self.scheduler.add_process(p)
                loaded_processes.append(p)
            except Exception as e:
                logging.warning(f"Error al cargar proceso {p.pid}: {e}")

        # Crear workers
        overhead = getattr(config, 'CONTEXT_SWITCH_OVERHEAD', 0)
        cores = [CoreWorker(self.scheduler, self.memory, overhead) for _ in range(self.num_cores)]
        for core in cores:
            core.start()
        for core in cores:
            core.join()

        # Tiempo simulado teórico: total burst / num_cores (cores en paralelo)
        total_burst = sum(p.burst_time for p in loaded_processes)
        total_time = total_burst / self.num_cores if self.num_cores > 0 else 0
        completed_processes = [p for p in loaded_processes if p.completion_time != -1]
        completed = len(completed_processes)
        throughput = completed / total_time if total_time > 0 else 0

        # Calcular métricas promedio
        if completed_processes:
            avg_waiting = sum(p.waiting_time for p in completed_processes) / completed
            avg_turnaround = sum(p.turnaround_time for p in completed_processes) / completed
            avg_response = sum(p.response_time for p in completed_processes) / completed
        else:
            avg_waiting = avg_turnaround = avg_response = 0

        # CPU utilization (tiempo total ejecutado / (tiempo simulado * num_cores))
        total_burst = sum(p.burst_time for p in loaded_processes)
        cpu_utilization = total_burst / (total_time * self.num_cores) if total_time > 0 else 0
        cpu_utilization = min(cpu_utilization, 1.0)  # Cap a 100%

        stats = {
            "total_time": total_time,
            "completed": completed,
            "throughput": throughput,
            "avg_waiting_time": avg_waiting,
            "avg_turnaround_time": avg_turnaround,
            "avg_response_time": avg_response,
            "cpu_utilization": cpu_utilization
        }
        if self.on_simulation_end:
            self.on_simulation_end(stats)

        return stats
