# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

import logging
from typing import TYPE_CHECKING, List, Dict, Optional
from utils.observer import Observable

if TYPE_CHECKING:
    from core.process import Process


class MemoryInsufficientError(Exception):
    """Excepción lanzada cuando no hay suficiente memoria."""
    pass


class PageTableEntry:
    """Representa una entrada en la tabla de páginas."""

    def __init__(self, frame: int = -1, valid: bool = False):
        self.frame = frame
        self.valid = valid


class PageTable:
    """Tabla de páginas para un proceso."""

    def __init__(self, num_pages: int):
        self.entries: List[PageTableEntry] = [PageTableEntry() for _ in range(num_pages)]
        self.fifo_queue: List[int] = []

    def get_num_pages(self) -> int:
        return len(self.entries)


class Memory(Observable):
    """Gestiona la memoria del sistema OS con paginación.

    Atributos:
        capacity (int): Capacidad total de memoria.
        page_size (int): Tamaño de cada página.
        num_frames (int): Número total de frames.
        frames (List[Optional[int]]): Frames físicos (None = libre).
        page_tables (Dict[int, PageTable]): Tablas de páginas por PID.
    """

    def __init__(self, capacity: int, page_size: int = 50):
        """Inicializa la memoria.

        Args:
            capacity (int): Capacidad total.
            page_size (int): Tamaño de página.

        Raises:
            ValueError: Si capacity es negativa o page_size inválida.
        """
        super().__init__()
        if capacity < 0:
            raise ValueError("Capacity debe ser no negativa")
        if page_size <= 0:
            raise ValueError("Page size debe ser positiva")

        self.capacity = capacity
        self.page_size = page_size
        self.num_frames = capacity // page_size
        self.frames: List[Optional[int]] = [None] * self.num_frames
        self.page_tables: Dict[int, PageTable] = {}
        self.used_frames = 0

    def allocate(self, process: 'Process') -> bool:
        """Asigna memoria para un proceso usando paginación.

        Args:
            process (Process): Proceso a asignar.

        Returns:
            bool: True si asignado.

        Raises:
            MemoryInsufficientError: Si no hay frames suficientes.
        """
        num_pages = (process.memory + self.page_size - 1) // self.page_size

        if self.used_frames + num_pages > self.num_frames:
            logging.warning(f"Memoria insuficiente para PID={process.pid}")
            raise MemoryInsufficientError(f"No hay suficiente memoria para PID={process.pid}")

        page_table = PageTable(num_pages)
        allocated = 0
        page_idx = 0

        for i in range(self.num_frames):
            if self.frames[i] is None:
                self.frames[i] = process.pid
                page_table.entries[page_idx].frame = i
                page_table.entries[page_idx].valid = True
                page_table.fifo_queue.append(i)
                allocated += 1
                page_idx += 1
                if allocated == num_pages:
                    break

        self.page_tables[process.pid] = page_table
        self.used_frames += num_pages
        logging.info(f"[RAM] asignado PID={process.pid} en {num_pages} páginas ({process.memory} bytes)")
        self.notify({"type": "allocated", "process": process, "used": self.used_frames})
        return True

    def free(self, process: 'Process') -> None:
        """Libera memoria de un proceso.

        Args:
            process (Process): Proceso a liberar.

        Raises:
            ValueError: Si el proceso no fue asignado o doble free.
        """
        if process.pid not in self.page_tables:
            logging.warning(f"[RAM] intento liberar PID={process.pid} sin asignación válida")
            raise ValueError(f"PID={process.pid} no tiene memoria asignada o ya fue liberado")

        page_table = self.page_tables[process.pid]
        freed = 0

        for i in range(self.num_frames):
            if self.frames[i] == process.pid:
                self.frames[i] = None
                freed += 1

        del self.page_tables[process.pid]
        self.used_frames -= freed
        logging.info(f"[RAM] liberado PID={process.pid} ({freed} frames)")
        self.notify({"type": "freed", "process": process, "used": self.used_frames})

    def fragmentation_external(self) -> int:
        """Calcula la fragmentación externa (frames libres no contiguos).

        Returns:
            int: Bytes libres que no forman un bloque contiguo suficiente.
        """
        free_frames = self.num_frames - self.used_frames
        max_contiguous = self._largest_free_block()
        return (free_frames - max_contiguous) * self.page_size

    def _largest_free_block(self) -> int:
        """Retorna el número mayor de frames libres contiguos."""
        largest = 0
        current = 0

        for frame in self.frames:
            if frame is None:
                current += 1
                if current > largest:
                    largest = current
            else:
                current = 0

        return largest

    def memory_map(self) -> str:
        """Genera un mapa de memoria visual.

        Returns:
            str: Representación textual de los frames de memoria.
        """
        lines = []
        scale = max(1, self.num_frames // 40)

        pos = 0
        for frame in self.frames:
            if frame is None:
                lines.append('.')
            else:
                lines.append(f'P{frame}')
            pos += 1

        return f"[{''.join(lines)[:40]:<40}] usado={self.used_frames}/{self.num_frames} frames"

    def get_page_table(self, pid: int) -> Optional[PageTable]:
        """Retorna la tabla de páginas de un proceso.

        Args:
            pid (int): PID del proceso.

        Returns:
            Optional[PageTable]: Tabla de páginas o None.
        """
        return self.page_tables.get(pid)

    def page_table_str(self, pid: int) -> str:
        """Genera una representación textual de la tabla de páginas.

        Args:
            pid (int): PID del proceso.

        Returns:
            str: Tabla de páginas formateada.
        """
        page_table = self.get_page_table(pid)
        if not page_table:
            return f"PID={pid} no tiene tabla de páginas"

        lines = [f"Page Table for PID={pid}"]
        lines.append(f"{'Page':<6} {'Frame':<6} {'Valid':<6}")
        lines.append("-" * 20)

        for i, entry in enumerate(page_table.entries):
            lines.append(f"{i:<6} {entry.frame:<6} {'Y' if entry.valid else 'N':<6}")

        return "\n".join(lines)
