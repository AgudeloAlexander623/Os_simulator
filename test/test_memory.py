# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

"""Tests para core/memory.py.

Cubre asignación, liberación, doble free, fragmentación,
mapa de memoria, tablas de páginas y casos borde.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.memory import Memory, MemoryInsufficientError
from core.process import Process


class TestMemoryAllocation(unittest.TestCase):
    """Asignación de memoria con paginación."""

    def test_basic_allocation(self):
        mem = Memory(500, 50)
        p = Process(1, 10, 100)
        self.assertTrue(mem.allocate(p))
        self.assertEqual(mem.used_frames, 2)

    def test_allocation_exact_page_size(self):
        mem = Memory(200, 50)
        p = Process(1, 10, 50)
        mem.allocate(p)
        self.assertEqual(mem.used_frames, 1)

    def test_allocation_partial_page_rounds_up(self):
        mem = Memory(200, 50)
        p = Process(1, 10, 1)
        mem.allocate(p)
        self.assertEqual(mem.used_frames, 1)

    def test_allocation_multiple_processes(self):
        mem = Memory(500, 50)
        p1 = Process(1, 10, 100)
        p2 = Process(2, 10, 150)
        p3 = Process(3, 10, 50)
        mem.allocate(p1)
        mem.allocate(p2)
        mem.allocate(p3)
        self.assertEqual(mem.used_frames, 6)

    def test_allocation_fills_all_frames(self):
        mem = Memory(100, 50)
        p1 = Process(1, 10, 50)
        p2 = Process(2, 10, 50)
        mem.allocate(p1)
        mem.allocate(p2)
        self.assertEqual(mem.used_frames, 2)
        self.assertEqual(mem.used_frames, mem.num_frames)

    def test_insufficient_memory_raises(self):
        mem = Memory(200, 50)
        p = Process(1, 10, 300)
        with self.assertRaises(MemoryInsufficientError):
            mem.allocate(p)
        self.assertEqual(mem.used_frames, 0)

    def test_insufficient_memory_after_partial_allocation(self):
        mem = Memory(100, 50)
        p1 = Process(1, 10, 100)
        p2 = Process(2, 10, 100)
        mem.allocate(p1)
        with self.assertRaises(MemoryInsufficientError):
            mem.allocate(p2)
        self.assertEqual(mem.used_frames, 2)


class TestMemoryFree(unittest.TestCase):
    """Liberación de memoria."""

    def test_free_allocated_process(self):
        mem = Memory(500, 50)
        p = Process(1, 10, 100)
        mem.allocate(p)
        mem.free(p)
        self.assertEqual(mem.used_frames, 0)

    def test_free_multiple_processes(self):
        mem = Memory(500, 50)
        p1 = Process(1, 10, 100)
        p2 = Process(2, 10, 150)
        mem.allocate(p1)
        mem.allocate(p2)
        mem.free(p1)
        self.assertEqual(mem.used_frames, 3)
        mem.free(p2)
        self.assertEqual(mem.used_frames, 0)

    def test_free_in_reverse_order(self):
        mem = Memory(500, 50)
        p1 = Process(1, 10, 100)
        p2 = Process(2, 10, 150)
        mem.allocate(p1)
        mem.allocate(p2)
        mem.free(p2)
        self.assertEqual(mem.used_frames, 2)

    def test_double_free_raises(self):
        mem = Memory(500, 50)
        p = Process(1, 10, 100)
        mem.allocate(p)
        mem.free(p)
        with self.assertRaises(ValueError):
            mem.free(p)

    def test_free_never_allocated_raises(self):
        mem = Memory(500, 50)
        p = Process(1, 10, 100)
        with self.assertRaises(ValueError):
            mem.free(p)


class TestMemoryPageTable(unittest.TestCase):
    """Tablas de páginas por proceso."""

    def test_page_table_created_on_allocate(self):
        mem = Memory(200, 50)
        p = Process(1, 10, 100)
        mem.allocate(p)
        pt = mem.get_page_table(1)
        self.assertIsNotNone(pt)
        self.assertEqual(pt.get_num_pages(), 2)

    def test_page_table_entries_are_valid(self):
        mem = Memory(200, 50)
        p = Process(1, 10, 100)
        mem.allocate(p)
        pt = mem.get_page_table(1)
        valid = [e for e in pt.entries if e.valid]
        self.assertEqual(len(valid), 2)

    def test_page_table_removed_on_free(self):
        mem = Memory(200, 50)
        p = Process(1, 10, 100)
        mem.allocate(p)
        mem.free(p)
        self.assertIsNone(mem.get_page_table(1))

    def test_page_table_nonexistent_pid(self):
        mem = Memory(200, 50)
        self.assertIsNone(mem.get_page_table(999))

    def test_page_table_str_format(self):
        mem = Memory(100, 50)
        p = Process(1, 10, 100)
        mem.allocate(p)
        output = mem.page_table_str(1)
        self.assertIn("PID=1", output)
        self.assertIn("Page", output)
        self.assertIn("Frame", output)

    def test_page_table_str_nonexistent_pid(self):
        mem = Memory(100, 50)
        output = mem.page_table_str(999)
        self.assertIn("no tiene tabla", output)


class TestMemoryFragmentation(unittest.TestCase):
    """Cálculo de fragmentación externa."""

    def test_no_fragmentation_when_empty(self):
        mem = Memory(200, 50)
        self.assertEqual(mem.fragmentation_external(), 0)

    def test_no_fragmentation_when_full(self):
        mem = Memory(100, 50)
        p1 = Process(1, 10, 50)
        p2 = Process(2, 10, 50)
        mem.allocate(p1)
        mem.allocate(p2)
        self.assertEqual(mem.fragmentation_external(), 0)

    def test_fragmentation_with_scattered_free_frames(self):
        mem = Memory(300, 50)
        p1 = Process(1, 10, 50)
        p2 = Process(2, 10, 50)
        p3 = Process(3, 10, 50)
        mem.allocate(p1)
        mem.allocate(p2)
        mem.allocate(p3)
        mem.free(p2)
        frag = mem.fragmentation_external()
        self.assertGreaterEqual(frag, 0)

    def test_largest_free_block_empty(self):
        mem = Memory(200, 50)
        self.assertEqual(mem._largest_free_block(), 4)

    def test_largest_free_block_partial(self):
        mem = Memory(200, 50)
        p = Process(1, 10, 100)
        mem.allocate(p)
        self.assertEqual(mem._largest_free_block(), 2)


class TestMemoryMap(unittest.TestCase):
    """Representación visual de la memoria."""

    def test_memory_map_empty(self):
        mem = Memory(200, 50)
        result = mem.memory_map()
        self.assertIn("usado=0/4", result)

    def test_memory_map_with_process(self):
        mem = Memory(200, 50)
        p = Process(1, 10, 100)
        mem.allocate(p)
        result = mem.memory_map()
        self.assertIn("P1", result)
        self.assertIn("usado=2/4", result)

    def test_memory_map_after_free(self):
        mem = Memory(200, 50)
        p = Process(1, 10, 100)
        mem.allocate(p)
        mem.free(p)
        result = mem.memory_map()
        self.assertNotIn("P1", result)
        self.assertIn("usado=0/4", result)


class TestMemoryEdgeCases(unittest.TestCase):
    """Casos borde y validaciones."""

    def test_zero_capacity(self):
        mem = Memory(0, 50)
        self.assertEqual(mem.num_frames, 0)
        self.assertEqual(mem.used_frames, 0)

    def test_negative_capacity_raises(self):
        with self.assertRaises(ValueError):
            Memory(-100, 50)

    def test_invalid_page_size_raises(self):
        with self.assertRaises(ValueError):
            Memory(500, 0)

    def test_large_page_size(self):
        mem = Memory(500, 500)
        self.assertEqual(mem.num_frames, 1)

    def test_memory_capacity_property(self):
        mem = Memory(1000, 50)
        self.assertEqual(mem.capacity, 1000)

    def test_allocate_after_free_reuses_frames(self):
        mem = Memory(100, 50)
        p1 = Process(1, 10, 50)
        p2 = Process(2, 10, 50)
        mem.allocate(p1)
        mem.free(p1)
        mem.allocate(p2)
        self.assertEqual(mem.used_frames, 1)
        self.assertIsNotNone(mem.get_page_table(2))


if __name__ == "__main__":
    unittest.main()
