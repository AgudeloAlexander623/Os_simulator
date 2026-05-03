import threading
from threading import Lock


scheduler_lock: Lock = Lock()
memory_lock: Lock = Lock()
active_counter_lock: Lock = Lock()
