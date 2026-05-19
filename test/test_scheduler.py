# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.scheduler import FCFSScheduler, SJFScheduler, PriorityScheduler, RoundRobinScheduler
from core.process import Process


class TestSchedulers(unittest.TestCase):
    def test_fcfs_scheduler(self):
        sched = FCFSScheduler()
        p1 = Process(1, 10, 100)
        p2 = Process(2, 5, 100)
        sched.add_process(p1)
        sched.add_process(p2)
        self.assertEqual(sched.get_process(), p1)
        self.assertEqual(sched.get_process(), p2)

    def test_sjf_scheduler(self):
        sched = SJFScheduler(2)
        p1 = Process(1, 10, 100)
        p2 = Process(2, 5, 100)
        sched.add_process(p1)
        sched.add_process(p2)
        self.assertEqual(sched.get_process(), p2)  # SJF: menor burst primero
        self.assertEqual(sched.get_process(), p1)

    def test_priority_scheduler(self):
        sched = PriorityScheduler(2)
        p1 = Process(1, 10, 100, priority=2)
        p2 = Process(2, 5, 100, priority=1)  # Menor priority = mayor prioridad
        sched.add_process(p1)
        sched.add_process(p2)
        self.assertEqual(sched.get_process(), p2)
        self.assertEqual(sched.get_process(), p1)

    def test_round_robin_scheduler(self):
        sched = RoundRobinScheduler(2)
        p1 = Process(1, 10, 100)
        p2 = Process(2, 5, 100)
        sched.add_process(p1)
        sched.add_process(p2)
        self.assertEqual(sched.get_process(), p1)
        sched.add_process(p1)  # Re-add after quantum
        self.assertEqual(sched.get_process(), p2)


if __name__ == '__main__':
    unittest.main()
