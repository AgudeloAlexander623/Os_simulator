# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

"""Tests para las funcionalidades nuevas: llegadas escalonadas, I/O,
paginación y sistema de archivos."""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.process import Process, ProcessState
from core.memory import Memory, MemoryInsufficientError
from core.filesystem import FileSystem
from core.scheduler import FCFSScheduler, SJFScheduler, RoundRobinScheduler
from concurrency.worker import CoreWorker
from controllers.simulation_controller import SimulationController


class TestStaggeredArrivals(unittest.TestCase):
    """Tests para llegadas escalonadas de procesos."""

    def test_process_has_arrival_time(self):
        """Un proceso debe poder tener un tiempo de llegada distinto de cero."""
        p = Process(1, 10, 100)
        p.arrival_time = 5
        self.assertEqual(p.arrival_time, 5)

    def test_controller_staggered_arrivals(self):
        """El controlador debe completar procesos con llegadas escalonadas."""
        controller = SimulationController(
            scheduler_type='round_robin', quantum=2, memory_cap=1000, num_cores=1
        )
        # P1 llega en t=0, P2 llega en t=3
        controller.add_process(1, 4, 100, arrival=0)
        controller.add_process(2, 4, 100, arrival=3)
        stats = controller.start_simulation()

        self.assertEqual(stats['completed'], 2)
        # P1 debería terminar antes que P2
        self.assertLessEqual(stats['total_time'], 12)


class TestIOOperations(unittest.TestCase):
    """Tests para operaciones de I/O en procesos."""

    def test_process_io_operations_consumed(self):
        """Las operaciones de I/O deben consumirse una sola vez."""
        p = Process(1, 10, 100)
        p.io_operations = [3, 5]

        # Primera solicitud de I/O
        io_time = p.request_io()
        self.assertEqual(io_time, 3)
        self.assertEqual(p.state, ProcessState.BLOCKED)
        self.assertEqual(p.total_io_time, 3)
        self.assertEqual(len(p.io_operations), 1)

        # Segunda solicitud de I/O
        io_time = p.request_io()
        self.assertEqual(io_time, 5)
        self.assertEqual(p.total_io_time, 8)
        self.assertEqual(len(p.io_operations), 0)

        # No hay más operaciones
        io_time = p.request_io()
        self.assertEqual(io_time, 0)

    def test_process_execute_blocks_when_io_pending(self):
        """execute() debe poner el proceso en BLOCKED si hay I/O pendiente."""
        p = Process(1, 10, 100)
        p.io_operations = [3]

        p.execute(2)
        self.assertEqual(p.state, ProcessState.BLOCKED)
        self.assertEqual(p.remaining_time, 8)

    def test_process_execute_ready_when_no_io(self):
        """execute() debe poner el proceso en READY si no hay I/O pendiente."""
        p = Process(1, 10, 100)

        p.execute(2)
        self.assertEqual(p.state, ProcessState.READY)

    def test_io_in_simulation(self):
        """Un proceso con I/O debe completar correctamente en simulación."""
        controller = SimulationController(
            scheduler_type='round_robin', quantum=2, memory_cap=1000, num_cores=1
        )
        controller.add_process(1, 6, 100, io_time=2)
        stats = controller.start_simulation()

        self.assertEqual(stats['completed'], 1)


class TestPaging(unittest.TestCase):
    """Tests para el sistema de paginación de memoria."""

    def test_page_allocation(self):
        """La memoria debe asignar páginas correctamente."""
        mem = Memory(200, 50)  # 4 frames
        p = Process(1, 10, 100)  # Necesita 2 páginas
        mem.allocate(p)

        self.assertEqual(mem.used_frames, 2)
        self.assertEqual(len(mem.page_tables), 1)
        pt = mem.get_page_table(1)
        self.assertIsNotNone(pt)
        self.assertEqual(pt.get_num_pages(), 2)
        # Verificar que las páginas tienen frames válidos
        valid_entries = [e for e in pt.entries if e.valid]
        self.assertEqual(len(valid_entries), 2)

    def test_page_eviction_fifo(self):
        """El reemplazo FIFO debe desalojar páginas de procesos huérfanos."""
        mem = Memory(100, 50)  # 2 frames
        p1 = Process(1, 10, 50)
        mem.allocate(p1)
        mem.free(p1)  # Liberar, pero el frame queda en la cola FIFO

        # Ahora asignar un proceso que necesita 2 frames
        p2 = Process(2, 10, 100)
        mem.allocate(p2)  # Debería desalojar el frame huérfano

        self.assertEqual(mem.used_frames, 2)
        self.assertIsNone(mem.get_page_table(1))

    def test_memory_insufficient_no_eviction(self):
        """Si no se pueden desalojar páginas activas, debe fallar."""
        mem = Memory(100, 50)  # 2 frames
        p1 = Process(1, 10, 100)
        mem.allocate(p1)

        # P2 necesita 2 frames pero P1 está activo
        p2 = Process(2, 10, 100)
        with self.assertRaises(MemoryInsufficientError):
            mem.allocate(p2)

    def test_page_table_str(self):
        """La representación textual de la tabla de páginas debe ser legible."""
        mem = Memory(100, 50)
        p = Process(1, 10, 100)
        mem.allocate(p)

        output = mem.page_table_str(1)
        self.assertIn("PID=1", output)
        self.assertIn("Page", output)
        self.assertIn("Frame", output)


class TestFileSystem(unittest.TestCase):
    """Tests para el sistema de archivos básico."""

    def test_create_directory(self):
        """Debe poder crear directorios."""
        fs = FileSystem(1000)
        self.assertTrue(fs.mkdir("/test"))
        self.assertTrue(fs.mkdir("/test/sub"))

    def test_create_and_read_file(self):
        """Debe poder crear y leer archivos."""
        fs = FileSystem(1000)
        fs.mkdir("/data")
        fs.create_file("/data/hello.txt", "Hello World", pid=1)

        content = fs.read_file("/data/hello.txt", pid=1)
        self.assertEqual(content, "Hello World")

    def test_write_file(self):
        """Debe poder escribir en archivos existentes."""
        fs = FileSystem(1000)
        fs.create_file("/log.txt", "old", pid=1)
        fs.write_file("/log.txt", "new content", pid=1)

        content = fs.read_file("/log.txt")
        self.assertEqual(content, "new content")

    def test_delete_file(self):
        """Debe poder eliminar archivos."""
        fs = FileSystem(1000)
        fs.create_file("/tmp.txt", "data", pid=1)
        self.assertTrue(fs.delete("/tmp.txt"))
        self.assertIsNone(fs.read_file("/tmp.txt"))

    def test_list_directory(self):
        """Debe poder listar el contenido de un directorio."""
        fs = FileSystem(1000)
        fs.mkdir("/docs")
        fs.create_file("/docs/readme.txt", "readme", pid=1)
        fs.create_file("/docs/notes.txt", "notes", pid=1)

        entries = fs.list_dir("/docs")
        self.assertEqual(len(entries), 2)

    def test_tree_representation(self):
        """Debe generar una representación en árbol del filesystem."""
        fs = FileSystem(1000)
        fs.mkdir("/src")
        fs.create_file("/src/main.py", "code", pid=1)

        tree = fs.tree()
        self.assertIn("src", tree)
        self.assertIn("main.py", tree)

    def test_filesystem_capacity(self):
        """No debe permitir crear archivos si no hay espacio."""
        fs = FileSystem(50)
        fs.create_file("/big.txt", "x" * 40, pid=1)

        # No hay espacio para otro archivo grande
        self.assertFalse(fs.create_file("/big2.txt", "y" * 40, pid=1))


class TestIntegrationNewFeatures(unittest.TestCase):
    """Tests de integración combinando las nuevas funcionalidades."""

    def test_full_simulation_with_io_and_arrivals(self):
        """Simulación completa con llegadas escalonadas e I/O."""
        controller = SimulationController(
            scheduler_type='round_robin', quantum=2, memory_cap=1000, num_cores=2
        )
        controller.add_process(1, 6, 100, arrival=0, io_time=2)
        controller.add_process(2, 4, 100, arrival=1)
        stats = controller.start_simulation()

        self.assertEqual(stats['completed'], 2)
        self.assertGreater(stats['total_time'], 0)
        self.assertGreater(stats['context_switches'], -1)

    def test_filesystem_used_during_simulation(self):
        """El filesystem debe tener archivos después de una simulación."""
        controller = SimulationController(
            scheduler_type='fcfs', quantum=0, memory_cap=1000, num_cores=1
        )
        controller.add_process(1, 4, 100)
        controller.add_process(2, 6, 100)
        controller.start_simulation()

        # Verificar que se crearon directorios y archivos
        entries = controller.filesystem.list_dir("/processes")
        self.assertEqual(len(entries), 2)

        # Verificar que los logs tienen contenido
        log1 = controller.filesystem.read_file("/processes/P1/status.log")
        self.assertIsNotNone(log1)
        self.assertIn("PID=1", log1)


if __name__ == '__main__':
    unittest.main()
