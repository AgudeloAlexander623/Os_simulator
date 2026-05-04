# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

import unittest
import sys
import os

# Ajustar path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.process import Process
from core.states import ProcessState


class TestProcess(unittest.TestCase):
    def test_process_creation(self):
        p = Process(1, 10, 100)
        self.assertEqual(p.pid, 1)
        self.assertEqual(p.burst_time, 10)
        self.assertEqual(p.memory, 100)
        self.assertEqual(p.remaining_time, 10)
        self.assertEqual(p.state, ProcessState.READY)

    def test_process_execute(self):
        p = Process(1, 10, 100)
        executed = p.execute(3)
        self.assertEqual(executed, 3)
        self.assertEqual(p.remaining_time, 7)
        self.assertEqual(p.state, ProcessState.READY)

    def test_process_terminate(self):
        p = Process(1, 2, 100)
        executed = p.execute(2)
        self.assertEqual(executed, 2)
        self.assertEqual(p.remaining_time, 0)
        self.assertEqual(p.state, ProcessState.TERMINATED)


if __name__ == '__main__':
    unittest.main()