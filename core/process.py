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

    remaining_time: int = field(init=False)
    state: ProcessState = field(default=ProcessState.READY)
    arrival_time: int = field(default=0)
    start_time: int = field(default=-1)
    completion_time: int = field(default=-1)

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
            quantum (int): Tiempo máximo de ejecución.

        Returns:
            int: Tiempo ejecutado.
        """
        self.state = ProcessState.RUNNING

        executed = min(self.remaining_time, quantum)
        self.remaining_time -= executed

        if self.remaining_time <= 0:
            self.state = ProcessState.TERMINATED
        else:
            self.state = ProcessState.READY

        return executed

    @property
    def waiting_time(self) -> int:
        """Calcula el tiempo de espera.

        Returns:
            int: Tiempo de espera (start_time - arrival_time).
        """
        if self.start_time == -1:
            return 0
        return self.start_time - self.arrival_time

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
            int: Tiempo de respuesta (start_time - arrival_time).
        """
        return self.waiting_time  # Para FCFS, response = waiting