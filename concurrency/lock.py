# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

import threading
from threading import Lock


scheduler_lock: Lock = Lock()
memory_lock: Lock = Lock()
