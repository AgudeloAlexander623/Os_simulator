# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

"""Tests para utilidades: config, process_factory, gantt y locks."""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestConfig(unittest.TestCase):
    """Verifica que las configuraciones por defecto son válidas."""

    def test_scheduler_type_is_valid(self):
        from utils import config
        valid = {"fcfs", "sjf", "priority", "round_robin"}
        self.assertIn(config.SCHEDULER_TYPE, valid)

    def test_quantum_is_non_negative(self):
        from utils import config
        self.assertGreaterEqual(config.QUANTUM, 0)

    def test_memory_capacity_is_positive(self):
        from utils import config
        self.assertGreater(config.MEMORY_CAPACITY, 0)

    def test_page_size_is_positive(self):
        from utils import config
        self.assertGreater(config.PAGE_SIZE, 0)

    def test_num_cores_is_at_least_one(self):
        from utils import config
        self.assertGreaterEqual(config.NUM_CORES, 1)

    def test_fs_capacity_is_positive(self):
        from utils import config
        self.assertGreater(config.FS_CAPACITY, 0)

    def test_context_switch_overhead_is_non_negative(self):
        from utils import config
        self.assertGreaterEqual(config.CONTEXT_SWITCH_OVERHEAD, 0)


class TestProcessFactory(unittest.TestCase):
    """sample_processes retorna datos coherentes."""

    def test_returns_non_empty_list(self):
        from utils.process_factory import sample_processes
        procs = sample_processes()
        self.assertIsInstance(procs, list)
        self.assertGreater(len(procs), 0)

    def test_each_process_has_valid_fields(self):
        from utils.process_factory import sample_processes
        for pid, burst, mem, pri, arrival, io_time in sample_processes():
            self.assertGreater(pid, 0)
            self.assertGreater(burst, 0)
            self.assertGreater(mem, 0)
            self.assertGreaterEqual(pri, 0)
            self.assertGreaterEqual(arrival, 0)
            self.assertGreaterEqual(io_time, 0)

    def test_pids_are_unique(self):
        from utils.process_factory import sample_processes
        pids = [p[0] for p in sample_processes()]
        self.assertEqual(len(pids), len(set(pids)))


class TestGanttEdgeCases(unittest.TestCase):
    """Casos borde del diagrama de Gantt."""

    def test_record_with_none_pid(self):
        from utils.gantt import GanttChart
        chart = GanttChart()
        chart.record(0, 0, None)
        result = chart.render(1)
        self.assertIn("Core 0:", result)

    def test_record_with_time_gap(self):
        from utils.gantt import GanttChart
        chart = GanttChart()
        chart.record(0, 0, 1)
        chart.record(5, 0, 1)
        self.assertGreaterEqual(len(chart.timeline), 6)
        self.assertEqual(chart.timeline[0][0], 1)
        self.assertEqual(chart.timeline[5][0], 1)

    def test_render_many_cores(self):
        from utils.gantt import GanttChart
        chart = GanttChart()
        chart.record(0, 0, 1)
        chart.record(0, 7, 8)
        result = chart.render(8)
        lines = result.split("\n")
        self.assertEqual(len(lines), 8)

    def test_render_idle_core(self):
        from utils.gantt import GanttChart
        chart = GanttChart()
        chart.record(0, 0, 1)
        result = chart.render(2)
        self.assertIn("Core 0:", result)
        self.assertIn("Core 1:", result)


class TestLocks(unittest.TestCase):
    """Verifica que los locks existen y son funcionales."""

    def test_scheduler_lock_exists(self):
        from concurrency.lock import scheduler_lock
        self.assertTrue(scheduler_lock.acquire(blocking=False))
        scheduler_lock.release()

    def test_memory_lock_exists(self):
        from concurrency.lock import memory_lock
        self.assertTrue(memory_lock.acquire(blocking=False))
        memory_lock.release()

    def test_locks_are_independent(self):
        from concurrency.lock import scheduler_lock, memory_lock
        scheduler_lock.acquire()
        self.assertTrue(memory_lock.acquire(blocking=False))
        memory_lock.release()
        scheduler_lock.release()


if __name__ == "__main__":
    unittest.main()
