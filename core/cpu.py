import time

# DEPRECATED: Esta clase fue reemplazada por CoreWorker en concurrency/worker.py.
# CoreWorker soporta multi-core con threading y proper lock management.
# Esta clase se mantiene solo como referencia histórica.


class CPU:
    def __init__(self, scheduler):
        self.scheduler = scheduler

    def run(self):
        while self.scheduler.has_processes():
            process = self.scheduler.get_process()

            if not process:
                continue

            executed = process.execute(self.scheduler.quantum)

            print(
                f"[CPU] PID={process.pid} ejecutó {executed} | restante={process.remaining_time}"
            )

            time.sleep(0.5)

            if process.state.name != "TERMINATED":
                self.scheduler.add_process(process)