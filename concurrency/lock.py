# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

"""Locks globales para sincronización entre workers.

Provee dos locks de threading que se usan en toda la simulación para
garantizar acceso exclusivo al scheduler y a la memoria cuando varios
cores ejecutan concurrentemente.
"""

from threading import Lock


scheduler_lock: Lock = Lock()
memory_lock: Lock = Lock()
