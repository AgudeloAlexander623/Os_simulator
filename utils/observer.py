from typing import Callable, Any


class Observable:
    """Clase base para objetos observables (Observer pattern)."""

    def __init__(self):
        self._observers = []

    def attach(self, observer: Callable[[Any], None]) -> None:
        """Adjunta un observador.

        Args:
            observer (Callable): Función a llamar en notificaciones.
        """
        self._observers.append(observer)

    def detach(self, observer: Callable[[Any], None]) -> None:
        """Desadjunta un observador.

        Args:
            observer (Callable): Observador a remover.
        """
        self._observers.remove(observer)

    def notify(self, event: Any) -> None:
        """Notifica a todos los observadores.

        Args:
            event (Any): Datos del evento.
        """
        for observer in self._observers:
            observer(event)