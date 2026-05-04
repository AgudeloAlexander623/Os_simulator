# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

import logging
from typing import TYPE_CHECKING, List, Tuple
from utils.observer import Observable

if TYPE_CHECKING:
    from core.process import Process


class MemoryInsufficientError(Exception):
    """Excepción lanzada cuando no hay suficiente memoria."""
    pass


class MemoryBlock:
    """Representa un bloque de memoria asignado a un proceso."""

    def __init__(self, start: int, size: int, pid: int):
        self.start = start
        self.size = size
        self.pid = pid

    @property
    def end(self) -> int:
        return self.start + self.size


class Memory(Observable):
    """Gestiona la memoria del sistema OS con bloques contiguos.

    Atributos:
        capacity (int): Capacidad total de memoria.
        used (int): Memoria actualmente usada.
        blocks (List[MemoryBlock]): Bloques de memoria asignados.
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
        self.blocks: List[MemoryBlock] = []

    def allocate(self, process: 'Process') -> bool:
        """Asigna memoria para un proceso usando first-fit.

        Args:
            process (Process): Proceso a asignar.

        Returns:
            bool: True si asignado.

        Raises:
            MemoryInsufficientError: Si no hay espacio contiguo.
        """
        if self.used + process.memory > self.capacity:
            logging.warning(f"Memoria insuficiente para PID={process.pid}")
            raise MemoryInsufficientError(f"No hay suficiente memoria para PID={process.pid}")

        addr = self._find_first_fit(process.memory)
        if addr is None:
            logging.warning(f"Fragmentación externa: no hay bloque contiguo para PID={process.pid}")
            raise MemoryInsufficientError(f"No hay bloque contiguo para PID={process.pid}")

        block = MemoryBlock(addr, process.memory, process.pid)
        self.blocks.append(block)
        self.used += process.memory
        logging.info(f"[RAM] asignado PID={process.pid} en [{addr}:{addr + process.memory})")
        self.notify({"type": "allocated", "process": process, "used": self.used})
        return True

    def free(self, process: 'Process') -> None:
        """Libera memoria de un proceso.

        Args:
            process (Process): Proceso a liberar.

        Raises:
            ValueError: Si el proceso no fue asignado o doble free.
        """
        block = next((b for b in self.blocks if b.pid == process.pid), None)
        if block is None:
            logging.warning(f"[RAM] intento liberar PID={process.pid} sin asignación válida")
            raise ValueError(f"PID={process.pid} no tiene memoria asignada o ya fue liberado")

        self.blocks.remove(block)
        self.used -= process.memory
        logging.info(f"[RAM] liberado PID={process.pid}")
        self.notify({"type": "freed", "process": process, "used": self.used})

    def _find_first_fit(self, size: int) -> int:
        """Busca un hueco contiguo usando first-fit.

        Args:
            size: Tamaño necesario.

        Returns:
            Dirección de inicio o None si no hay espacio.
        """
        sorted_blocks = sorted(self.blocks, key=lambda b: b.start)
        candidate = 0

        for block in sorted_blocks:
            if candidate + size <= block.start:
                return candidate
            candidate = max(candidate, block.end)

        if candidate + size <= self.capacity:
            return candidate

        return None

    def fragmentation_external(self) -> int:
        """Calcula la fragmentación externa (espacio libre no contiguo).

        Returns:
            int: Bytes libres totales que no forman un bloque contiguo suficiente.
        """
        free_total = self.capacity - self.used
        max_contiguous = self._largest_free_block()
        return free_total - max_contiguous

    def _largest_free_block(self) -> int:
        """Retorna el tamaño del mayor hueco libre contiguo."""
        sorted_blocks = sorted(self.blocks, key=lambda b: b.start)
        largest = 0
        prev_end = 0

        for block in sorted_blocks:
            gap = block.start - prev_end
            if gap > largest:
                largest = gap
            prev_end = block.end

        tail = self.capacity - prev_end
        if tail > largest:
            largest = tail

        return largest

    def memory_map(self) -> str:
        """Genera un mapa de memoria visual.

        Returns:
            str: Representación textual de los bloques de memoria.
        """
        if not self.blocks:
            return f"[{' ' * 40}] libre={self.capacity}"

        lines = []
        sorted_blocks = sorted(self.blocks, key=lambda b: b.start)
        scale = max(1, self.capacity // 40)

        pos = 0
        for block in sorted_blocks:
            free_gap = block.start - pos
            if free_gap > 0:
                lines.append('.' * (free_gap // scale))
            pid_str = f"P{block.pid}"
            lines.append(pid_str * (block.size // scale))
            pos = block.end

        remaining = self.capacity - pos
        if remaining > 0:
            lines.append('.' * (remaining // scale))

        return f"[{''.join(lines)[:40]:<40}] usado={self.used}/{self.capacity}"
