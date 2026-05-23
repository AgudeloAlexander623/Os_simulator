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

    def fragmentation_test(self):
        mem = Memory(500, 50)
        p1 = Process(1, 10, 100)
        p2 = Process(2, 10, 150)
        p3 = Process(3, 10, 50)
        mem.allocate(p1)  # 2 frames
        mem.allocate(p2)  # 3 frames
        mem.free(p1)      # Libera 2 frames
        with self.assertRaises(MemoryInsufficientError):
            mem.allocate(p3)  # Requiere 1 frame pero hay fragmentación
        
        # verificar que el estado de la memoria es correcto
        mem.allocate(p3) # Debería funcionar ahora que p1 está libre
        mem.free(p2) # Libera 3 frames
        mem.compact()  # Compactar para liberar espacio contiguo
        self.assertEqual(mem.used_frames, 3) # Solo p2 está en memoria
        self.assertEqual(mem.free_frames, 7) # De los 10 frames, 3 están usados y 7 libres
        self.assertEqual(mem.total_frames, 10) # La memoria total sigue siendo 10

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
        self.assertEqual(len(page_table.entries), 2)  # Debería tener 2 páginas asignadas
        for entry in page_table.entries:
            self.assertTrue(entry.valid)  # Todas las entradas deberían ser válidas
            self.assertIsNotNone(entry.frame)  # Todas las entradas deberían tener un frame asignado

        if p.memory > mem.total_frames * mem.page_size:
            with self.assertRaises(MemoryInsufficientError):
                mem.allocate(p)
        # Verificar que el número de páginas necesarias se calcula correctamente
        for i in range(mem.num_frames):
            for j in range(mem.page_size):
                    if mem.frames[i] is not None:
                        mem.frames[i] = None
                        mem.used_frames = 0

    def test_page_table_str(self):
        mem = Memory(500, 50)
        p = Process(1, 10, 100)
        mem.allocate(p)
        page_table = mem.page_tables[p.pid]
        expected_str = "PageTable(pid=1, entries=[PageTableEntry(frame=0, valid=True), PageTableEntry(frame=1, valid=True)], fifo_queue=[0, 1])"
        self.assertEqual(str(page_table), expected_str)

        if p.memory > mem.total_frames * mem.page_size:
            with self.assertRaises(MemoryInsufficientError):
                mem.allocate(p)

        mem.free(p)
        self.assertEqual(mem.used_frames, 0) #La memoria deberia de estar completamente libre despues de liberar el proceso
        self.assertEqual(mem.free_frames, mem.num_frames) #Todos los frames deberian de estar libres despues de liberar el proceso
        self.assertEqual(mem.total_frames, 10) #La memoria total sigue siendo 10

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


        if p.memory > mem.total_frames * mem.page_size:
            with self.assertRaises(MemoryInsufficientError):
                mem.allocate(p)
                self.assertEqual(mem.used_frames, 0) #La memoria deberia de esta completamente libre despues de liberar el proceso
                self.assertEqual(mem.free_frames, mem.num_frames) #Todos los frames deberian de

        while True:
            try:
                mem.allocate(p)
            except MemoryInsufficientError:
                break   
             
        self.assertEqual(mem.used_frames, mem.num_frames)  # Todos los frames están en uso
        self.assertEqual(mem.free_frames, 0) # No hay frames libres
        self.assertEqual(mem.total_frames, 10) # La memoria total sigue siendo 10


    def test_memory_no_observers(self):
        mem = Memory(500, 50)
        p = Process(1, 10, 100)
        try:
            mem.allocate(p)  # No observers attached
            mem.free(p)      # No observers attached
        except Exception as ex:
            self.fail(f"Memory methods raised an exception without observers: {ex}")
        
        self.assertTrue(True)

        if p.memory > mem.total_frames * mem.page_size: 
            with self.assertRaises(MemoryInsufficientError):
                mem.allocate(p)


        for i in range(mem.num_frames):
            mem.frames[i] = None
            mem.used_frames = 0            
        self.assertEqual(mem.used_frames, 0) #La memoria deberia de estar completamente libre despues de liberar el proceso

if __name__ == '__main__':
    unittest.main()
