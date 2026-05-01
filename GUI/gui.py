import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import logging
import os
import sys

# Ajustar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.process import Process
from core.scheduler import Scheduler, FCFSScheduler, SJFScheduler, PriorityScheduler, RoundRobinScheduler
from core.memory import Memory
from concurrency.worker import CoreWorker
from utils import config


def create_scheduler(sched_type: str, quantum: int) -> Scheduler:
    if sched_type == 'fcfs':
        return FCFSScheduler()
    elif sched_type == 'sjf':
        return SJFScheduler(quantum)
    elif sched_type == 'priority':
        return PriorityScheduler(quantum)
    elif sched_type == 'round_robin':
        return RoundRobinScheduler(quantum)
    else:
        raise ValueError(f"Tipo de scheduler desconocido: {sched_type}")


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

        self.scheduler = create_scheduler(config.SCHEDULER_TYPE, config.QUANTUM)
        self.memory = Memory(capacity=config.MEMORY_CAPACITY)
        self.processes = []

    def create_widgets(self):
        # Frame para controles
        control_frame = tk.Frame(self.root, bg='#1a1a1a')
        control_frame.pack(fill="x", padx=10, pady=5)

        # Selector de scheduler
        tk.Label(control_frame, text="Scheduler:", bg='#1a1a1a', fg='#00ff00', font=('Courier', 12)).pack(anchor='w')
        self.sched_var = tk.StringVar(value=config.SCHEDULER_TYPE)
        sched_options = ['round_robin', 'fcfs', 'sjf', 'priority']
        self.sched_menu = tk.OptionMenu(control_frame, self.sched_var, *sched_options)
        self.sched_menu.config(bg='#333333', fg='#00ff00', font=('Courier', 10))
        self.sched_menu.pack(pady=5)

        # Controles para quantum y memoria
        tk.Label(control_frame, text="Quantum:", bg='#1a1a1a', fg='#00ff00', font=('Courier', 10)).pack(anchor='w')
        self.quantum_var = tk.IntVar(value=config.QUANTUM)
        self.quantum_entry = tk.Entry(control_frame, textvariable=self.quantum_var, bg='#333333', fg='#00ff00', font=('Courier', 10))
        self.quantum_entry.pack(pady=2)

        tk.Label(control_frame, text="Memoria:", bg='#1a1a1a', fg='#00ff00', font=('Courier', 10)).pack(anchor='w')
        self.memory_var = tk.IntVar(value=config.MEMORY_CAPACITY)
        self.memory_entry = tk.Entry(control_frame, textvariable=self.memory_var, bg='#333333', fg='#00ff00', font=('Courier', 10))
        self.memory_entry.pack(pady=2)

        # Etiqueta para procesos
        tk.Label(control_frame, text="Procesos:", bg='#1a1a1a', fg='#00ff00', font=('Courier', 12)).pack(anchor='w')

        # Tabla de procesos
        columns = ("PID", "Burst Time", "Memory", "Priority")
        self.tree = ttk.Treeview(control_frame, columns=columns, show="headings", height=5)
        self.tree.pack(fill="x", pady=5)

        # Estilo para treeview hacker
        style = ttk.Style()
        style.configure("Treeview", background="#333333", foreground="#00ff00", fieldbackground="#333333", font=('Courier', 10))
        style.configure("Treeview.Heading", background="#444444", foreground="#00ff00", font=('Courier', 10, 'bold'))

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        # Botones para editar procesos
        button_frame = tk.Frame(control_frame, bg='#1a1a1a')
        button_frame.pack(pady=5)
        self.add_button = tk.Button(button_frame, text="Agregar Proceso", command=self.add_process, bg='#333333', fg='#00ff00', font=('Courier', 10))
        self.add_button.pack(side='left', padx=5)
        self.remove_button = tk.Button(button_frame, text="Remover Seleccionado", command=self.remove_process, bg='#333333', fg='#00ff00', font=('Courier', 10))
        self.remove_button.pack(side='left', padx=5)

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

        # Área de estadísticas
        self.stats_label = tk.Label(self.root, text="Estadísticas: ", bg='#1a1a1a', fg='#00ff00', font=('Courier', 12))
        self.stats_label.pack(pady=5)

        # Agregar procesos de ejemplo
        self.add_sample_processes()

    def add_sample_processes(self):
        sample_processes = [
            (1, 10, 100, 1),
            (2, 6, 200, 2),
            (3, 8, 300, 0),
        ]
        for pid, burst, mem, pri in sample_processes:
            self.tree.insert("", "end", values=(pid, burst, mem, pri))

    def add_process(self):
        # Ventana emergente para agregar proceso
        add_win = tk.Toplevel(self.root)
        add_win.title("Agregar Proceso")
        add_win.configure(bg='#1a1a1a')

        tk.Label(add_win, text="PID:", bg='#1a1a1a', fg='#00ff00').grid(row=0, column=0)
        pid_entry = tk.Entry(add_win, bg='#333333', fg='#00ff00')
        pid_entry.grid(row=0, column=1)

        tk.Label(add_win, text="Burst Time:", bg='#1a1a1a', fg='#00ff00').grid(row=1, column=0)
        burst_entry = tk.Entry(add_win, bg='#333333', fg='#00ff00')
        burst_entry.grid(row=1, column=1)

        tk.Label(add_win, text="Memory:", bg='#1a1a1a', fg='#00ff00').grid(row=2, column=0)
        mem_entry = tk.Entry(add_win, bg='#333333', fg='#00ff00')
        mem_entry.grid(row=2, column=1)

        tk.Label(add_win, text="Priority:", bg='#1a1a1a', fg='#00ff00').grid(row=3, column=0)
        pri_entry = tk.Entry(add_win, bg='#333333', fg='#00ff00')
        pri_entry.grid(row=3, column=1)

        def save_process():
            try:
                pid = int(pid_entry.get())
                burst = int(burst_entry.get())
                mem = int(mem_entry.get())
                pri = int(pri_entry.get())
                self.tree.insert("", "end", values=(pid, burst, mem, pri))
                add_win.destroy()
            except ValueError:
                messagebox.showerror("Error", "Valores inválidos")

        tk.Button(add_win, text="Guardar", command=save_process, bg='#333333', fg='#00ff00').grid(row=4, columnspan=2)

    def remove_process(self):
        selected = self.tree.selection()
        if selected:
            self.tree.delete(selected)

    def start_simulation(self):
        self.start_button.config(state='disabled')
        self.log_text.delete(1.0, tk.END)  # Limpiar logs
        self.stats_label.config(text="Estadísticas: Simulando...")

        # Crear scheduler basado en selección
        sched_type = self.sched_var.get()
        quantum = self.quantum_var.get()
        memory_cap = self.memory_var.get()
        self.scheduler = create_scheduler(sched_type, quantum)
        self.memory = Memory(capacity=memory_cap)

        # Crear procesos desde la tabla
        self.processes = []
        for item in self.tree.get_children():
            values = self.tree.item(item, 'values')
            pid, burst, mem, pri = int(values[0]), int(values[1]), int(values[2]), int(values[3])
            self.processes.append(Process(pid, burst, mem, pri))

        # Cargar en memoria y scheduler
        for p in self.processes:
            if self.memory.allocate(p):
                self.scheduler.add_process(p)

        # Crear workers y ejecutar en thread
        cores = [CoreWorker(self.scheduler, self.memory) for _ in range(config.NUM_CORES)]
        sim_thread = threading.Thread(target=self.run_simulation, args=(cores,))
        sim_thread.start()

    def run_simulation(self, cores):
        import time
        start_time = time.time()
        for core in cores:
            core.start()
        for core in cores:
            core.join()
        end_time = time.time()
        total_time = end_time - start_time
        completed = sum(1 for p in self.processes if p.state.name == 'TERMINATED')
        throughput = completed / total_time if total_time > 0 else 0
        self.stats_label.config(text=f"Estadísticas: Tiempo total: {total_time:.2f}s, Procesos completados: {completed}, Throughput: {throughput:.2f} proc/s")
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