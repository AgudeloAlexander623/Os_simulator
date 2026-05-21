# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

"""Tests de integración: componentes working together.

Cubre scheduler + worker, controller end-to-end, multi-core,
observer, context switch overhead y validaciones.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controllers.simulation_controller import SimulationController
from core.process import Process
from core.memory import Memory, MemoryInsufficientError
from core.scheduler import (
    FCFSScheduler,
    SJFScheduler,
    PriorityScheduler,
    RoundRobinScheduler,
)
from concurrency.worker import CoreWorker
from utils.gantt import GanttChart


class TestIntegrationSchedulerWorker(unittest.TestCase):
    """Scheduler + Worker + procesos en conjunto."""

    def test_fcfs_completes_all_processes(self):
        scheduler = FCFSScheduler()
        memory = Memory(1000)
        processes = [
            Process(1, 4, 100),
            Process(2, 6, 200),
            Process(3, 3, 150),
        ]
        for p in processes:
            memory.allocate(p)
            scheduler.add_process(p)

        worker = CoreWorker(scheduler, memory)
        worker.start()
        worker.join()

        self.assertEqual(worker.current_time, 13)
        self.assertTrue(all(p.completion_time != -1 for p in processes))

    def test_sjf_orders_by_shortest(self):
        scheduler = SJFScheduler(quantum=2)
        memory = Memory(1000)
        processes = [
            Process(1, 10, 100),
            Process(2, 2, 100),
            Process(3, 5, 100),
        ]
        for p in processes:
            memory.allocate(p)
            scheduler.add_process(p)

        worker = CoreWorker(scheduler, memory)
        worker.start()
        worker.join()

        self.assertEqual(worker.current_time, 17)
        self.assertEqual(processes[1].completion_time, 2)
        self.assertEqual(processes[2].completion_time, 7)
        self.assertEqual(processes[0].completion_time, 17)

    def test_round_robin_quantum_scheduling(self):
        scheduler = RoundRobinScheduler(quantum=2)
        memory = Memory(1000)
        processes = [Process(1, 4, 100), Process(2, 4, 100)]
        for p in processes:
            memory.allocate(p)
            scheduler.add_process(p)

        worker = CoreWorker(scheduler, memory)
        worker.start()
        worker.join()

        self.assertEqual(worker.current_time, 8)
        self.assertTrue(all(p.completion_time != -1 for p in processes))

    def test_priority_scheduler_orders_by_priority(self):
        scheduler = PriorityScheduler(quantum=2)
        memory = Memory(1000)
        p_high = Process(1, 3, 100, priority=1)
        p_low = Process(2, 3, 100, priority=5)
        memory.allocate(p_high)
        memory.allocate(p_low)
        scheduler.add_process(p_low)
        scheduler.add_process(p_high)

        worker = CoreWorker(scheduler, memory)
        worker.start()
        worker.join()

        self.assertEqual(worker.current_time, 6)
        self.assertEqual(p_high.completion_time, 3)
        self.assertEqual(p_low.completion_time, 6)


class TestIntegrationController(unittest.TestCase):
    """SimulationController end-to-end."""

    def test_controller_completes_processes(self):
        controller = SimulationController(
            scheduler_type="round_robin", quantum=2, memory_cap=1000, num_cores=1,
        )
        controller.add_process(1, 4, 100, pri=1)
        controller.add_process(2, 6, 200, pri=2)
        stats = controller.start_simulation()

        self.assertEqual(stats["completed"], 2)
        self.assertEqual(stats["total_time"], 10)
        self.assertGreater(stats["throughput"], 0)

    def test_controller_multi_core_simulation(self):
        controller = SimulationController(
            scheduler_type="round_robin", quantum=2, memory_cap=1000, num_cores=2,
        )
        controller.add_process(1, 4, 100, pri=1)
        controller.add_process(2, 4, 100, pri=2)
        stats = controller.start_simulation()

        self.assertEqual(stats["completed"], 2)
        self.assertGreaterEqual(stats["total_time"], 4)
        self.assertLessEqual(stats["total_time"], 8)

    def test_controller_memory_insufficient(self):
        controller = SimulationController(
            scheduler_type="fcfs", quantum=0, memory_cap=100, num_cores=1,
        )
        controller.add_process(1, 4, 100, pri=1)
        controller.add_process(2, 4, 100, pri=1)
        stats = controller.start_simulation()
        self.assertEqual(stats["completed"], 1)

    def test_controller_empty_simulation(self):
        controller = SimulationController(
            scheduler_type="fcfs", quantum=0, memory_cap=500, num_cores=1,
        )
        stats = controller.start_simulation()

        self.assertEqual(stats["completed"], 0)
        self.assertEqual(stats["total_time"], 0)
        self.assertEqual(stats["throughput"], 0)
        self.assertEqual(stats["avg_waiting_time"], 0)

    def test_controller_single_process(self):
        controller = SimulationController(
            scheduler_type="sjf", quantum=2, memory_cap=500, num_cores=1,
        )
        controller.add_process(1, 5, 100, pri=0)
        stats = controller.start_simulation()

        self.assertEqual(stats["completed"], 1)
        self.assertEqual(stats["total_time"], 5)
        self.assertEqual(stats["avg_turnaround_time"], 5)
        self.assertEqual(stats["avg_waiting_time"], 0)

    def test_cpu_utilization_capped_at_100(self):
        controller = SimulationController(
            scheduler_type="round_robin", quantum=2, memory_cap=1000, num_cores=2,
        )
        controller.add_process(1, 4, 100, pri=1)
        controller.add_process(2, 4, 100, pri=2)
        stats = controller.start_simulation()

        self.assertLessEqual(stats["cpu_utilization"], 1.0)
        self.assertGreater(stats["cpu_utilization"], 0)

    def test_controller_invalid_scheduler(self):
        with self.assertRaises(ValueError):
            SimulationController(
                scheduler_type="unknown", quantum=2, memory_cap=500, num_cores=1,
            )

    def test_controller_stats_has_gantt_chart(self):
        controller = SimulationController(
            scheduler_type="fcfs", quantum=0, memory_cap=500, num_cores=1,
        )
        controller.add_process(1, 3, 100, pri=0)
        controller.add_process(2, 5, 100, pri=0)
        stats = controller.start_simulation()

        self.assertIn("gantt_chart", stats)
        self.assertIsInstance(stats["gantt_chart"], str)
        self.assertIn("Core 0:", stats["gantt_chart"])

    def test_controller_all_schedulers(self):
        for sched in ["fcfs", "sjf", "priority", "round_robin"]:
            controller = SimulationController(
                scheduler_type=sched, quantum=2, memory_cap=500, num_cores=1,
            )
            controller.add_process(1, 4, 100, pri=1)
            controller.add_process(2, 6, 100, pri=2)
            stats = controller.start_simulation()
            self.assertEqual(stats["completed"], 2, f"Failed for {sched}")
            self.assertGreater(stats["total_time"], 0)
            self.assertIn("gantt_chart", stats)

    def test_controller_invalid_params(self):
        with self.assertRaises(ValueError):
            SimulationController(
                scheduler_type="fcfs", quantum=-1, memory_cap=500, num_cores=1,
            )
        with self.assertRaises(ValueError):
            SimulationController(
                scheduler_type="fcfs", quantum=0, memory_cap=0, num_cores=1,
            )
        with self.assertRaises(ValueError):
            SimulationController(
                scheduler_type="fcfs", quantum=0, memory_cap=500, num_cores=0,
            )
        with self.assertRaises(ValueError):
            SimulationController(
                scheduler_type="fcfs", quantum=0, memory_cap=500, num_cores=1,
                context_switch_overhead=-1,
            )

    def test_controller_process_metrics_in_stats(self):
        controller = SimulationController(
            scheduler_type="fcfs", quantum=0, memory_cap=500, num_cores=1,
        )
        controller.add_process(1, 5, 100, pri=0)
        controller.add_process(2, 3, 100, pri=0)
        stats = controller.start_simulation()

        metrics = stats["process_metrics"]
        self.assertEqual(len(metrics), 2)
        for m in metrics:
            self.assertIn("pid", m)
            self.assertIn("burst_time", m)
            self.assertIn("waiting_time", m)
            self.assertIn("turnaround_time", m)
            self.assertIn("response_time", m)


class TestIntegrationMemoryObserver(unittest.TestCase):
    """Memory con Observer pattern."""

    def test_memory_notifies_on_allocate_and_free(self):
        memory = Memory(500, 50)
        events = []
        memory.attach(lambda e: events.append(e))

        process = Process(1, 4, 100)
        memory.allocate(process)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "allocated")
        self.assertEqual(events[0]["used"], 2)

        memory.free(process)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[1]["type"], "freed")
        self.assertEqual(events[1]["used"], 0)


class TestIntegrationWorker(unittest.TestCase):
    """CoreWorker en detalle."""

    def test_worker_context_switch_overhead_fcfs(self):
        scheduler = FCFSScheduler()
        memory = Memory(1000)
        processes = [Process(1, 4, 100), Process(2, 4, 100)]
        for p in processes:
            memory.allocate(p)
            scheduler.add_process(p)

        overhead = 2
        worker = CoreWorker(scheduler, memory, context_switch_overhead=overhead)
        worker.start()
        worker.join()

        self.assertEqual(worker.current_time, 4 + overhead + 4)

    def test_worker_context_switch_overhead_round_robin(self):
        scheduler = RoundRobinScheduler(quantum=2)
        memory = Memory(1000)
        processes = [Process(1, 6, 100), Process(2, 6, 100)]
        for p in processes:
            memory.allocate(p)
            scheduler.add_process(p)

        overhead = 1
        worker = CoreWorker(scheduler, memory, context_switch_overhead=overhead)
        worker.start()
        worker.join()

        # RR con quantum=2: P1(2)+sw+P2(2)+sw+P1(2)+sw+P2(2)+sw+P1(2)+sw+P2(2)
        # 12 unidades de ejecucion + 5 context switches = 17
        self.assertEqual(worker.current_time, 17)
        self.assertGreater(worker.context_switches, 0)

    def test_worker_gantt_chart_records(self):
        scheduler = FCFSScheduler()
        memory = Memory(1000)
        processes = [Process(1, 3, 100), Process(2, 2, 100)]
        for p in processes:
            memory.allocate(p)
            scheduler.add_process(p)

        gantt = GanttChart()
        worker = CoreWorker(scheduler, memory, core_id=0, gantt_chart=gantt)
        worker.start()
        worker.join()

        self.assertGreater(len(gantt.timeline), 0)
        self.assertIn(0, gantt.timeline[0])

    def test_worker_total_time(self):
        scheduler = FCFSScheduler()
        memory = Memory(1000)
        p = Process(1, 5, 100)
        memory.allocate(p)
        scheduler.add_process(p)

        worker = CoreWorker(scheduler, memory)
        worker.start()
        worker.join()

        self.assertEqual(worker.get_total_time(), 5)
        self.assertEqual(worker.get_context_switches(), 0)


if __name__ == "__main__":
    unittest.main()
