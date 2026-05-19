# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

import logging
import threading
from typing import List, Callable
from core.process import Process
from core.scheduler import Scheduler, FCFSScheduler, SJFScheduler, PriorityScheduler, RoundRobinScheduler
from core.memory import Memory
from core.filesystem import FileSystem
from utils import config
from concurrency.worker import CoreWorker
from utils.gantt import GanttChart


class SimulationController:
    """Controlador para la lógica de simulación (MVC)."""

    def __init__(self, scheduler_type: str, quantum: int, memory_cap: int, num_cores: int, context_switch_overhead: int = 0):
        """Inicializa el controlador.

        Args:
            scheduler_type (str): Tipo de scheduler.
            quantum (int): Quantum.
            memory_cap (int): Capacidad de memoria.
            num_cores (int): Número de cores.
            context_switch_overhead (int): Costo de context switch.
        """
        self.scheduler = self._create_scheduler(scheduler_type, quantum)
        self.memory = Memory(memory_cap, getattr(config, 'PAGE_SIZE', 50))
        self.filesystem = FileSystem(getattr(config, 'FS_CAPACITY', 1000))
        self.num_cores = num_cores
        self.context_switch_overhead = context_switch_overhead
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

    def add_process(self, pid: int, burst: int, mem: int, pri: int = 0, arrival: int = 0, io_time: int = 0) -> None:
        """Agrega un proceso.

        Args:
            pid (int): PID.
            burst (int): Burst time.
            mem (int): Memoria.
            pri (int): Prioridad.
            arrival (int): Tiempo de llegada.
            io_time (int): Tiempo de I/O después de cada ejecución.
        """
        process = Process(pid, burst, mem, pri)
        process.arrival_time = arrival
        if io_time > 0:
            process.io_operations = [io_time]
        self.processes.append(process)

    def start_simulation(self) -> dict:
        loaded_processes = []

        # Ordenar procesos por arrival_time
        sorted_processes = sorted(self.processes, key=lambda p: p.arrival_time)

        # Agregar todos los procesos a memoria
        for p in sorted_processes:
            try:
                self.memory.allocate(p)
                loaded_processes.append(p)
            except Exception as e:
                logging.warning(f"Error al cargar proceso {p.pid}: {e}")

        # Agregar procesos con arrival_time=0 al scheduler
        for p in loaded_processes:
            if p.arrival_time == 0:
                self.scheduler.add_process(p)
                logging.info(f"[Controller] PID={p.pid} llegó en t=0")

        # Crear workers
        gantt = GanttChart()
        cores = [
            CoreWorker(self.scheduler, self.memory, self.context_switch_overhead, core_id=i, gantt_chart=gantt)
            for i in range(self.num_cores)
        ]

        # Thread para agregar procesos escalonados
        staggered = [p for p in loaded_processes if p.arrival_time > 0]
        if staggered:
            def submit_staggered():
                import time
                for p in staggered:
                    time.sleep(p.arrival_time * 0.01)
                    self.scheduler.add_process(p)
                    logging.info(f"[Controller] PID={p.pid} llegó en t={p.arrival_time}")
                self.scheduler.submission_complete = True

            submitter = threading.Thread(target=submit_staggered)
            submitter.start()
        else:
            self.scheduler.submission_complete = True

        # Iniciar workers
        for core in cores:
            core.start()

        # Esperar a que terminen
        if staggered:
            submitter.join()
        for core in cores:
            core.join()

        # Tiempo real de simulación: máximo completion_time entre procesos completados
        completed_processes = [p for p in loaded_processes if p.completion_time != -1]
        completed = len(completed_processes)
        total_time = max(p.completion_time for p in completed_processes) if completed_processes else 0
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
        cpu_utilization = min(cpu_utilization, 1.0)

        total_context_switches = sum(core.get_context_switches() for core in cores)

        process_metrics = [
            {
                "pid": p.pid,
                "burst_time": p.burst_time,
                "priority": p.priority,
                "waiting_time": p.waiting_time,
                "turnaround_time": p.turnaround_time,
                "response_time": p.response_time,
            }
            for p in loaded_processes
        ]

        stats = {
            "total_time": total_time,
            "completed": completed,
            "throughput": throughput,
            "avg_waiting_time": avg_waiting,
            "avg_turnaround_time": avg_turnaround,
            "avg_response_time": avg_response,
            "cpu_utilization": cpu_utilization,
            "context_switches": total_context_switches,
            "gantt_chart": gantt.render(self.num_cores),
            "process_metrics": process_metrics,
        }
        if self.on_simulation_end:
            self.on_simulation_end(stats)

        return stats
