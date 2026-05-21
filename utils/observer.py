# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

"""Patrón Observer: permite suscribirse a eventos de un objeto.

Un observador defectuoso no interrumpe la notificación al resto.
"""

import logging
from typing import Callable, Any


class Observable:
    """Clase base para objetos que emiten eventos a suscriptores."""

    def __init__(self) -> None:
        self._observers: list[Callable[[Any], None]] = []

    def attach(self, observer: Callable[[Any], None]) -> None:
        """Suscribe un observador."""
        self._observers.append(observer)

    def detach(self, observer: Callable[[Any], None]) -> None:
        """Desuscribe un observador (silencioso si no existe)."""
        try:
            self._observers.remove(observer)
        except ValueError:
            pass

    def notify(self, event: Any) -> None:
        """Notifica a todos los observadores.

        Si un observador lanza una excepción, se loguea pero no
        interrumpe la notificación al resto.
        """
        for observer in self._observers:
            try:
                observer(event)
            except Exception:
                logging.exception("Error en observador durante notify")
