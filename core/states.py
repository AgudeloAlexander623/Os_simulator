from enum import Enum

class ProcessState(Enum):
    READY = "READY"
    RUNNING = "RUNNING"
    TERMINATED = "TERMINATED"