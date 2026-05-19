# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

from dataclasses import dataclass, field
from core.states import ProcessState


@dataclass
class Process:
    """Representa un proceso en el simulador OS.

    Atributos:
        pid (int): Identificador único del proceso.
        burst_time (int): Tiempo total de ejecución requerido.
        memory (int): Memoria requerida por el proceso.
        priority (int): Prioridad del proceso (menor número = mayor prioridad).
        remaining_time (int): Tiempo restante de ejecución.
        state (ProcessState): Estado actual del proceso.
        arrival_time (int): Tiempo de llegada al sistema.
        start_time (int): Tiempo cuando comenzó ejecución.
        completion_time (int): Tiempo cuando terminó ejecución.
    """
    pid: int
    burst_time: int
    memory: int
    priority: int = 0
    arrival_time: int = 0
    io_operations: list = field(default_factory=list)

    remaining_time: int = field(init=False)
    state: ProcessState = field(default=ProcessState.READY)
    start_time: int = field(default=-1)
    completion_time: int = field(default=-1)
    first_scheduled_time: int = field(default=-1)
    io_blocked_time: int = field(default=0)
    total_io_time: int = field(default=0)

    def __post_init__(self) -> None:
        """Inicializa remaining_time y valida atributos."""
        if self.pid <= 0:
            raise ValueError("PID debe ser positivo")
        if self.burst_time <= 0:
            raise ValueError("Burst time debe ser positivo")
        if self.memory <= 0:
            raise ValueError("Memory debe ser positiva")
        self.remaining_time = self.burst_time

    def execute(self, quantum: int) -> int:
        """Ejecuta el proceso por un quantum de tiempo.

        Args:
            quantum (int): Tiempo máximo de ejecución (0 = ejecuta todo, FCFS).

        Returns:
            int: Tiempo ejecutado.
        """
        self.state = ProcessState.RUNNING

        executed = self.remaining_time if quantum == 0 else min(self.remaining_time, quantum)
        self.remaining_time -= executed

        if self.remaining_time <= 0:
            self.state = ProcessState.TERMINATED
        elif self.io_operations:
            self.state = ProcessState.BLOCKED
        else:
            self.state = ProcessState.READY

        return executed

    @property
    def waiting_time(self) -> int:
        """Calcula el tiempo de espera.

        Fórmula estándar: turnaround_time - burst_time.
        Esto incluye todo el tiempo en cola READY (incluyendo re-encolados).

        Returns:
            int: Tiempo de espera total.
        """
        tt = self.turnaround_time
        return tt - self.burst_time if tt > 0 else 0

    @property
    def turnaround_time(self) -> int:
        """Calcula el tiempo de turnaround.

        Returns:
            int: Tiempo total (completion_time - arrival_time).
        """
        if self.completion_time == -1:
            return 0
        return self.completion_time - self.arrival_time

    @property
    def response_time(self) -> int:
        """Calcula el tiempo de respuesta.

        Returns:
            int: Tiempo de respuesta (first_scheduled_time - arrival_time).
        """
        if self.first_scheduled_time == -1:
            return 0
        return self.first_scheduled_time - self.arrival_time

    def request_io(self) -> int:
        """Solicita operación de I/O.

        Consume la primera operación pendiente de la cola de I/O.
        Si no hay operaciones, retorna 0.

        Returns:
            int: Tiempo de I/O consumido, 0 si no hay operaciones.
        """
        if self.io_operations:
            io_time = self.io_operations.pop(0)
            self.state = ProcessState.BLOCKED
            self.io_blocked_time = io_time
            self.total_io_time += io_time
            return io_time
        return 0
