# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

"""Tests para funcionalidades extendidas: llegadas escalonadas, I/O,
paginación, sistema de archivos e integración combinada.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.process import Process, ProcessState
from core.memory import Memory, MemoryInsufficientError
from core.filesystem import FileSystem
from core.scheduler import FCFSScheduler, SJFScheduler, RoundRobinScheduler
from concurrency.worker import CoreWorker
from controllers.simulation_controller import SimulationController


class TestStaggeredArrivals(unittest.TestCase):
    """Llegadas escalonadas de procesos."""

    def test_process_has_arrival_time(self):
        p = Process(1, 10, 100)
        p.arrival_time = 5
        self.assertEqual(p.arrival_time, 5)

    def test_controller_staggered_arrivals(self):
        controller = SimulationController(
            scheduler_type="round_robin", quantum=2, memory_cap=1000, num_cores=1,
        )
        controller.add_process(1, 4, 100, arrival=0)
        controller.add_process(2, 4, 100, arrival=3)
        stats = controller.start_simulation()

        self.assertEqual(stats["completed"], 2)
        self.assertLessEqual(stats["total_time"], 12)

    def test_controller_all_arrivals_at_zero(self):
        controller = SimulationController(
            scheduler_type="fcfs", quantum=0, memory_cap=1000, num_cores=1,
        )
        controller.add_process(1, 3, 100, arrival=0)
        controller.add_process(2, 5, 100, arrival=0)
        stats = controller.start_simulation()

        self.assertEqual(stats["completed"], 2)
        self.assertEqual(stats["total_time"], 8)


class TestIOOperations(unittest.TestCase):
    """Operaciones de I/O en procesos."""

    def test_process_io_operations_consumed(self):
        p = Process(1, 10, 100)
        p.io_operations = [3, 5]

        io_time = p.request_io()
        self.assertEqual(io_time, 3)
        self.assertEqual(p.state, ProcessState.BLOCKED)
        self.assertEqual(p.total_io_time, 3)
        self.assertEqual(len(p.io_operations), 1)

        io_time = p.request_io()
        self.assertEqual(io_time, 5)
        self.assertEqual(p.total_io_time, 8)
        self.assertEqual(len(p.io_operations), 0)

        io_time = p.request_io()
        self.assertEqual(io_time, 0)

    def test_process_execute_blocks_when_io_pending(self):
        p = Process(1, 10, 100)
        p.io_operations = [3]
        p.execute(2)
        self.assertEqual(p.state, ProcessState.BLOCKED)
        self.assertEqual(p.remaining_time, 8)

    def test_process_execute_ready_when_no_io(self):
        p = Process(1, 10, 100)
        p.execute(2)
        self.assertEqual(p.state, ProcessState.READY)

    def test_io_in_simulation(self):
        controller = SimulationController(
            scheduler_type="round_robin", quantum=2, memory_cap=1000, num_cores=1,
        )
        controller.add_process(1, 6, 100, io_time=2)
        stats = controller.start_simulation()
        self.assertEqual(stats["completed"], 1)

    def test_io_blocked_time_tracked(self):
        p = Process(1, 10, 100)
        p.io_operations = [4]
        p.request_io()
        self.assertEqual(p.io_blocked_time, 4)


class TestPaging(unittest.TestCase):
    """Sistema de paginación de memoria."""

    def test_page_allocation(self):
        mem = Memory(200, 50)
        p = Process(1, 10, 100)
        mem.allocate(p)

        self.assertEqual(mem.used_frames, 2)
        self.assertEqual(len(mem.page_tables), 1)
        pt = mem.get_page_table(1)
        self.assertIsNotNone(pt)
        self.assertEqual(pt.get_num_pages(), 2)
        valid_entries = [e for e in pt.entries if e.valid]
        self.assertEqual(len(valid_entries), 2)

    def test_free_releases_frames_and_page_table(self):
        mem = Memory(100, 50)
        p1 = Process(1, 10, 50)
        mem.allocate(p1)
        self.assertEqual(mem.used_frames, 1)
        self.assertIsNotNone(mem.get_page_table(1))

        mem.free(p1)
        self.assertEqual(mem.used_frames, 0)
        self.assertIsNone(mem.get_page_table(1))

    def test_frames_reusable_after_free(self):
        mem = Memory(100, 50)
        p1 = Process(1, 10, 100)
        mem.allocate(p1)
        mem.free(p1)

        p2 = Process(2, 10, 100)
        mem.allocate(p2)
        self.assertEqual(mem.used_frames, 2)
        self.assertIsNone(mem.get_page_table(1))
        self.assertIsNotNone(mem.get_page_table(2))

    def test_memory_insufficient_no_eviction(self):
        mem = Memory(100, 50)
        p1 = Process(1, 10, 100)
        mem.allocate(p1)

        p2 = Process(2, 10, 100)
        with self.assertRaises(MemoryInsufficientError):
            mem.allocate(p2)

    def test_page_table_str(self):
        mem = Memory(100, 50)
        p = Process(1, 10, 100)
        mem.allocate(p)
        output = mem.page_table_str(1)
        self.assertIn("PID=1", output)
        self.assertIn("Page", output)
        self.assertIn("Frame", output)

    def test_partial_page_uses_full_frame(self):
        mem = Memory(200, 50)
        p = Process(1, 10, 1)
        mem.allocate(p)
        self.assertEqual(mem.used_frames, 1)


class TestFileSystem(unittest.TestCase):
    """Sistema de archivos básico."""

    def test_create_directory(self):
        fs = FileSystem(1000)
        self.assertTrue(fs.mkdir("/test"))
        self.assertTrue(fs.mkdir("/test/sub"))

    def test_create_duplicate_directory(self):
        fs = FileSystem(1000)
        fs.mkdir("/docs")
        self.assertFalse(fs.mkdir("/docs"))

    def test_create_and_read_file(self):
        fs = FileSystem(1000)
        fs.mkdir("/data")
        fs.create_file("/data/hello.txt", "Hello World", pid=1)
        content = fs.read_file("/data/hello.txt", pid=1)
        self.assertEqual(content, "Hello World")

    def test_create_duplicate_file(self):
        fs = FileSystem(1000)
        fs.create_file("/log.txt", "data", pid=1)
        self.assertFalse(fs.create_file("/log.txt", "other", pid=1))

    def test_write_file(self):
        fs = FileSystem(1000)
        fs.create_file("/log.txt", "old", pid=1)
        fs.write_file("/log.txt", "new content", pid=1)
        content = fs.read_file("/log.txt")
        self.assertEqual(content, "new content")

    def test_write_nonexistent_file(self):
        fs = FileSystem(1000)
        self.assertFalse(fs.write_file("/nope.txt", "data"))

    def test_delete_file(self):
        fs = FileSystem(1000)
        fs.create_file("/tmp.txt", "data", pid=1)
        self.assertTrue(fs.delete("/tmp.txt"))
        self.assertIsNone(fs.read_file("/tmp.txt"))

    def test_delete_nonexistent(self):
        fs = FileSystem(1000)
        self.assertFalse(fs.delete("/nope.txt"))

    def test_delete_directory_with_children(self):
        fs = FileSystem(1000)
        fs.mkdir("/parent")
        fs.create_file("/parent/child.txt", "data", pid=1)
        self.assertTrue(fs.delete("/parent"))
        self.assertIsNone(fs._resolve_path("/parent/child.txt"))

    def test_list_directory(self):
        fs = FileSystem(1000)
        fs.mkdir("/docs")
        fs.create_file("/docs/readme.txt", "readme", pid=1)
        fs.create_file("/docs/notes.txt", "notes", pid=1)
        entries = fs.list_dir("/docs")
        self.assertEqual(len(entries), 2)

    def test_list_nonexistent_directory(self):
        fs = FileSystem(1000)
        entries = fs.list_dir("/nope")
        self.assertEqual(entries, [])

    def test_tree_representation(self):
        fs = FileSystem(1000)
        fs.mkdir("/src")
        fs.create_file("/src/main.py", "code", pid=1)
        tree = fs.tree()
        self.assertIn("src", tree)
        self.assertIn("main.py", tree)

    def test_tree_deep_structure(self):
        fs = FileSystem(1000)
        fs.mkdir("/a")
        fs.mkdir("/a/b")
        fs.mkdir("/a/b/c")
        fs.create_file("/a/b/c/deep.txt", "deep", pid=1)
        tree = fs.tree()
        self.assertIn("a", tree)
        self.assertIn("b", tree)
        self.assertIn("c", tree)
        self.assertIn("deep.txt", tree)

    def test_filesystem_capacity(self):
        fs = FileSystem(50)
        fs.create_file("/big.txt", "x" * 40, pid=1)
        self.assertFalse(fs.create_file("/big2.txt", "y" * 40, pid=1))

    def test_read_directory_returns_none(self):
        fs = FileSystem(1000)
        fs.mkdir("/docs")
        self.assertIsNone(fs.read_file("/docs"))

    def test_file_used_space_tracked(self):
        fs = FileSystem(1000)
        fs.create_file("/file.txt", "hello", pid=1)
        self.assertEqual(fs.used, 5)

    def test_delete_frees_space(self):
        fs = FileSystem(1000)
        fs.create_file("/file.txt", "hello", pid=1)
        fs.delete("/file.txt")
        self.assertEqual(fs.used, 0)


class TestIntegrationNewFeatures(unittest.TestCase):
    """Integración combinando múltiples funcionalidades."""

    def test_full_simulation_with_io_and_arrivals(self):
        controller = SimulationController(
            scheduler_type="round_robin", quantum=2, memory_cap=1000, num_cores=2,
        )
        controller.add_process(1, 6, 100, arrival=0, io_time=2)
        controller.add_process(2, 4, 100, arrival=1)
        stats = controller.start_simulation()

        self.assertEqual(stats["completed"], 2)
        self.assertGreater(stats["total_time"], 0)
        self.assertGreaterEqual(stats["context_switches"], 0)

    def test_filesystem_used_during_simulation(self):
        controller = SimulationController(
            scheduler_type="fcfs", quantum=0, memory_cap=1000, num_cores=1,
        )
        controller.add_process(1, 4, 100)
        controller.add_process(2, 6, 100)
        controller.start_simulation()

        entries = controller.filesystem.list_dir("/processes")
        self.assertEqual(len(entries), 2)

        log1 = controller.filesystem.read_file("/processes/P1/status.log")
        self.assertIsNotNone(log1)
        self.assertIn("PID=1", log1)

    def test_simulation_with_sjf_and_io(self):
        controller = SimulationController(
            scheduler_type="sjf", quantum=2, memory_cap=1000, num_cores=1,
        )
        controller.add_process(1, 8, 100, io_time=1)
        controller.add_process(2, 4, 100)
        stats = controller.start_simulation()
        self.assertEqual(stats["completed"], 2)

    def test_simulation_metrics_are_reasonable(self):
        controller = SimulationController(
            scheduler_type="round_robin", quantum=2, memory_cap=1000, num_cores=1,
        )
        controller.add_process(1, 10, 100)
        controller.add_process(2, 10, 100)
        stats = controller.start_simulation()

        self.assertEqual(stats["completed"], 2)
        self.assertGreater(stats["avg_waiting_time"], 0)
        self.assertGreater(stats["avg_turnaround_time"], 0)
        self.assertGreater(stats["avg_response_time"], 0)
        self.assertGreater(stats["throughput"], 0)
        self.assertGreater(stats["cpu_utilization"], 0)

if __name__ == "__main__":
    unittest.main()
