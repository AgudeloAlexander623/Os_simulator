from core.process import Process
from core.scheduler import Scheduler, FCFSScheduler, SJFScheduler, PriorityScheduler, RoundRobinScheduler
from core.memory import Memory
from concurrency.worker import CoreWorker
import logging
import utils.logger
import utils.config as config


def create_scheduler(sched_type: str, quantum: int) -> Scheduler:
    if sched_type == 'fcfs':
        return FCFSScheduler()
    elif sched_type == 'sjf':
        return SJFScheduler(quantum)
    elif sched_type == 'priority':
        return PriorityScheduler(quantum)
    elif sched_type == 'round_robin':
        return RoundRobinScheduler(quantum)
    else:
        raise ValueError(f"Tipo de scheduler desconocido: {sched_type}")


def main():
    scheduler = create_scheduler(config.SCHEDULER_TYPE, config.QUANTUM)
    memory = Memory(capacity=config.MEMORY_CAPACITY)

    processes = [
        Process(1, 10, 100, priority=1),
        Process(2, 6, 200, priority=2),
        Process(3, 8, 300, priority=0),
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