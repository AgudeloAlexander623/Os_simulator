# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.observer import Observable


class TestObserver(unittest.TestCase):

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
        observable.detach(lambda e: None)  # Should not raise

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


if __name__ == '__main__':
    unittest.main()
