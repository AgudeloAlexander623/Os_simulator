# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

"""Tests para core/scheduler.py.

Cubre FCFS, SJF, Priority, Round-Robin, colas de I/O,
eventos de submission y manipulación de prioridad.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scheduler import (
    FCFSScheduler,
    SJFScheduler,
    PriorityScheduler,
    RoundRobinScheduler,
)
from core.process import Process


class TestFCFSScheduler(unittest.TestCase):
    """First-Come, First-Served: orden de llegada, sin quantum."""

    def test_orders_by_arrival(self):
        sched = FCFSScheduler()
        p1 = Process(1, 10, 100)
        p2 = Process(2, 5, 100)
        sched.add_process(p1)
        sched.add_process(p2)
        self.assertIs(sched.get_process(), p1)
        self.assertIs(sched.get_process(), p2)

    def test_empty_queue_returns_none(self):
        sched = FCFSScheduler()
        self.assertIsNone(sched.get_process())

    def test_default_quantum_is_zero(self):
        sched = FCFSScheduler()
        self.assertEqual(sched.quantum, 0)


class TestSJFScheduler(unittest.TestCase):
    """Shortest Job First: menor remaining_time primero."""

    def test_orders_by_shortest_burst(self):
        sched = SJFScheduler(quantum=2)
        p1 = Process(1, 10, 100)
        p2 = Process(2, 5, 100)
        p3 = Process(3, 3, 100)
        sched.add_process(p1)
        sched.add_process(p2)
        sched.add_process(p3)

        self.assertIs(sched.get_process(), p3)
        self.assertIs(sched.get_process(), p2)
        self.assertIs(sched.get_process(), p1)

    def test_reorders_after_partial_execution(self):
        sched = SJFScheduler(quantum=2)
        p1 = Process(1, 10, 100)
        p2 = Process(2, 3, 100)

        sched.add_process(p1)
        sched.add_process(p2)

        first = sched.get_process()
        self.assertIs(first, p2)

        p2.execute(2)
        sched.add_process(p2)

        second = sched.get_process()
        self.assertIs(second, p2)

    def test_empty_queue_returns_none(self):
        sched = SJFScheduler(quantum=2)
        self.assertIsNone(sched.get_process())


class TestPriorityScheduler(unittest.TestCase):
    """Priority: menor número = mayor prioridad."""

    def test_orders_by_priority(self):
        sched = PriorityScheduler(quantum=2)
        p1 = Process(1, 10, 100, priority=2)
        p2 = Process(2, 5, 100, priority=1)
        p3 = Process(3, 3, 100, priority=0)
        sched.add_process(p1)
        sched.add_process(p2)
        sched.add_process(p3)

        self.assertIs(sched.get_process(), p3)
        self.assertIs(sched.get_process(), p2)
        self.assertIs(sched.get_process(), p1)

    def test_update_priority(self):
        sched = PriorityScheduler(quantum=2)
        p1 = Process(1, 10, 100, priority=5)
        p2 = Process(2, 5, 100, priority=1)
        sched.add_process(p1)
        sched.add_process(p2)

        sched.update_process_priority(p1, 0)

        self.assertIs(sched.get_process(), p1)
        self.assertIs(sched.get_process(), p2)

    def test_remove_process(self):
        sched = PriorityScheduler(quantum=2)
        p1 = Process(1, 10, 100, priority=2)
        p2 = Process(2, 5, 100, priority=1)
        p3 = Process(3, 3, 100, priority=0)
        sched.add_process(p1)
        sched.add_process(p2)
        sched.add_process(p3)

        sched.remove_process(2)

        self.assertIs(sched.get_process(), p3)
        self.assertIs(sched.get_process(), p1)

    def test_remove_nonexistent_process(self):
        sched = PriorityScheduler(quantum=2)
        p1 = Process(1, 10, 100)
        sched.add_process(p1)

        sched.remove_process(999)

        self.assertIs(sched.get_process(), p1)


class TestRoundRobinScheduler(unittest.TestCase):
    """Round-Robin: quantum fijo, FIFO."""

    def test_fifo_order(self):
        sched = RoundRobinScheduler(quantum=2)
        p1 = Process(1, 10, 100)
        p2 = Process(2, 5, 100)
        sched.add_process(p1)
        sched.add_process(p2)
        self.assertIs(sched.get_process(), p1)
        sched.add_process(p1)
        self.assertIs(sched.get_process(), p2)

    def test_custom_quantum(self):
        sched = RoundRobinScheduler(quantum=4)
        self.assertEqual(sched.quantum, 4)


class TestSchedulerCommonBehavior(unittest.TestCase):
    """Comportamiento compartido por todos los schedulers."""

    def test_has_processes_empty(self):
        sched = FCFSScheduler()
        self.assertFalse(sched.has_processes())

    def test_has_processes_after_add(self):
        sched = FCFSScheduler()
        sched.add_process(Process(1, 10, 100))
        self.assertTrue(sched.has_processes())

    def test_has_processes_after_get(self):
        sched = FCFSScheduler()
        sched.add_process(Process(1, 10, 100))
        sched.get_process()
        self.assertFalse(sched.has_processes())

    def test_mark_terminated_decrements_counter(self):
        sched = FCFSScheduler()
        sched.add_process(Process(1, 10, 100))
        self.assertEqual(sched._active_count, 1)
        sched.mark_terminated()
        self.assertEqual(sched._active_count, 0)

    def test_has_active_processes(self):
        sched = FCFSScheduler()
        self.assertFalse(sched.has_active_processes())
        sched.add_process(Process(1, 10, 100))
        self.assertTrue(sched.has_active_processes())
        sched.mark_terminated()
        self.assertFalse(sched.has_active_processes())

    def test_submission_complete_default(self):
        sched = FCFSScheduler()
        self.assertTrue(sched.submission_complete.is_set())

    def test_submission_complete_can_be_cleared(self):
        sched = FCFSScheduler()
        sched.submission_complete.clear()
        self.assertFalse(sched.submission_complete.is_set())

    def test_io_queue_operations(self):
        sched = FCFSScheduler()
        p1 = Process(1, 10, 100)
        self.assertFalse(sched.has_io_processes())
        sched.add_to_io_queue(p1)
        self.assertTrue(sched.has_io_processes())
        retrieved = sched.get_process()
        self.assertIs(retrieved, p1)
        self.assertFalse(sched.has_io_processes())

    def test_io_queue_priority_over_ready_queue(self):
        sched = FCFSScheduler()
        p_ready = Process(1, 10, 100)
        p_io = Process(2, 5, 100)
        sched.add_process(p_ready)
        sched.add_to_io_queue(p_io)

        first = sched.get_process()
        self.assertIs(first, p_io)


if __name__ == "__main__":
    unittest.main()
