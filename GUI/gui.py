"""Interfaz gráfica del simulador OS (tkinter).

Organizada en paneles:
- Configuración: tipo de scheduler, quantum, memoria, cores, overhead
- Tabla de procesos: agregar, quitar, resetear a los de ejemplo
- Mapa de memoria: muestra el estado de los frames después de simular
- Log: salida en tiempo real del logging
- Estadísticas y Gantt: resultados numéricos más diagrama de Gantt
- Barra de estado: indicador de proceso y contador

La simulación corre en un hilo aparte para no congelar la interfaz.
"""

import os
import sys
from typing import Optional, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils import config
from utils.process_factory import sample_processes
from controllers.simulation_controller import SimulationController
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import logging


LIGHT_THEME = {
    "bg_primary": "#f5f5f5",
    "bg_secondary": "#ffffff",
    "bg_card": "#ffffff",
    "bg_input": "#f0f0f0",
    "bg_button_primary": "#2563eb",
    "bg_button_secondary": "#6b7280",
    "bg_button_danger": "#ef4444",
    "bg_success": "#10b981",
    "bg_statusbar": "#1e293b",
    "text_primary": "#1e293b",
    "text_secondary": "#64748b",
    "text_on_primary": "#ffffff",
    "text_on_dark": "#e2e8f0",
    "border": "#e2e8f0",
    "accent": "#2563eb",
    "log_bg": "#0f172a",
    "log_fg": "#22d3ee",
    "stats_bg": "#f8fafc",
    "stats_fg": "#1e293b",
    "toggle_bg": "#1e293b",
    "toggle_fg": "#e2e8f0",
    "toggle_active": "#334155",
}

DARK_THEME = {
    "bg_primary": "#0f172a",
    "bg_secondary": "#1e293b",
    "bg_card": "#1e293b",
    "bg_input": "#334155",
    "bg_button_primary": "#3b82f6",
    "bg_button_secondary": "#475569",
    "bg_button_danger": "#ef4444",
    "bg_success": "#22c55e",
    "bg_statusbar": "#020617",
    "text_primary": "#e2e8f0",
    "text_secondary": "#94a3b8",
    "text_on_primary": "#ffffff",
    "text_on_dark": "#cbd5e1",
    "border": "#334155",
    "accent": "#3b82f6",
    "log_bg": "#020617",
    "log_fg": "#22d3ee",
    "stats_bg": "#0f172a",
    "stats_fg": "#e2e8f0",
    "toggle_bg": "#64748b",
    "toggle_fg": "#ffffff",
    "toggle_active": "#475569",
}

THEME = LIGHT_THEME

FONT_BASE = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_SMALL = ("Segoe UI", 9)
FONT_MONO = ("Consolas", 10)
FONT_MONO_SMALL = ("Consolas", 9)


class TextHandler(logging.Handler):
    """Redirige los logs de logging a un widget Text de tkinter."""

    def __init__(self, text_widget: tk.Text) -> None:
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        self.text_widget.insert(tk.END, msg + '\n')
        self.text_widget.see(tk.END)


class OSSimulatorGUI:
    """Ventana principal del simulador.

    Construye toda la interfaz, maneja los eventos del usuario y lanza
    la simulación en un hilo separado.
    """

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("OS Simulator — J. Agudelo (Univalle 2026)")
        self.root.geometry("1200x700")
        self.root.configure(bg=THEME["bg_primary"])
        self.root.minsize(1000, 600)

        self.controller: Optional[SimulationController] = None
        self.is_running = False
        self._dark_mode = False

        self._create_layout()
        self._setup_styles()
        self._add_sample_processes()
        self._configure_event_bindings()

    def _create_layout(self) -> None:
        """Construye la disposición de todos los paneles de la ventana."""
        top_frame = tk.Frame(self.root, bg=THEME["bg_primary"])
        top_frame.pack(fill="both", expand=True, padx=12, pady=8)

        config_card = self._create_card(top_frame, "Configuration")
        config_card.pack(side="left", fill="both", padx=(0, 6))

        config_content = tk.Frame(config_card, bg=THEME["bg_secondary"])
        config_content.pack(fill="both", expand=True, padx=12, pady=8)
        self._build_config_controls(config_content)

        process_card = self._create_card(top_frame, "Processes")
        process_card.pack(side="right", fill="both", expand=True, padx=(6, 0))

        process_content = tk.Frame(process_card, bg=THEME["bg_secondary"])
        process_content.pack(fill="both", expand=True, padx=12, pady=8)
        self._build_process_table(process_content)

        bottom_paned = tk.PanedWindow(
            self.root, orient="horizontal", bg=THEME["border"], sashwidth=4
        )
        bottom_paned.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        memory_card = tk.Frame(bottom_paned, bg=THEME["bg_secondary"])
        self._build_card_inside(memory_card, "Memory Map")
        bottom_paned.add(memory_card, minsize=200)
        self._build_memory_panel(memory_card)

        logs_card = tk.Frame(bottom_paned, bg=THEME["bg_secondary"])
        self._build_card_inside(logs_card, "Log")
        bottom_paned.add(logs_card, minsize=250)
        self._build_log_panel(logs_card)

        stats_card = tk.Frame(bottom_paned, bg=THEME["bg_secondary"])
        self._build_card_inside(stats_card, "Statistics & Gantt")
        bottom_paned.add(stats_card, minsize=300)
        self._build_stats_panel(stats_card)

        self._build_statusbar()

    def _create_card(self, parent: tk.Widget, title: str) -> tk.Frame:
        """Crea un frame tipo tarjeta con una barra de título arriba."""
        outer = tk.Frame(parent, bg=THEME["bg_secondary"], relief="flat")

        title_bar = tk.Frame(outer, bg=THEME["bg_secondary"])
        title_bar.pack(fill="x", padx=12, pady=(10, 6))

        tk.Label(
            title_bar, text=title, bg=THEME["bg_secondary"],
            fg=THEME["text_primary"], font=FONT_TITLE,
        ).pack(anchor="w")

        tk.Frame(outer, height=1, bg=THEME["border"]).pack(fill="x", padx=12)

        return outer

    def _build_card_inside(self, frame: tk.Frame, title: str) -> None:
        """Pinta título y separador dentro de un frame (para usar con PanedWindow)."""
        title_bar = tk.Frame(frame, bg=THEME["bg_secondary"])
        title_bar.pack(fill="x", padx=12, pady=(10, 6))

        tk.Label(
            title_bar, text=title, bg=THEME["bg_secondary"],
            fg=THEME["text_primary"], font=FONT_TITLE,
        ).pack(anchor="w")

        tk.Frame(frame, height=1, bg=THEME["border"]).pack(fill="x", padx=12)

    def _build_config_controls(self, parent: tk.Widget) -> None:
        """Crea los controles de configuración: scheduler, quantum, memoria, cores y overhead."""
        fields = [
            ("Scheduler", "sched_var", config.SCHEDULER_TYPE, True),
            ("Quantum", "quantum_var", config.QUANTUM, False),
            ("Memory", "memory_var", config.MEMORY_CAPACITY, False),
            ("Cores", "cores_var", config.NUM_CORES, False),
            ("Context Switch", "overhead_var", getattr(config, 'CONTEXT_SWITCH_OVERHEAD', 0), False),
        ]

        self.sched_var = tk.StringVar()
        self.quantum_var = tk.IntVar()
        self.memory_var = tk.IntVar()
        self.cores_var = tk.IntVar()
        self.overhead_var = tk.IntVar()

        vars_map = {
            "sched_var": self.sched_var,
            "quantum_var": self.quantum_var,
            "memory_var": self.memory_var,
            "cores_var": self.cores_var,
            "overhead_var": self.overhead_var,
        }

        self.sched_var.set(config.SCHEDULER_TYPE)
        self.quantum_var.set(config.QUANTUM)
        self.memory_var.set(config.MEMORY_CAPACITY)
        self.cores_var.set(config.NUM_CORES)
        self.overhead_var.set(getattr(config, 'CONTEXT_SWITCH_OVERHEAD', 0))

        for i, (label, var_name, default, is_option) in enumerate(fields):
            row = tk.Frame(parent, bg=THEME["bg_secondary"])
            row.pack(fill="x", pady=4)

            tk.Label(
                row, text=label, bg=THEME["bg_secondary"],
                fg=THEME["text_secondary"], font=FONT_SMALL, width=14, anchor="w",
            ).pack(side="left")

            var_obj = vars_map[var_name]
            if is_option:
                opts = ['round_robin', 'fcfs', 'sjf', 'priority']
                menu = ttk.Combobox(
                    row, textvariable=var_obj, values=opts,
                    state="readonly", width=14, font=FONT_SMALL,
                )
                menu.pack(side="left", fill="x", expand=True)
            else:
                entry = tk.Entry(
                    row, textvariable=var_obj, bg=THEME["bg_input"],
                    fg=THEME["text_primary"], font=FONT_SMALL, relief="flat",
                )
                entry.pack(side="left", fill="x", expand=True, ipady=4)

        # Buttons
        btn_row = tk.Frame(parent, bg=THEME["bg_secondary"])
        btn_row.pack(fill="x", pady=(16, 4))

        self.start_button = tk.Button(
            btn_row, text="▶  Run Simulation",
            command=self.start_simulation,
            bg=THEME["bg_button_primary"], fg=THEME["text_on_primary"],
            font=FONT_BOLD, relief="flat", bd=0, padx=16, pady=8,
            activebackground="#1d4ed8", activeforeground=THEME["text_on_primary"],
            cursor="hand2",
        )
        self.start_button.pack(side="left", padx=(0, 8))

        self.clear_btn = tk.Button(
            btn_row, text="✕  Clear",
            command=self._clear_logs,
            bg=THEME["bg_button_secondary"], fg=THEME["text_on_primary"],
            font=FONT_SMALL, relief="flat", bd=0, padx=12, pady=8,
            activebackground="#4b5563", activeforeground=THEME["text_on_primary"],
            cursor="hand2",
        )
        self.clear_btn.pack(side="left")

    def _build_process_table(self, parent: tk.Widget) -> None:
        """Crea la tabla de procesos con columnas PID, Burst, Memory,
        Priority, Arrival e I/O Time.
        """
        columns = ("PID", "Burst", "Memory", "Priority", "Arrival", "I/O Time")
        self.tree = ttk.Treeview(
            parent, columns=columns, show="headings", height=8
        )
        self.tree.pack(fill="both", expand=True)

        col_widths = {
            "PID": 50, "Burst": 60, "Memory": 65,
            "Priority": 60, "Arrival": 55, "I/O Time": 65,
        }
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 70), anchor="center")

        # Button bar
        btn_bar = tk.Frame(parent, bg=THEME["bg_secondary"])
        btn_bar.pack(fill="x", pady=(8, 0))

        tk.Button(
            btn_bar, text="+  Add", command=self.add_process,
            bg=THEME["bg_button_primary"], fg=THEME["text_on_primary"],
            font=FONT_SMALL, relief="flat", bd=0, padx=12, pady=6,
            activebackground="#1d4ed8", cursor="hand2",
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            btn_bar, text="−  Remove", command=self.remove_process,
            bg=THEME["bg_button_danger"], fg=THEME["text_on_primary"],
            font=FONT_SMALL, relief="flat", bd=0, padx=12, pady=6,
            activebackground="#dc2626", cursor="hand2",
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            btn_bar, text="Reset to Sample", command=self._reset_processes,
            bg=THEME["bg_button_secondary"], fg=THEME["text_on_primary"],
            font=FONT_SMALL, relief="flat", bd=0, padx=12, pady=6,
            activebackground="#4b5563", cursor="hand2",
        ).pack(side="right")

    def _build_log_panel(self, parent: tk.Widget) -> None:
        """Crea el panel de log con ScrollText y conecta el handler de logging."""
        content = tk.Frame(parent, bg=THEME["bg_secondary"])
        content.pack(fill="both", expand=True, padx=12, pady=8)

        self.log_text = scrolledtext.ScrolledText(
            content, bg=THEME["log_bg"], fg=THEME["log_fg"],
            font=FONT_MONO_SMALL, relief="flat", padx=8, pady=8,
        )
        self.log_text.pack(fill="both", expand=True)

        handler = TextHandler(self.log_text)
        handler.setFormatter(logging.Formatter('%(asctime)s  %(message)s', datefmt='%H:%M:%S'))
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)

    def _build_memory_panel(self, parent: tk.Widget) -> None:
        """Crea el panel que muestra el mapa de memoria después de la simulación."""
        content = tk.Frame(parent, bg=THEME["bg_secondary"])
        content.pack(fill="both", expand=True, padx=12, pady=8)

        self.memory_text = scrolledtext.ScrolledText(
            content, bg=THEME["log_bg"], fg="#a5f3fc",
            font=FONT_MONO_SMALL, relief="flat", padx=8, pady=8,
            state="disabled",
        )
        self.memory_text.pack(fill="both", expand=True)
        self.memory_text.insert(tk.END, "Run a simulation to see memory usage.")

    def _build_stats_panel(self, parent: tk.Widget) -> None:
        """Crea el panel de estadísticas con Gantt y tabla de métricas por proceso."""
        content = tk.Frame(parent, bg=THEME["bg_secondary"])
        content.pack(fill="both", expand=True, padx=12, pady=8)

        self.stats_text = scrolledtext.ScrolledText(
            content, bg=THEME["stats_bg"], fg=THEME["stats_fg"],
            font=FONT_MONO, relief="flat", padx=12, pady=12,
            state="disabled", height=8,
        )
        self.stats_text.pack(fill="x", expand=False)
        self.stats_text.insert(tk.END, "Run a simulation to see statistics here.")

        process_metrics_frame = tk.Frame(content, bg=THEME["bg_secondary"])
        process_metrics_frame.pack(fill="both", expand=True, pady=(8, 0))

        tk.Label(
            process_metrics_frame, text="Per-Process Metrics",
            bg=THEME["bg_secondary"], fg=THEME["text_primary"],
            font=FONT_BOLD,
        ).pack(anchor="w", pady=(0, 4))

        columns = ("PID", "Burst", "Priority", "Waiting", "Turnaround", "Response")
        self.process_metrics_tree = ttk.Treeview(
            process_metrics_frame, columns=columns, show="headings", height=6,
        )
        self.process_metrics_tree.pack(fill="both", expand=True)

        col_widths = {
            "PID": 50, "Burst": 60, "Priority": 60,
            "Waiting": 80, "Turnaround": 90, "Response": 90,
        }
        for col in columns:
            self.process_metrics_tree.heading(col, text=col)
            self.process_metrics_tree.column(col, width=col_widths[col], anchor="center")
    
    def _build_statusbar(self) -> None:
        """Crea la barra inferior con el estado, botón de tema y contador de procesos."""
        self.status_bar = tk.Frame(self.root, bg=THEME["bg_statusbar"], height=28)
        self.status_bar.pack(fill="x", side="bottom")

        self.status_label = tk.Label(
            self.status_bar, text="OS Simulator — J. Agudelo | Univalle 2026 | Ready",
            bg=THEME["bg_statusbar"],
            fg=THEME["text_on_dark"], font=FONT_SMALL, anchor="w", padx=12,
        )
        self.status_label.pack(side="left")

        self.theme_btn = tk.Button(
            self.status_bar, text="☀ Light / Dark",
            command=self._toggle_theme,
            bg=THEME["toggle_bg"], fg=THEME["toggle_fg"],
            font=FONT_SMALL, relief="flat", bd=0, padx=10, pady=1,
            activebackground=THEME["toggle_active"],
            cursor="hand2",
        )
        self.theme_btn.pack(side="right", padx=(0, 8))

        self.proc_count_label = tk.Label(
            self.status_bar, text="", bg=THEME["bg_statusbar"],
            fg=THEME["text_on_dark"], font=FONT_SMALL, anchor="e", padx=12,
        )
        self.proc_count_label.pack(side="right")
        self._update_proc_count()
    
    def _setup_styles(self) -> None:
        """Configura el tema visual de ttk (Treeview, Combobox)."""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=THEME["bg_input"], foreground=THEME["text_primary"],
            fieldbackground=THEME["bg_input"], font=FONT_SMALL,
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background=THEME["bg_primary"], foreground=THEME["text_secondary"],
            font=FONT_BOLD, relief="flat",
        )
        style.map("Treeview.Heading", background=[("active", THEME["border"])])
        style.configure(
            "TCombobox",
            fieldbackground=THEME["bg_input"], foreground=THEME["text_primary"],
            font=FONT_SMALL,
        )
    
    def _update_proc_count(self) -> None:
        """Actualiza el label del contador de procesos en la barra de estado."""
        count = len(self.tree.get_children())
        self.proc_count_label.config(text=f"{count} process{'es' if count != 1 else ''}")
    
    def _add_sample_processes(self) -> None:
        """Carga los procesos de ejemplo en la tabla, incluyendo arrival e I/O."""
        for pid, burst, mem, pri, arrival, io_time in sample_processes():
            self.tree.insert(
                "", "end", values=(pid, burst, mem, pri, arrival, io_time)
            )
        self._update_proc_count()
    
    def add_process(self) -> None:
        """Abre una ventana emergente para agregar un proceso nuevo a la tabla.

        Incluye campos para PID, Burst Time, Memory, Priority,
        Arrival Time e I/O Time, permitiendo configurar llegadas
        escalonadas y operaciones de I/O desde la GUI.
        """
        win = tk.Toplevel(self.root)
        win.title("Add Process")
        win.geometry("340x300")
        win.configure(bg=THEME["bg_primary"])
        win.transient(self.root)
        win.grab_set()

        field_labels = [
            "PID", "Burst Time", "Memory", "Priority",
            "Arrival Time", "I/O Time",
        ]
        entries = []

        for i, label in enumerate(field_labels):
            tk.Label(
                win, text=label, bg=THEME["bg_primary"],
                fg=THEME["text_secondary"], font=FONT_SMALL,
            ).grid(row=i, column=0, padx=12, pady=6, sticky="e")

            entry = tk.Entry(
                win, bg=THEME["bg_input"], fg=THEME["text_primary"],
                font=FONT_SMALL, relief="flat", width=15,
            )
            entry.grid(row=i, column=1, padx=(0, 12), pady=6, sticky="w")
            entry.insert(0, "0")
            entries.append(entry)

        def save():
            """Valida los datos ingresados y agrega el proceso a la tabla."""
            try:
                raw = [int(e.get()) for e in entries]
                pid, burst, mem, pri, arrival, io_time = raw

                if pid <= 0:
                    messagebox.showerror("Error", "PID must be positive", parent=win)
                    return
                if burst <= 0:
                    messagebox.showerror("Error", "Burst time must be positive", parent=win)
                    return
                if mem <= 0:
                    messagebox.showerror("Error", "Memory must be positive", parent=win)
                    return
                if pri < 0:
                    messagebox.showerror("Error", "Priority cannot be negative", parent=win)
                    return
                if arrival < 0:
                    messagebox.showerror("Error", "Arrival time cannot be negative", parent=win)
                    return
                if io_time < 0:
                    messagebox.showerror("Error", "I/O time cannot be negative", parent=win)
                    return

                for item in self.tree.get_children():
                    if int(self.tree.item(item, 'values')[0]) == pid:
                        messagebox.showerror("Error", f"PID {pid} already exists", parent=win)
                        return

                self.tree.insert(
                    "", "end", values=(pid, burst, mem, pri, arrival, io_time)
                )
                self._update_proc_count()
                win.destroy()
            except ValueError:
                messagebox.showerror("Error", "All fields must be integers", parent=win)

        tk.Button(
            win, text="Save", command=save,
            bg=THEME["bg_button_primary"], fg=THEME["text_on_primary"],
            font=FONT_SMALL, relief="flat", bd=0, padx=20, pady=6,
            activebackground="#1d4ed8", cursor="hand2",
        ).grid(row=len(field_labels), column=0, columnspan=2, pady=12)

        win.bind("<Return>", lambda _: save())

    def remove_process(self) -> None:
        """Elimina el proceso seleccionado de la tabla."""
        selected = self.tree.selection()
        if selected:
            self.tree.delete(selected)
            self._update_proc_count()

    def start_simulation(self) -> None:
        """Toma la configuración actual, crea el controller y lanza la simulación en un hilo."""
        if self.is_running:
            return

        self.is_running = True
        self.start_button.config(state="disabled", bg="#94a3b8")
        self.clear_btn.config(state="disabled")
        self.log_text.delete(1.0, tk.END)

        for item in self.process_metrics_tree.get_children():
            self.process_metrics_tree.delete(item)

        self.status_label.config(text="Simulating...", fg="#facc15", bg=THEME["bg_statusbar"])

        sched_type = self.sched_var.get()
        quantum = self.quantum_var.get()
        memory_cap = self.memory_var.get()
        num_cores = max(1, self.cores_var.get())
        overhead = max(0, self.overhead_var.get())

        self.controller = SimulationController(
            sched_type, quantum, memory_cap, num_cores, overhead
        )
        self.controller.on_simulation_end = self.on_simulation_end

        for item in self.tree.get_children():
            values = self.tree.item(item, 'values')
            pid = int(values[0])
            burst = int(values[1])
            mem = int(values[2])
            pri = int(values[3])
            arrival = int(values[4]) if len(values) > 4 else 0
            io_time = int(values[5]) if len(values) > 5 else 0
            self.controller.add_process(pid, burst, mem, pri, arrival, io_time)

        sim_thread = threading.Thread(target=self._run_simulation_thread)
        sim_thread.start()

    def _run_simulation_thread(self) -> None:
        """Ejecuta la simulación (corre en un hilo aparte) y actualiza la UI al terminar."""
        try:
            stats = self.controller.start_simulation()
            self.root.after(0, self.on_simulation_end, stats)
        except Exception as e:
            logging.exception("Simulation crashed")
            self.root.after(0, self._reset_ui_after_error, str(e))
    
    def on_simulation_end(self, stats: dict) -> None:
        """Callback que se ejecuta al terminar la simulación: muestra resultados, memoria y re-activa la UI."""
        cpu_pct = stats['cpu_utilization'] * 100

        stats_text = (
            f"  Simulation Results\n"
            f"  {'─' * 36}\n"
            f"  Total Time:          {stats['total_time']:.2f} units\n"
            f"  Processes Completed: {stats['completed']}\n"
            f"  Throughput:          {stats['throughput']:.2f} proc/s\n"
            f"  Context Switches:    {stats['context_switches']}\n"
            f"  Avg Waiting Time:    {stats['avg_waiting_time']:.2f} units\n"
            f"  Avg Turnaround Time: {stats['avg_turnaround_time']:.2f} units\n"
            f"  Avg Response Time:   {stats['avg_response_time']:.2f} units\n"
            f"  CPU Utilization:     {cpu_pct:.1f}%\n"
            f"\n"
            f"  Gantt Chart\n"
            f"  {'─' * 36}\n"
            f"{stats['gantt_chart']}\n"
        )

        self.stats_text.config(state="normal")
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, stats_text)
        self.stats_text.config(state="disabled")

        # Update memory panel
        memory_map = self.controller.memory.memory_map()
        fragmentation = self.controller.memory.fragmentation_external()
        frag_pct = (fragmentation / self.controller.memory.capacity * 100) if self.controller.memory.capacity > 0 else 0
        used_bytes = self.controller.memory.used_frames * self.controller.memory.page_size
        free_bytes = self.controller.memory.capacity - used_bytes
        mem_text = (
            f"  Memory Map\n"
            f"  {'─' * 36}\n"
            f"{memory_map}\n"
            f"\n"
            f"  Used:     {used_bytes}/{self.controller.memory.capacity}\n"
            f"  Free:     {free_bytes}\n"
            f"  Frames:   {self.controller.memory.used_frames}/{self.controller.memory.num_frames}\n"
            f"  Frag Ext: {fragmentation} bytes ({frag_pct:.1f}%)\n"
        )
        self.memory_text.config(state="normal")
        self.memory_text.delete(1.0, tk.END)
        self.memory_text.insert(tk.END, mem_text)
        self.memory_text.config(state="disabled")

        self.status_label.config(text="Done", fg=THEME["bg_success"])
        self.start_button.config(state="normal", bg=THEME["bg_button_primary"])
        self.clear_btn.config(state="normal")
        self.is_running = False

        self._update_process_metrics_table(stats.get("process_metrics", []))

        logging.info("Simulation finished")
    
    def _update_process_metrics_table(self, metrics: list) -> None:
        """Refresca la tabla de métricas por proceso con los datos de la simulación."""
        for item in self.process_metrics_tree.get_children():
            self.process_metrics_tree.delete(item)

        for m in metrics:
            self.process_metrics_tree.insert(
                "", "end", values=(
                    m["pid"],
                    m["burst_time"],
                    m["priority"],
                    f'{m["waiting_time"]:.2f}',
                    f'{m["turnaround_time"]:.2f}',
                    f'{m["response_time"]:.2f}',
                ),
            )

    def _clear_logs(self) -> None:
        """Limpia logs, memoria, estadísticas y métricas, pero deja la tabla de procesos intacta."""
        self.log_text.delete(1.0, tk.END)
        self.memory_text.config(state="normal")
        self.memory_text.delete(1.0, tk.END)
        self.memory_text.insert(tk.END, "Run a simulation to see memory usage.")
        self.memory_text.config(state="disabled")
        self.stats_text.config(state="normal")
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, "Run a simulation to see statistics here.")
        self.stats_text.config(state="disabled")
        for item in self.process_metrics_tree.get_children():
            self.process_metrics_tree.delete(item)

    def _toggle_theme(self) -> None:
        """Alterna entre tema claro y oscuro.

        Cambia el diccionario THEME en el módulo y reconfigura los
        colores de todos los widgets visibles para reflejar el nuevo
        tema. El estado del toggle se persiste en self._dark_mode
        durante la sesión.
        """
        self._dark_mode = not self._dark_mode
        new = DARK_THEME if self._dark_mode else LIGHT_THEME
        THEME.update(new)
        self._apply_theme()

    def _apply_theme(self) -> None:
        """Reaplica el tema activo a TODA la jerarquía de widgets.

        Camina recursivamente todos los hijos del root y actualiza
        colores según el tipo de widget: frames, labels, entries,
        botones de acción y áreas de texto. El objetivo es que no
        quede ningún elemento con colores del tema anterior, imitando
        el comportamiento de un cambio de tema completo como en Chrome.
        """
        self.root.configure(bg=THEME["bg_primary"])

        # ─── 1. Barra de estado ──────────────────────────────────────
        self.status_bar.configure(bg=THEME["bg_statusbar"])
        self.status_label.configure(bg=THEME["bg_statusbar"], fg=THEME["text_on_dark"])
        self.proc_count_label.configure(bg=THEME["bg_statusbar"], fg=THEME["text_on_dark"])
        theme_icon = "☾" if self._dark_mode else "☀"
        self.theme_btn.configure(
            text=f"{theme_icon} Light / Dark",
            bg=THEME["toggle_bg"], fg=THEME["toggle_fg"],
            activebackground=THEME["toggle_active"],
        )

        # ─── 2. Botones principales ──────────────────────────────────
        self.start_button.configure(bg=THEME["bg_button_primary"])
        self.clear_btn.configure(bg=THEME["bg_button_secondary"])

        # ─── 3. Widgets de texto (log, memoria, estadisticas) ────────
        self.log_text.configure(bg=THEME["log_bg"], fg=THEME["log_fg"])
        self.memory_text.configure(bg=THEME["log_bg"], fg=THEME["log_fg"])
        self.stats_text.configure(bg=THEME["stats_bg"], fg=THEME["stats_fg"])

        # ─── 4. Estilos ttk (Treeview, Combobox) ─────────────────────
        style = ttk.Style()
        style.configure(
            "Treeview",
            background=THEME["bg_input"],
            foreground=THEME["text_primary"],
            fieldbackground=THEME["bg_input"],
        )
        style.configure(
            "Treeview.Heading",
            background=THEME["bg_primary"],
            foreground=THEME["text_secondary"],
        )
        style.map("Treeview.Heading", background=[("active", THEME["border"])])
        style.map("Treeview", background=[("selected", THEME["accent"])])
        style.configure(
            "TCombobox",
            fieldbackground=THEME["bg_input"],
            foreground=THEME["text_primary"],
            arrowcolor=THEME["text_secondary"],
        )

        # ─── 5. Pase recursivo por toda la ventana ───────────────────
        self._walk_and_theme(self.root)

    def _walk_and_theme(self, parent: tk.Widget) -> None:
        """Camina recursivamente los hijos de un widget y aplica el tema.

        Args:
            parent: Widget raíz cuyos hijos se recorrerán.
        """
        for child in parent.winfo_children():
            self._theme_widget(child)
            self._walk_and_theme(child)

    def _theme_widget(self, widget: tk.Widget) -> None:
        """Aplica colores del tema activo a un widget según su tipo.

        La función inspecciona la clase del widget y decide qué
        atributos de color actualizar. Los widgets ya configurados
        manualmente en _apply_theme() (statusbar, botones ppales,
        textos) se saltan para no pisar sus colores específicos.

        Heurística de frames:
        - Los frames hijo directo del root se dejan con bg_primary
          (área de fondo general).
        - Los frames anidados más profundo se asignan a bg_secondary
          (contenido de tarjetas y paneles).

        Args:
            widget: Widget a tematizar.
        """
        widget_class = widget.winfo_class()

        if widget_class == "Frame":
            if widget is self.status_bar:
                return
            parent = widget.nametowidget(widget.winfo_parent())
            if parent is self.root:
                widget.configure(bg=THEME["bg_primary"])
            else:
                widget.configure(bg=THEME["bg_secondary"])

        elif widget_class == "Label":
            current_bg = widget.cget("bg")
            if current_bg not in (THEME["bg_statusbar"],):
                widget.configure(bg=THEME["bg_secondary"], fg=THEME["text_primary"])

        elif widget_class == "Entry":
            widget.configure(
                bg=THEME["bg_input"], fg=THEME["text_primary"],
                insertbackground=THEME["text_primary"],
            )

        elif widget_class == "Button":
            current_bg = widget.cget("bg")
            light_button_bgs = {
                LIGHT_THEME["bg_button_primary"],
                LIGHT_THEME["bg_button_secondary"],
                LIGHT_THEME["bg_button_danger"],
            }
            dark_button_bgs = {
                DARK_THEME["bg_button_primary"],
                DARK_THEME["bg_button_secondary"],
                DARK_THEME["bg_button_danger"],
            }
            if current_bg in light_button_bgs:
                dark_map = {
                    LIGHT_THEME["bg_button_primary"]: DARK_THEME["bg_button_primary"],
                    LIGHT_THEME["bg_button_secondary"]: DARK_THEME["bg_button_secondary"],
                    LIGHT_THEME["bg_button_danger"]: DARK_THEME["bg_button_danger"],
                }
                new_bg = dark_map.get(current_bg, current_bg)
                widget.configure(bg=new_bg)
            elif current_bg in dark_button_bgs:
                light_map = {
                    DARK_THEME["bg_button_primary"]: LIGHT_THEME["bg_button_primary"],
                    DARK_THEME["bg_button_secondary"]: LIGHT_THEME["bg_button_secondary"],
                    DARK_THEME["bg_button_danger"]: LIGHT_THEME["bg_button_danger"],
                }
                new_bg = light_map.get(current_bg, current_bg)
                widget.configure(bg=new_bg)

        elif widget_class == "PanedWindow":
            widget.configure(bg=THEME["border"], sashwidth=4)

        elif widget_class in ("Text", "ScrolledText"):
            pass

    def _reset_processes(self) -> None:
        """Reemplaza la tabla de procesos con los procesos de ejemplo."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._add_sample_processes()

    def _reset_ui_after_error(self, error_msg: str) -> None:
        """Rehabilita la interfaz después de un error en la simulación y muestra el mensaje."""
        self.is_running = False
        self.start_button.config(state="normal", bg=THEME["bg_button_primary"])
        self.clear_btn.config(state="normal")
        self.status_label.config(text=f"Error: {error_msg}", fg=THEME["bg_button_danger"], bg=THEME["bg_statusbar"])
        logging.error(f"Simulation error: {error_msg}")

    def reset(self) -> None:
        self.is_running = False
        self.start_button.config(state="normal", bg=THEME["bg_button_primary"])
        self.clear_btn.config(state="normal")
        self._reset_processes()
        self._clear_logs()
        self.status_label.config(text="OS Simulator — J. Agudelo | Univalle 2026 | Ready", fg=THEME["text_on_dark"], bg=THEME["bg_statusbar"])
        
    def add_process_to_controller(self, pid: int, burst: int, mem: int, pri: int) -> None:
        """Agrega un proceso al controller durante la simulación y actualiza el contador."""
        """Agrega un proceso al controller durante la simulacion (si controller existe)."""
        if self.controller:
            self.controller.add_process(pid, burst, mem, pri)
            self._update_proc_count()
    
    def remove_process_from_controller(self, pid: int) -> None:
        """Remueve un proceso del controller durante la simulación y actualiza el contador."""
        """Remueve un proceso del controller durante la simulacion."""
        if self.controller:
            self.controller.remove_process(pid)
            self._update_proc_count()

    def on_closing(self) -> None:
        """Pregunta confirmación si hay una simulación corriendo antes de cerrar."""
        if self.is_running and messagebox.askokcancel("Quit", "A simulation is running. Do you really want to quit?"):
            self.root.destroy()
        elif not self.is_running:
            self.root.destroy()

    def _configure_event_bindings(self) -> None:
        """Registra el cierre seguro (Ctrl+W) y atajos de teclado (Ctrl+R reset, Ctrl+C copiar stats)."""
        """Registra atajos de teclado y el cierre seguro de la ventana."""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind("<Control-r>", lambda e: self.reset())
        self.root.bind(
            "<Control-c>",
            lambda e: self._copy_to_clipboard(self.stats_text.get(1.0, tk.END)),
        )

    def _copy_to_clipboard(self, text: str) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        
        messagebox.showinfo("Copied", "Statistics copied to clipboard!")

        self.root.after(2000, lambda: self.root.clipboard_clear())

    def import_sample_processes(self, processes: list) -> None:
        """Importa una lista de procesos al controller durante la simulacion (si controller existe)."""
        if self.controller:
            for pid, burst, mem, pri in processes:
                self.controller.add_process(pid, burst, mem, pri)

        self._update_proc_count()
        

    def update_proc_count(self) -> None:
        """Actualiza el contador de procesos en la barra de estado."""
        count = len(self.tree.get_children())
        self.proc_count_label.config(text=f"{count} process{'es' if count != 1 else ''}")


    def get_process_count(self):
        """Retorna el número actual de procesos en la tabla."""
        return len(self.tree.get_children())



if __name__ == "__main__":
    root = tk.Tk()
    app = OSSimulatorGUI(root)
    root.mainloop()