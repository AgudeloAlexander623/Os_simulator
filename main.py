# Copyright (c) 2026 Jessid Alexander Agudelo — Universidad del Valle
# Educational use only. See LICENSE for details.

"""Punto de entrada principal del simulador OS.

Lanza la interfaz gráfica (GUI) para configurar y ejecutar simulaciones
de forma interactiva.
"""

import tkinter as tk
from GUI.gui import OSSimulatorGUI


def main():
    """Inicia la aplicación del simulador OS con interfaz gráfica."""
    root = tk.Tk()
    app = OSSimulatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
