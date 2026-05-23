# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

import unittest
import sys
import os
import logging
import threading

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

    def remove_whitespace(self, text: str) -> str:
        return "".join(text.split())
    
    def test_render_ignores_whitespace(self):
        chart = GanttChart()
        chart.record(0, 0, 1)
        chart.record(1, 0, 1)

        result = chart.render(1)
        cleaned_result = self.remove_whitespace(result)
        self.assertIn("P1", cleaned_result)

        self.assertNotIn(" ", cleaned_result)
        self.assertNotIn("\n", cleaned_result)
        self.assertNotIn("\t", cleaned_result)

    def test_render_with_long_process_names(self):
        chart = GanttChart()
        chart.record(0, 0, 1)
        chart.record(1, 0, 2)

        result = chart.render(1)
        self.assertIn("P1", result)
        self.assertIn("P2", result)



        
class TestGanttChartEdgeCases(unittest.TestCase):

    def test_record_non_sequential_time(self):
        chart = GanttChart()
        chart.record(0, 0, 1)
        chart.record(2, 0, 2)  # Skip time 1

        result = chart.render(1)
        self.assertIn("P1", result)
        self.assertIn("P2", result)

    def test_record_overlapping_processes(self):
        chart = GanttChart()
        chart.record(0, 0, 1)
        chart.record(1, 0, 2)

        result = chart.render(1)
        self.assertIn("P1", result)
        self.assertIn("P2", result)

    def test_record_same_time_different_cores(self):
        chart = GanttChart()
        chart.record(0, 0, 1)  # P1 on core 0
        chart.record(0, 1, 2)  # P2 on core 1 at the same time

        result = chart.render(2)
        self.assertIn("P1", result)
        self.assertIn("P2", result) 

    def test_render_with_no_processes(self):
        chart = GanttChart()
        result = chart.render(1)
        self.assertEqual(result, "(vacío)")

    def test_render_with_only_idle_time(self):
        chart = GanttChart()
        chart.record(0, 0, 1)
        # Time 1-3 is idle
        chart.record(4, 0, 2)

        result = chart.render(1)
        self.assertIn("P1", result)
        self.assertIn("P2", result)
        self.assertIn("idle", result)
    
    def test_record_with_large_time_gap(self):
        chart = GanttChart()
        chart.record(0, 0, 1)
        chart.record(10, 0, 2)
        chart.record(20, 0, 1)
        result = chart.render(3)
        self.assertIn("P1", result)
        self.assertIn("P2", result)
        self.assertIn("idle", result)

class TestGanttChartInvalidInputs(unittest.TestCase):

    def test_record_negative_time(self):
        chart = GanttChart()
        with self.assertRaises(ValueError):
            chart.record(-1, 0, 1)
    
    def test_record_negative_core(self):
        chart = GanttChart()
        with self.assertRaises(ValueError):
            chart.record(0, -1, 1)

    def test_record_non_integer_time(self):
        chart = GanttChart()
        with self.assertRaises(ValueError):
            chart.record("not_an_integer", 0, 1)

if __name__ == '__main__':
    unittest.main()
