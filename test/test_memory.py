# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

"""Tests para core/memory.py.

Cubre asignación y liberación de frames, insuficiencia de memoria,
fragmentación externa, bloque libre más grande, tabla de páginas,
mapeo de memoria, notificaciones del patrón Observer, y casos sin
observadores suscritos.
"""

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

    def test_fragmentation_external_calculation(self):
        mem = Memory(500, 50)
        p1 = Process(1, 10, 100)
        p2 = Process(2, 10, 150)
        mem.allocate(p1)
        mem.allocate(p2)
        mem.free(p1)
        frag = mem.fragmentation_external()
        self.assertGreaterEqual(frag, 0)

    def test_largest_free_block(self):
        mem = Memory(500, 50)
        p1 = Process(1, 10, 100)
        p2 = Process(2, 10, 150)
        mem.allocate(p1)  # 2 frames
        mem.allocate(p2)  # 3 frames
        mem.free(p1)      # Libera 2 frames
        largest_block = mem._largest_free_block()
        self.assertEqual(largest_block, 5)  # De los 10 frames, el bloque más grande es de 5 frames
        
        # liberar p2 y verificar que el bloque más grande ahora es de 10 frames
        mem.free(p2)
        largest_block = mem._largest_free_block()
        self.assertEqual(largest_block, 10)
        self.assertEqual(mem.used_frames, 0)
        self.assertEqual(mem.free_frames, 10)
        self.assertEqual(mem.total_frames, 10)

        self.assertEqual(mem.fragmentation_external(), 0) # Sin fragmentación externa después de liberar todo

    def test_memory_insufficient_after_allocation(self):
        mem = Memory(200, 50)
        p1 = Process(1, 10, 100)
        p2 = Process(2, 10, 150)
        mem.allocate(p1)  # 2 frames, quedan 2 libres

        with self.assertRaises(MemoryInsufficientError):
            mem.allocate(p2)  # Requiere 3 frames, solo quedan 2
        self.assertEqual(mem.used_frames, 2)
        self.assertEqual(mem.free_frames, 2)
        self.assertEqual(mem.total_frames, 4)

        mem.free(p1)
        self.assertTrue(mem.allocate(p2))
        self.assertEqual(mem.used_frames, 3)
        self.assertEqual(mem.free_frames, 1)
        self.assertEqual(mem.total_frames, 4)

    def test_memory_insufficient_after_allocation_and_free(self):
        mem = Memory(200, 50)
        p1 = Process(1, 10, 100)
        mem.allocate(p1)
        mem.free(p1)

        self.assertEqual(mem.used_frames, 0)
        self.assertEqual(mem.free_frames, 4)
        self.assertEqual(mem.total_frames, 4)

        p2 = Process(2, 10, 150)
        self.assertTrue(mem.allocate(p2))
        self.assertEqual(mem.used_frames, 3)
        self.assertEqual(mem.free_frames, 1)
        self.assertEqual(mem.total_frames, 4)

        mem.free(p2)
        self.assertEqual(mem.used_frames, 0)
        self.assertEqual(mem.free_frames, 4)
        self.assertEqual(mem.total_frames, 4)

        for i in range(mem.num_frames):
            mem.frames[i] = None
            mem.used_frames = 0

        self.assertEqual(mem.used_frames, 0)
        self.assertEqual(mem.free_frames, 4)
        self.assertEqual(mem.total_frames, 4)

    def test_memory_mapping(self):
        mem = Memory(500, 50)
        p = Process(1, 10, 100)
        mem.allocate(p)
        page_table = mem.page_tables[p.pid]
        self.assertEqual(len(page_table.entries), 2)
        for entry in page_table.entries:
            self.assertTrue(entry.valid)
            self.assertIsNotNone(entry.frame)

    def test_page_table_str(self):
        mem = Memory(500, 50)
        p = Process(1, 10, 100)
        mem.allocate(p)
        page_table = mem.page_tables[p.pid]
        expected_str = "PageTable(pid=1, entries=[PageTableEntry(frame=0, valid=True), PageTableEntry(frame=1, valid=True)], fifo_queue=[0, 1])"
        self.assertEqual(str(page_table), expected_str)

        mem.free(p)
        self.assertEqual(mem.used_frames, 0)
        self.assertEqual(mem.free_frames, mem.num_frames)
        self.assertEqual(mem.total_frames, mem.num_frames)

    def test_memory_observer_notification(self):
        events = []
        mem = Memory(500, 50)
        mem.attach(lambda e: events.append(e))
        p = Process(1, 10, 100)
        mem.allocate(p)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "allocated")
        self.assertEqual(events[0]["process"], p)
        self.assertEqual(events[0]["used"], 2)

        mem.free(p)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[1]["type"], "freed")
        self.assertEqual(events[1]["process"], p)
        self.assertEqual(events[1]["used"], 0)


    def test_memory_no_observers(self):
        mem = Memory(500, 50)
        p = Process(1, 10, 100)
        try:
            mem.allocate(p)
            mem.free(p)
        except Exception as ex:
            self.fail(f"Memory methods raised an exception without observers: {ex}")

        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
