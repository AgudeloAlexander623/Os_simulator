# OS Simulator

Un simulador básico de sistema operativo en Python, con procesos, scheduler round-robin, gestión de memoria y concurrencia.

## Características
- Simulación de procesos con burst time y memoria.
- Scheduler con quantum configurable.
- Gestión de memoria simple.
- Concurrencia con threads.
- Interfaz gráfica básica con estilo hacker.

## Instalación
1. Clona el repo.
2. Crea un venv: `python -m venv venv`
3. Activa: `source venv/bin/activate`
4. Instala dependencias: `pip install -r requirements.txt`
5. Ejecuta: `python main.py` o `python GUI/gui.py`

## Uso
- main.py: Ejecuta simulación en consola.
- GUI/gui.py: Interfaz gráfica.

## Mejoras futuras
- Más algoritmos de scheduling.
- Paginación de memoria.
- Tests unitarios.
- Documentación completa.