# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

"""Tests para core/process.py.

Cubre creación, ejecución, métricas calculadas, I/O y validaciones.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.process import Process
from core.states import ProcessState


class TestProcessCreation(unittest.TestCase):
    """Creación y validación de procesos."""

    def test_valid_process(self):
        p = Process(1, 10, 100)
        self.assertEqual(p.pid, 1)
        self.assertEqual(p.burst_time, 10)
        self.assertEqual(p.memory, 100)
        self.assertEqual(p.remaining_time, 10)
        self.assertEqual(p.state, ProcessState.READY)
        self.assertEqual(p.priority, 0)
        self.assertEqual(p.arrival_time, 0)
        self.assertEqual(p.start_time, -1)
        self.assertEqual(p.completion_time, -1)
        self.assertEqual(p.first_scheduled_time, -1)

    def test_invalid_pid_zero(self):
        with self.assertRaises(ValueError):
            Process(0, 10, 100)

    def test_invalid_pid_negative(self):
        with self.assertRaises(ValueError):
            Process(-1, 10, 100)

    def test_invalid_burst_time(self):
        with self.assertRaises(ValueError):
            Process(1, 0, 100)

    def test_invalid_burst_time_negative(self):
        with self.assertRaises(ValueError):
            Process(1, -5, 100)

    def test_invalid_memory(self):
        with self.assertRaises(ValueError):
            Process(1, 10, 0)

    def test_invalid_memory_negative(self):
        with self.assertRaises(ValueError):
            Process(1, 10, -50)

    def test_process_with_priority(self):
        p = Process(1, 10, 100, priority=5)
        self.assertEqual(p.priority, 5)

    def test_process_with_arrival(self):
        p = Process(1, 10, 100)
        p.arrival_time = 7
        self.assertEqual(p.arrival_time, 7)


class TestProcessExecution(unittest.TestCase):
    """Ejecución con quantum y transiciones de estado."""

    def test_execute_partial_quantum(self):
        p = Process(1, 10, 100)
        executed = p.execute(3)
        self.assertEqual(executed, 3)
        self.assertEqual(p.remaining_time, 7)
        self.assertEqual(p.state, ProcessState.READY)

    def test_execute_exact_completion(self):
        p = Process(1, 5, 100)
        executed = p.execute(5)
        self.assertEqual(executed, 5)
        self.assertEqual(p.remaining_time, 0)
        self.assertEqual(p.state, ProcessState.TERMINATED)

    def test_execute_quantum_larger_than_remaining(self):
        p = Process(1, 3, 100)
        executed = p.execute(10)
        self.assertEqual(executed, 3)
        self.assertEqual(p.remaining_time, 0)
        self.assertEqual(p.state, ProcessState.TERMINATED)

    def test_execute_fcfs_mode_quantum_zero(self):
        p = Process(1, 7, 100)
        executed = p.execute(0)
        self.assertEqual(executed, 7)
        self.assertEqual(p.remaining_time, 0)
        self.assertEqual(p.state, ProcessState.TERMINATED)

    def test_execute_multiple_times_until_termination(self):
        p = Process(1, 10, 100)
        total = 0
        while p.state != ProcessState.TERMINATED:
            total += p.execute(3)
        self.assertEqual(total, 10)
        self.assertEqual(p.remaining_time, 0)

    def test_execute_sets_running_state(self):
        p = Process(1, 10, 100)
        p.execute(3)
        self.assertEqual(p.state, ProcessState.READY)

    def test_execute_blocks_when_io_pending(self):
        p = Process(1, 10, 100)
        p.io_operations = [3]
        p.execute(2)
        self.assertEqual(p.state, ProcessState.BLOCKED)
        self.assertEqual(p.remaining_time, 8)


class TestProcessMetrics(unittest.TestCase):
    """Métricas calculadas: waiting_time, turnaround_time, response_time.

    Estas propiedades son de solo lectura y se derivan de
    completion_time, arrival_time, burst_time y total_io_time.
    """

    def test_turnaround_time_completed(self):
        p = Process(1, 10, 100)
        p.arrival_time = 2
        p.completion_time = 20
        self.assertEqual(p.turnaround_time, 18)

    def test_turnaround_time_not_completed(self):
        p = Process(1, 10, 100)
        self.assertEqual(p.turnaround_time, 0)

    def test_response_time_scheduled(self):
        p = Process(1, 10, 100)
        p.arrival_time = 3
        p.first_scheduled_time = 7
        self.assertEqual(p.response_time, 4)

    def test_response_time_not_scheduled(self):
        p = Process(1, 10, 100)
        self.assertEqual(p.response_time, 0)

    def test_waiting_time_calculation(self):
        p = Process(1, 10, 100)
        p.arrival_time = 0
        p.completion_time = 20
        p.total_io_time = 5
        self.assertEqual(p.waiting_time, 5)

    def test_waiting_time_not_completed(self):
        p = Process(1, 10, 100)
        self.assertEqual(p.waiting_time, 0)

    def test_waiting_time_cannot_be_negative(self):
        p = Process(1, 10, 100)
        p.arrival_time = 0
        p.completion_time = 8
        p.total_io_time = 100
        self.assertEqual(p.waiting_time, 0)


class TestProcessIO(unittest.TestCase):
    """Operaciones de I/O en procesos."""

    def test_request_io_consumes_first_operation(self):
        p = Process(1, 10, 100)
        p.io_operations = [3, 5]
        io_time = p.request_io()
        self.assertEqual(io_time, 3)
        self.assertEqual(p.state, ProcessState.BLOCKED)
        self.assertEqual(p.total_io_time, 3)
        self.assertEqual(p.io_blocked_time, 3)
        self.assertEqual(len(p.io_operations), 1)

    def test_request_io_second_operation(self):
        p = Process(1, 10, 100)
        p.io_operations = [3, 5]
        p.request_io()
        io_time = p.request_io()
        self.assertEqual(io_time, 5)
        self.assertEqual(p.total_io_time, 8)
        self.assertEqual(len(p.io_operations), 0)

    def test_request_io_no_operations(self):
        p = Process(1, 10, 100)
        io_time = p.request_io()
        self.assertEqual(io_time, 0)
        self.assertEqual(p.state, ProcessState.READY)

    def test_request_io_empty_list(self):
        p = Process(1, 10, 100)
        p.io_operations = []
        io_time = p.request_io()
        self.assertEqual(io_time, 0)


if __name__ == "__main__":
    unittest.main()
