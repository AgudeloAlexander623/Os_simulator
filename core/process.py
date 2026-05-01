from dataclasses import dataclass, field
from core.states import ProcessState


@dataclass
class Process:
    pid: int
    burst_time: int
    memory: int

    remaining_time: int = field(init=False)
    state: ProcessState = field(default=ProcessState.READY)

    def __post_init__(self) -> None:
        self.remaining_time = self.burst_time

    def execute(self, quantum: int) -> int:
        self.state = ProcessState.RUNNING

        executed = min(self.remaining_time, quantum)
        self.remaining_time -= executed

        if self.remaining_time <= 0:
            self.state = ProcessState.TERMINATED
        else:
            self.state = ProcessState.READY

        return executed