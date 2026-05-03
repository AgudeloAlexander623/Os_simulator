import threading


class Semaphore:
    """Semáforo para sincronización de procesos."""

    def __init__(self, value: int = 1):
        """Inicializa el semáforo.

        Args:
            value: Valor inicial del semáforo.
        """
        self._value = value
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)

    def acquire(self) -> None:
        """Adquiere el semáforo, bloqueando si es necesario."""
        with self._condition:
            while self._value <= 0:
                self._condition.wait()
            self._value -= 1

    def release(self) -> None:
        """Libera el semáforo, despertando hilos en espera."""
        with self._condition:
            self._value += 1
            self._condition.notify()

    @property
    def value(self) -> int:
        """Retorna el valor actual del semáforo."""
        with self._lock:
            return self._value


class Event:
    """Evento para sincronización de procesos (estilo threading.Event)."""

    def __init__(self):
        self._flag = False
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)

    def set(self) -> None:
        """Setea el evento, despertando todos los hilos en espera."""
        with self._condition:
            self._flag = True
            self._condition.notify_all()

    def clear(self) -> None:
        """Limpia el evento."""
        with self._lock:
            self._flag = False

    def wait(self, timeout: float = -1) -> bool:
        """Espera a que el evento sea seteado.

        Args:
            timeout: Tiempo máximo de espera en segundos (-1 = infinito).

        Returns:
            bool: True si el evento fue seteado, False si hubo timeout.
        """
        with self._condition:
            if timeout < 0:
                while not self._flag:
                    self._condition.wait()
                return True
            return self._condition.wait_for(lambda: self._flag, timeout=timeout)

    def is_set(self) -> bool:
        """Retorna si el evento está seteado."""
        with self._lock:
            return self._flag
