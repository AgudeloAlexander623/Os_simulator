import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import logging
import os
import sys

# Ajustar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.process import Process
from core.scheduler import Scheduler
from core.memory import Memory
from concurrency.worker import CoreWorker
from utils import config


class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.insert(tk.END, msg + '\n')
        self.text_widget.see(tk.END)


class OSSimulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OS Simulator - Hacker Mode")
        self.root.geometry("800x600")
        self.root.configure(bg='#1a1a1a')  # Fondo oscuro hacker

        # Configurar logging para la GUI
        self.log_text = scrolledtext.ScrolledText(self.root, height=10, bg='#000000', fg='#00ff00', font=('Courier', 10))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

        handler = TextHandler(self.log_text)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)

        self.create_widgets()

        self.scheduler = Scheduler(quantum=config.QUANTUM)
        self.memory = Memory(capacity=config.MEMORY_CAPACITY)
        self.processes = []

    def create_widgets(self):
        # Frame para controles
        control_frame = tk.Frame(self.root, bg='#1a1a1a')
        control_frame.pack(fill="x", padx=10, pady=5)

        # Etiqueta para procesos
        tk.Label(control_frame, text="Procesos:", bg='#1a1a1a', fg='#00ff00', font=('Courier', 12)).pack(anchor='w')

        # Tabla de procesos
        columns = ("PID", "Burst Time", "Memory")
        self.tree = ttk.Treeview(control_frame, columns=columns, show="headings", height=5)
        self.tree.pack(fill="x", pady=5)

        # Estilo para treeview hacker
        style = ttk.Style()
        style.configure("Treeview", background="#333333", foreground="#00ff00", fieldbackground="#333333", font=('Courier', 10))
        style.configure("Treeview.Heading", background="#444444", foreground="#00ff00", font=('Courier', 10, 'bold'))

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        # Botón iniciar con estilo hacker
        self.start_button = tk.Button(
            control_frame,
            text="Iniciar Simulación",
            command=self.start_simulation,
            bg='#333333',
            fg='#00ff00',
            font=('Courier', 12, 'bold'),
            activebackground='#555555',
            activeforeground='#00ff00'
        )
        self.start_button.pack(pady=10)

        # Agregar procesos de ejemplo
        self.add_sample_processes()

    def add_sample_processes(self):
        sample_processes = [
            (1, 10, 100),
            (2, 6, 200),
            (3, 8, 300),
        ]
        for pid, burst, mem in sample_processes:
            self.tree.insert("", "end", values=(pid, burst, mem))

    def start_simulation(self):
        self.start_button.config(state='disabled')
        self.log_text.delete(1.0, tk.END)  # Limpiar logs

        # Crear procesos desde la tabla
        self.processes = []
        for item in self.tree.get_children():
            values = self.tree.item(item, 'values')
            pid, burst, mem = int(values[0]), int(values[1]), int(values[2])
            self.processes.append(Process(pid, burst, mem))

        # Cargar en memoria y scheduler
        for p in self.processes:
            if self.memory.allocate(p):
                self.scheduler.add_process(p)

        # Crear workers y ejecutar en thread
        cores = [CoreWorker(self.scheduler, self.memory) for _ in range(2)]
        sim_thread = threading.Thread(target=self.run_simulation, args=(cores,))
        sim_thread.start()

    def run_simulation(self, cores):
        for core in cores:
            core.start()
        for core in cores:
            core.join()
        logging.info("Simulación finalizada")
        self.start_button.config(state='normal')


if __name__ == "__main__":
    root = tk.Tk()
    app = OSSimulatorGUI(root)
    root.mainloop()
    def create_processes(self):
        self.processes = [
            Process(1, 10, 100),
            Process(2, 6, 200),
            Process(3, 8, 300),
        ]

        for p in self.processes:
           if self.memory.allocate(p):
                self.scheduler.add_process(p)
                self.tree.insert("", "end", iid=p.pid , values=(
                    p.pid,
                    p.state.name,
                    p.remaining_time,
                    p.memory
                ))

    # actualizar tabla
    def Update_table(self, process):
        self.tree.item(process.pid, values=(
            process.pid,
            process.state.name,
            process.remaining_time,
            process.memory
        ))

    def run_simulation(self):
        if not self.scheduler.has_processes():
            self.log.insert("end", "simulacion terminada\n")
            return

        process = self.scheduler.get_process()

        if process:
            executed = process.execute(self.scheduler.quantum)

            self.log.insert(
                "end",
                f"PID {process.pid} ejecuto {executed}| restante={process.remaining_time}\n"
            )

            self.update_table(process)

            if process.remaining_time > 0:
                self.scheduler.add_process(process)
        self.root.after(500,self.run_simulation)


        def start_simulation(self):
            self.tree.delete(*self.tree.get_children())
            self.log.delete("1.0", "end")

            self.scheduler = Scheduler(quantum=2)
            self.memory = Memory(capacity=500)

            self.create_processes()
            self.run_simulation()


# ejecutamos la GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = OSSimulatorGUI(root)
    root.mainloop()