# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

"""Tests para utils/observer.py y su integración con Memory.

Verifica attach, detach, notify, múltiples observadores
y que un observador defectuoso no rompa la cadena.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.observer import Observable


class TestObserver(unittest.TestCase):
    """Tests unitarios del patrón Observer."""

    def test_attach_and_notify(self):
        observable = Observable()
        events = []
        observable.attach(lambda e: events.append(e))
        observable.notify({"type": "test"})
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "test")

    def test_detach_observer(self):
        observable = Observable()
        events = []
        callback = lambda e: events.append(e)
        observable.attach(callback)
        observable.notify(1)
        observable.detach(callback)
        observable.notify(2)
        self.assertEqual(len(events), 1)

    def test_detach_nonexistent_observer(self):
        observable = Observable()
        observable.detach(lambda e: None)

    def test_multiple_observers(self):
        observable = Observable()
        events = []
        observable.attach(lambda e: events.append(("a", e)))
        observable.attach(lambda e: events.append(("b", e)))
        observable.notify("data")
        self.assertEqual(len(events), 2)

    def test_notify_with_none(self):
        observable = Observable()
        received = []
        observable.attach(lambda e: received.append(e))
        observable.notify(None)
        self.assertEqual(received, [None])

    def test_notify_with_different_types(self):
        observable = Observable()
        received = []
        observable.attach(lambda e: received.append(e))
        observable.notify("string")
        observable.notify(42)
        observable.notify({"key": "value"})
        self.assertEqual(received, ["string", 42, {"key": "value"}])

    def test_observer_exception_does_not_break_chain(self):
        observable = Observable()
        received = []

        def faulty_observer(e):
            raise ValueError("Observer error")

        observable.attach(faulty_observer)
        observable.attach(lambda e: received.append(e))

        observable.notify("test")

        self.assertEqual(received, ["test"])

    def test_no_observers_notify_is_safe(self):
        observable = Observable()
        observable.notify("anything")

    def test_detach_all_observers(self):
        observable = Observable()
        events = []
        cb1 = lambda e: events.append(1)
        cb2 = lambda e: events.append(2)
        observable.attach(cb1)
        observable.attach(cb2)
        observable.detach(cb1)
        observable.detach(cb2)
        observable.notify("x")
        self.assertEqual(len(events), 0)


class TestObservableMemoryIntegration(unittest.TestCase):
    """Memory hereda de Observable: verificamos que emite eventos correctos."""

    def test_memory_notify_on_allocate(self):
        from core.memory import Memory
        from core.process import Process

        memory = Memory(capacity=1000, page_size=50)
        events = []
        memory.attach(lambda e: events.append(e))

        p = Process(1, 10, 100)
        memory.allocate(p)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "allocated")
        self.assertEqual(events[0]["process"], p)
        self.assertEqual(events[0]["used"], 2)

    def test_memory_notify_on_free(self):
        from core.memory import Memory
        from core.process import Process

        memory = Memory(capacity=1000, page_size=50)
        events = []
        memory.attach(lambda e: events.append(e))

        p = Process(1, 10, 100)
        memory.allocate(p)
        memory.free(p)

        self.assertEqual(len(events), 2)
        self.assertEqual(events[1]["type"], "freed")
        self.assertEqual(events[1]["process"], p)
        self.assertEqual(events[1]["used"], 0)

    def test_memory_no_observers(self):
        from core.memory import Memory
        from core.process import Process

        memory = Memory(capacity=1000, page_size=50)
        p = Process(1, 10, 100)
        memory.allocate(p)
        memory.free(p)

    def test_memory_multiple_observers(self):
        from core.memory import Memory
        from core.process import Process

        memory = Memory(capacity=1000, page_size=50)
        events_a = []
        events_b = []
        memory.attach(lambda e: events_a.append(e))
        memory.attach(lambda e: events_b.append(e))

        p = Process(1, 10, 100)
        memory.allocate(p)

        self.assertEqual(len(events_a), 1)
        self.assertEqual(len(events_b), 1)
        self.assertEqual(events_a[0]["type"], "allocated")
        self.assertEqual(events_b[0]["type"], "allocated")

    def test_memory_faulty_observer_does_not_break_allocate(self):
        from core.memory import Memory
        from core.process import Process

        memory = Memory(capacity=1000, page_size=50)

        def faulty_observer(e):
            raise RuntimeError("bad observer")

        memory.attach(faulty_observer)
        p = Process(1, 10, 100)

        memory.allocate(p)
        self.assertEqual(memory.used_frames, 2)


if __name__ == "__main__":
    unittest.main()
