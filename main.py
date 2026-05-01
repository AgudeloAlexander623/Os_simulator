from controllers.simulation_controller import SimulationController
import utils.config as config
import logging
import utils.logger


def main():
    controller = SimulationController(
        scheduler_type=config.SCHEDULER_TYPE,
        quantum=config.QUANTUM,
        memory_cap=config.MEMORY_CAPACITY,
        num_cores=config.NUM_CORES
    )

    # Agregar procesos
    processes = [
        (1, 10, 100, 1),
        (2, 6, 200, 2),
        (3, 8, 300, 0),
    ]

    for pid, burst, mem, pri in processes:
        controller.add_process(pid, burst, mem, pri)

    # Iniciar simulación
    stats = controller.start_simulation()

    logging.info(f"Procesos completados: {stats['completed']}")
    logging.info(f"Tiempo de espera promedio: {stats['avg_waiting_time']:.2f}")
    logging.info(f"Tiempo de turnaround promedio: {stats['avg_turnaround_time']:.2f}")
    logging.info(f"Uso de CPU: {stats['cpu_utilization']:.2f}")
    logging.info("Simulación finalizada")


if __name__ == "__main__":
    main()