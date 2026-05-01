from controllers.simulation_controller import SimulationController
import utils.config as config
import logging
import utils.logger


def main():
    controller = SimulationController()

    # Agregar procesos
    processes = [
        (1, 10, 100, 1),
        (2, 6, 200, 2),
        (3, 8, 300, 0),
    ]

    for pid, burst, mem, pri in processes:
        controller.add_process(pid, burst, mem, pri)

    # Iniciar simulación
    controller.start_simulation()

    logging.info("Simulación finalizada")


if __name__ == "__main__":
    main()