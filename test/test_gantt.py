# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.gantt import GanttChart


class TestGanttChart(unittest.TestCase):

    def test_record_and_render_single_core(self):
        chart = GanttChart()
        chart.record(0, 0, 1)
        chart.record(1, 0, 1)
        chart.record(2, 0, 2)

        result = chart.render(1)
        self.assertIn("Core 0:", result)
        self.assertIn("P1", result)
        self.assertIn("P2", result)

    def test_render_multiple_cores(self):
        chart = GanttChart()
        chart.record(0, 0, 1)
        chart.record(0, 1, 2)
        chart.record(1, 0, 1)
        chart.record(1, 1, 2)

        result = chart.render(2)
        lines = result.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertIn("Core 0:", lines[0])
        self.assertIn("Core 1:", lines[1])

    def test_render_empty(self):
        chart = GanttChart()
        result = chart.render(1)
        self.assertEqual(result, "(vacío)")

    def test_render_with_idle_core(self):
        chart = GanttChart()
        chart.record(0, 0, 1)
        chart.record(1, 0, 1)
        # Core 1 never gets any process

        result = chart.render(2)
        self.assertIn("Core 0:", result)
        self.assertIn("Core 1:", result)

    def test_record_expands_timeline(self):
        chart = GanttChart()
        chart.record(5, 0, 1)  # Skip ahead

        self.assertGreaterEqual(len(chart.timeline), 6)
        self.assertEqual(chart.timeline[5][0], 1)


if __name__ == '__main__':
    unittest.main()
