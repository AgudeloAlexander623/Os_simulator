# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.memory import Memory, MemoryInsufficientError
from core.process import Process


class TestMemory(unittest.TestCase):
    def test_memory_allocation(self):
        mem = Memory(500, 50)
        p = Process(1, 10, 100)
        self.assertTrue(mem.allocate(p))
        self.assertEqual(mem.used_frames, 2)

    def test_memory_insufficient(self):
        mem = Memory(200, 50)
        p = Process(1, 10, 300)
        with self.assertRaises(MemoryInsufficientError):
            mem.allocate(p)
        self.assertEqual(mem.used_frames, 0)

    def test_memory_free(self):
        mem = Memory(500, 50)
        p = Process(1, 10, 100)
        mem.allocate(p)
        mem.free(p)
        self.assertEqual(mem.used_frames, 0)


if __name__ == '__main__':
    unittest.main()
