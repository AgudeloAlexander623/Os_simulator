from core.process import Process
from core.scheduler import Scheduler
from core.memory import Memory
from concurrency.worker import CoreWorker
import logging
import utils.logger
import utils.config as config


def main():
    scheduler = Scheduler(quantum=config.QUANTUM)
    memory = Memory(capacity=config.MEMORY_CAPACITY)

    processes = [
        Process(1, 10, 100),
        Process(2, 6, 200),
        Process(3, 8, 300),
    ]

    # cargar procesos en memoria
    for p in processes:
        if memory.allocate(p):
            scheduler.add_process(p)

    # crear núcleos (threads)
    cores = [CoreWorker(scheduler, memory) for _ in range(config.NUM_CORES)]

    # iniciar ejecución
    for core in cores:
        core.start()

    for core in cores:
        core.join()

    logging.info("Simulación finalizada")


if __name__ == "__main__":
    main()