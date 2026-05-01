import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.process import Process


class MemoryInsufficientError(Exception):
    """Excepción lanzada cuando no hay suficiente memoria."""
    pass


class Memory:
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
        if capacity < 0:
            raise ValueError("Capacity debe ser no negativa")
        self.capacity = capacity
        self.used = 0

    def allocate(self, process: 'Process') -> bool:
        """Asigna memoria para un proceso.

        Args:
            process (Process): Proceso a asignar.

        Returns:
            bool: True si asignado, False si insuficiente.

        Raises:
            MemoryInsufficientError: Si no hay espacio.
        """
        if self.used + process.memory > self.capacity:
            logging.warning(f"Memoria insuficiente para PID={process.pid}")
            raise MemoryInsufficientError(f"No hay suficiente memoria para PID={process.pid}")
        self.used += process.memory
        logging.info(f"[RAM] asignado PID={process.pid}")
        return True

    def free(self, process: 'Process') -> None:
        """Libera memoria de un proceso.

        Args:
            process (Process): Proceso a liberar.
        """
        self.used -= process.memory
        logging.info(f"[RAM] liberado PID={process.pid}")