# OS Simulator

Un simulador básico de sistema operativo en Python, con procesos, scheduler múltiple, gestión de memoria y concurrencia.

## Características
- Simulación de procesos con burst time, memoria y prioridad.
- Schedulers: Round-Robin, FCFS, SJF, Priority.
- Gestión de memoria simple con liberación automática.
- Concurrencia con threads.
- Interfaz gráfica básica con estilo hacker: selector de scheduler, configuración de parámetros, edición de procesos, logs en tiempo real y estadísticas finales.
- Configuración externa y tests unitarios.

## Instalación
1. Clona el repo.
2. Crea un venv: `python -m venv venv`
3. Activa: `source venv/bin/activate`
4. Instala dependencias: `pip install -r requirements.txt`
5. Ejecuta: `python main.py` o `python GUI/gui.py`

## Uso
- main.py: Ejecuta simulación en consola (configura scheduler en utils/config.py).
- GUI/gui.py: Interfaz gráfica para seleccionar scheduler, configurar parámetros, editar procesos y ver logs/estadísticas.

## Configuración
Edita `utils/config.py` para cambiar quantum, scheduler, memoria, etc.

## Tests
Ejecuta `python -m unittest discover test` para correr tests.

## Mejoras futuras
- Paginación de memoria.
- Operaciones I/O con bloqueo de procesos.
- Sistema de archivos básico.
- Más métricas y visualizaciones en GUI.