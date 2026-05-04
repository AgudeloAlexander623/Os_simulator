# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

from controllers.simulation_controller import SimulationController
from utils import config
from utils.process_factory import sample_processes
import logging
import utils.logger  # Configura logging a archivo + consola


def main():
    controller = SimulationController(
        scheduler_type=config.SCHEDULER_TYPE,
        quantum=config.QUANTUM,
        memory_cap=config.MEMORY_CAPACITY,
        num_cores=config.NUM_CORES
    )

    for pid, burst, mem, pri in sample_processes():
        controller.add_process(pid, burst, mem, pri)

    stats = controller.start_simulation()

    logging.info(f"Procesos completados: {stats['completed']}")
    logging.info(f"Tiempo de espera promedio: {stats['avg_waiting_time']:.2f}")
    logging.info(f"Tiempo de turnaround promedio: {stats['avg_turnaround_time']:.2f}")
    logging.info(f"Uso de CPU: {stats['cpu_utilization']:.2f}")
    logging.info(f"Gantt Chart:\n{stats['gantt_chart']}")
    logging.info("Simulación finalizada")


if __name__ == "__main__":
    main()
