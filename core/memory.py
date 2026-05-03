import logging
from typing import TYPE_CHECKING
from utils.observer import Observable

if TYPE_CHECKING:
    from core.process import Process


class MemoryInsufficientError(Exception):
    """Excepción lanzada cuando no hay suficiente memoria."""
    pass


class Memory(Observable):
    """Gestiona la memoria del sistema OS.

    Atributos:
        capacity (int): Capacidad total de memoria.
        used (int): Memoria actualmente usada.
    """

    def __init__(self, capacity: int):
        """Inicializa la memoria.

        Args:
            capacity (int): Capacidad total.

        Raises:
            ValueError: Si capacity es negativa.
        """
        super().__init__()
        if capacity < 0:
            raise ValueError("Capacity debe ser no negativa")
        self.capacity = capacity
        self.used = 0

    def allocate(self, process: 'Process') -> bool:
        """Asigna memoria para un proceso.

        Args:
            process (Process): Proceso a asignar.

        Returns:
            bool: True si asignado.

        Raises:
            MemoryInsufficientError: Si no hay espacio.
        """
        if self.used + process.memory > self.capacity:
            logging.warning(f"Memoria insuficiente para PID={process.pid}")
            raise MemoryInsufficientError(f"No hay suficiente memoria para PID={process.pid}")
        self.used += process.memory
        logging.info(f"[RAM] asignado PID={process.pid}")
        self.notify({"type": "allocated", "process": process, "used": self.used})
        return True

    def free(self, process: 'Process') -> None:
        """Libera memoria de un proceso.

        Args:
            process (Process): Proceso a liberar.

        Raises:
            ValueError: Si el proceso no fue asignado o doble free.
        """
        if self.used < process.memory:
            logging.warning(f"[RAM] intento liberar PID={process.pid} sin asignación válida")
            raise ValueError(f"PID={process.pid} no tiene memoria asignada o ya fue liberado")
        self.used -= process.memory
        logging.info(f"[RAM] liberado PID={process.pid}")
        self.notify({"type": "freed", "process": process, "used": self.used})