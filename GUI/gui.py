import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils import config
from utils.process_factory import sample_processes
from controllers.simulation_controller import SimulationController
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import logging


# ==============================================================================
# Modern Theme Palette
# ==============================================================================
THEME = {
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
}

FONT_BASE = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_SMALL = ("Segoe UI", 9)
FONT_MONO = ("Consolas", 10)
FONT_MONO_SMALL = ("Consolas", 9)


class TextHandler(logging.Handler):
    def __init__(self, text_widget: tk.Text) -> None:
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        self.text_widget.insert(tk.END, msg + '\n')
        self.text_widget.see(tk.END)


class OSSimulatorGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("OS Simulator — J. Agudelo (Univalle 2026)")
        self.root.geometry("1200x700")
        self.root.configure(bg=THEME["bg_primary"])
        self.root.minsize(1000, 600)

        self.controller: Optional[SimulationController] = None
        self.is_running = False

        self._create_layout()
        self._setup_styles()
        self._add_sample_processes()
        self._setup_memory_observer()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_layout(self) -> None:
        # ---- Top section: controls + process table (side by side) ----
        top_frame = tk.Frame(self.root, bg=THEME["bg_primary"])
        top_frame.pack(fill="both", expand=True, padx=12, pady=8)

        # Left: Configuration panel
        config_card = self._create_card(top_frame, "Configuration")
        config_card.pack(side="left", fill="both", padx=(0, 6))

        config_content = tk.Frame(config_card, bg=THEME["bg_secondary"])
        config_content.pack(fill="both", expand=True, padx=12, pady=8)
        self._build_config_controls(config_content)

        # Right: Process table
        process_card = self._create_card(top_frame, "Processes")
        process_card.pack(side="right", fill="both", expand=True, padx=(6, 0))

        process_content = tk.Frame(process_card, bg=THEME["bg_secondary"])
        process_content.pack(fill="both", expand=True, padx=12, pady=8)
        self._build_process_table(process_content)

        # ---- Bottom section: memory + fs + logs + stats ----
        bottom_paned = tk.PanedWindow(
            self.root, orient="horizontal", bg=THEME["border"], sashwidth=4
        )
        bottom_paned.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        # Memory panel
        memory_card = tk.Frame(bottom_paned, bg=THEME["bg_secondary"])
        self._build_card_inside(memory_card, "Memory Map")
        bottom_paned.add(memory_card, minsize=200)
        self._build_memory_panel(memory_card)

        # File System panel
        fs_card = tk.Frame(bottom_paned, bg=THEME["bg_secondary"])
        self._build_card_inside(fs_card, "File System")
        bottom_paned.add(fs_card, minsize=200)
        self._build_filesystem_panel(fs_card)

        # Logs panel
        logs_card = tk.Frame(bottom_paned, bg=THEME["bg_secondary"])
        self._build_card_inside(logs_card, "Log")
        bottom_paned.add(logs_card, minsize=250)
        self._build_log_panel(logs_card)

        # Stats panel
        stats_card = tk.Frame(bottom_paned, bg=THEME["bg_secondary"])
        self._build_card_inside(stats_card, "Statistics & Gantt")
        bottom_paned.add(stats_card, minsize=300)
        self._build_stats_panel(stats_card)

        # ---- Status bar ----
        self._build_statusbar()

    def _create_card(self, parent: tk.Widget, title: str) -> tk.Frame:
        """Crea un frame card con título. Retorna el frame contenedor."""
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
        """Agrega título y separador dentro de un frame existente (para PanedWindow)."""
        title_bar = tk.Frame(frame, bg=THEME["bg_secondary"])
        title_bar.pack(fill="x", padx=12, pady=(10, 6))

        tk.Label(
            title_bar, text=title, bg=THEME["bg_secondary"],
            fg=THEME["text_primary"], font=FONT_TITLE,
        ).pack(anchor="w")

        tk.Frame(frame, height=1, bg=THEME["border"]).pack(fill="x", padx=12)

    def _build_config_controls(self, parent: tk.Widget) -> None:
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

        tk.Button(
            btn_row, text="↺  Reset",
            command=self.reset,
            bg=THEME["bg_button_secondary"], fg=THEME["text_on_primary"],
            font=FONT_SMALL, relief="flat", bd=0, padx=12, pady=8,
            activebackground="#4b5563", activeforeground=THEME["text_on_primary"],
            cursor="hand2",
        ).pack(side="left", padx=(8, 0))

        tk.Button(
            btn_row, text="↓  Export",
            command=self._export_results,
            bg=THEME["bg_success"], fg=THEME["text_on_primary"],
            font=FONT_SMALL, relief="flat", bd=0, padx=12, pady=8,
            activebackground="#059669", activeforeground=THEME["text_on_primary"],
            cursor="hand2",
        ).pack(side="right")

    def _build_process_table(self, parent: tk.Widget) -> None:
        columns = ("PID", "Burst", "Memory", "Priority", "Arrival", "I/O")
        self.tree = ttk.Treeview(
            parent, columns=columns, show="headings", height=8
        )
        self.tree.pack(fill="both", expand=True)

        for col in columns:
            self.tree.heading(col, text=col)
            widths = {"PID": 50, "Burst": 70, "Memory": 80, "Priority": 70, "Arrival": 70, "I/O": 60}
            self.tree.column(col, width=widths.get(col, 80), anchor="center")

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
        content = tk.Frame(parent, bg=THEME["bg_secondary"])
        content.pack(fill="both", expand=True, padx=12, pady=8)

        self.log_text = scrolledtext.ScrolledText(
            content, bg=THEME["log_bg"], fg=THEME["log_fg"],
            font=FONT_MONO_SMALL, relief="flat", padx=8, pady=8,
        )
        self.log_text.pack(fill="both", expand=True)

        handler = TextHandler(self.log_text)
        handler.setFormatter(logging.Formatter('%(asctime)s  %(message)s', datefmt='%H:%M:%S'))
        root_logger = logging.getLogger()
        if not any(isinstance(h, TextHandler) for h in root_logger.handlers):
            root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)

    def _build_memory_panel(self, parent: tk.Widget) -> None:
        content = tk.Frame(parent, bg=THEME["bg_secondary"])
        content.pack(fill="both", expand=True, padx=12, pady=8)

        self.memory_text = scrolledtext.ScrolledText(
            content, bg=THEME["log_bg"], fg="#a5f3fc",
            font=FONT_MONO_SMALL, relief="flat", padx=8, pady=8,
            state="disabled",
        )
        self.memory_text.pack(fill="both", expand=True)
        self.memory_text.insert(tk.END, "Run a simulation to see memory usage.")

    def _build_filesystem_panel(self, parent: tk.Widget) -> None:
        content = tk.Frame(parent, bg=THEME["bg_secondary"])
        content.pack(fill="both", expand=True, padx=12, pady=8)

        self.fs_text = scrolledtext.ScrolledText(
            content, bg=THEME["log_bg"], fg="#a5f3fc",
            font=FONT_MONO_SMALL, relief="flat", padx=8, pady=8,
            state="disabled",
        )
        self.fs_text.pack(fill="both", expand=True)
        self.fs_text.insert(tk.END, "Run a simulation to see file system tree.")

        self.page_table_text = scrolledtext.ScrolledText(
            content, bg=THEME["log_bg"], fg="#c4b5fd",
            font=FONT_MONO_SMALL, relief="flat", padx=8, pady=8,
            state="disabled", height=8,
        )
        self.page_table_text.pack(fill="both", expand=True, pady=(8, 0))
        self.page_table_text.insert(tk.END, "Page tables appear after simulation.")

    def _setup_memory_observer(self) -> None:
        pass

    def _show_page_tables(self) -> None:
        if not self.controller:
            return
        lines = []
        for pid in sorted(self.controller.memory.page_tables.keys()):
            lines.append(self.controller.memory.page_table_str(pid))
            lines.append("")
        text = "\n".join(lines) if lines else "No page tables available."
        self.page_table_text.config(state="normal")
        self.page_table_text.delete(1.0, tk.END)
        self.page_table_text.insert(tk.END, text)
        self.page_table_text.config(state="disabled")

    def _export_results(self) -> None:
        if not self.controller:
            messagebox.showinfo("Export", "Run a simulation first.")
            return
        import json
        from tkinter import filedialog
        stats = self.controller.start_simulation() if not hasattr(self, '_last_stats') else self._last_stats
        export_data = {
            "scheduler": self.sched_var.get(),
            "quantum": self.quantum_var.get(),
            "memory_capacity": self.memory_var.get(),
            "num_cores": self.cores_var.get(),
            "stats": stats,
        }
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if path:
            with open(path, "w") as f:
                json.dump(export_data, f, indent=2)
            messagebox.showinfo("Export", f"Results exported to {path}")

    def _build_stats_panel(self, parent: tk.Widget) -> None:
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

        columns = ("PID", "Burst", "Priority", "Waiting", "Turnaround", "Response", "I/O")
        self.process_metrics_tree = ttk.Treeview(
            process_metrics_frame, columns=columns, show="headings", height=6,
        )
        self.process_metrics_tree.pack(fill="both", expand=True)

        col_widths = {
            "PID": 50, "Burst": 60, "Priority": 60,
            "Waiting": 80, "Turnaround": 90, "Response": 90, "I/O": 60,
        }
        for col in columns:
            self.process_metrics_tree.heading(col, text=col)
            self.process_metrics_tree.column(col, width=col_widths[col], anchor="center")

    def _build_statusbar(self) -> None:
        self.status_bar = tk.Frame(self.root, bg=THEME["bg_statusbar"], height=28)
        self.status_bar.pack(fill="x", side="bottom")

        self.status_label = tk.Label(
            self.status_bar, text="OS Simulator — J. Agudelo | Univalle 2026 | Ready", bg=THEME["bg_statusbar"],
            fg=THEME["text_on_dark"], font=FONT_SMALL, anchor="w", padx=12,
        )
        self.status_label.pack(side="left")

        self.proc_count_label = tk.Label(
            self.status_bar, text="", bg=THEME["bg_statusbar"],
            fg=THEME["text_on_dark"], font=FONT_SMALL, anchor="e", padx=12,
        )
        self.proc_count_label.pack(side="right")
        self._update_proc_count()

    def _setup_styles(self) -> None:
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
        count = len(self.tree.get_children())
        self.proc_count_label.config(text=f"{count} process{'es' if count != 1 else ''}")

    def _add_sample_processes(self) -> None:
        for pid, burst, mem, pri, arrival in sample_processes():
            self.tree.insert("", "end", values=(pid, burst, mem, pri, arrival, 0))
        self._update_proc_count()

    def _reset_processes(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._add_sample_processes()

    def add_process(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("Add Process")
        win.geometry("320x280")
        win.configure(bg=THEME["bg_primary"])
        win.transient(self.root)
        win.grab_set()

        fields_data = [
            ("PID", 0), ("Burst Time", 0), ("Memory", 0),
            ("Priority", 0), ("Arrival", 0), ("I/O Time", 0),
        ]
        entries = []

        for i, (label, _) in enumerate(fields_data):
            tk.Label(
                win, text=label, bg=THEME["bg_primary"],
                fg=THEME["text_secondary"], font=FONT_SMALL,
            ).grid(row=i, column=0, padx=12, pady=8, sticky="e")

            entry = tk.Entry(
                win, bg=THEME["bg_input"], fg=THEME["text_primary"],
                font=FONT_SMALL, relief="flat", width=15,
            )
            entry.grid(row=i, column=1, padx=(0, 12), pady=8, sticky="w")
            entry.insert(0, "0")
            entries.append(entry)

        def save():
            try:
                values = [int(e.get()) for e in entries]
                pid, burst, mem, pri, arrival, io_time = values

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
                    if self.tree.item(item, 'values')[0] == pid:
                        messagebox.showerror("Error", f"PID {pid} already exists", parent=win)
                        return

                self.tree.insert("", "end", values=values)
                self._update_proc_count()
                win.destroy()
            except ValueError:
                messagebox.showerror("Error", "All fields must be integers", parent=win)

        tk.Button(
            win, text="Save", command=save,
            bg=THEME["bg_button_primary"], fg=THEME["text_on_primary"],
            font=FONT_SMALL, relief="flat", bd=0, padx=20, pady=6,
            activebackground="#1d4ed8", cursor="hand2",
        ).grid(row=6, column=0, columnspan=2, pady=12)

        win.bind("<Return>", lambda _: save())

    def remove_process(self) -> None:
        selected = self.tree.selection()
        if selected:
            self.tree.delete(selected)
            self._update_proc_count()

    def start_simulation(self) -> None:
        if self.is_running:
            return

        self.is_running = True
        self.start_button.config(state="disabled", bg="#94a3b8")
        self.clear_btn.config(state="disabled")
        self.log_text.delete(1.0, tk.END)

        for item in self.process_metrics_tree.get_children():
            self.process_metrics_tree.delete(item)

        self.status_label.config(text="Simulating...", fg="#facc15")

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
            pid, burst, mem, pri = int(values[0]), int(values[1]), int(values[2]), int(values[3])
            arrival = int(values[4]) if len(values) > 4 else 0
            io_time = int(values[5]) if len(values) > 5 else 0
            self.controller.add_process(pid, burst, mem, pri, arrival, io_time)

        sim_thread = threading.Thread(target=self._run_simulation_thread)
        sim_thread.start()

    def _run_simulation_thread(self) -> None:
        stats = self.controller.start_simulation()
        self.root.after(0, self.on_simulation_end, stats)

    def on_simulation_end(self, stats: dict) -> None:
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

        fs_tree = self.controller.filesystem.tree("/")
        self.fs_text.config(state="normal")
        self.fs_text.delete(1.0, tk.END)
        self.fs_text.insert(tk.END, fs_tree if fs_tree else "No files created.")
        self.fs_text.config(state="disabled")

        self._last_stats = stats

        logging.info("Simulation finished")

    def _update_process_metrics_table(self, metrics: list) -> None:
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
                    m.get("total_io_time", 0),
                ),
            )

    def _clear_logs(self) -> None:
        self.log_text.delete(1.0, tk.END)
        self.memory_text.config(state="normal")
        self.memory_text.delete(1.0, tk.END)
        self.memory_text.insert(tk.END, "Run a simulation to see memory usage.")
        self.memory_text.config(state="disabled")
        self.fs_text.config(state="normal")
        self.fs_text.delete(1.0, tk.END)
        self.fs_text.insert(tk.END, "Run a simulation to see file system tree.")
        self.fs_text.config(state="disabled")
        self.page_table_text.config(state="normal")
        self.page_table_text.delete(1.0, tk.END)
        self.page_table_text.insert(tk.END, "Page tables appear after simulation.")
        self.page_table_text.config(state="disabled")
        self.stats_text.config(state="normal")
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, "Run a simulation to see statistics here.")
        self.stats_text.config(state="disabled")
        for item in self.process_metrics_tree.get_children():
            self.process_metrics_tree.delete(item)

    def _reset_processes(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._add_sample_processes()

    def reset(self) -> None:
        """Resetea el estado para permitir una nueva simulación sin reiniciar la app."""
        self._reset_processes()
        self._clear_logs()
        self.status_label.config(text="Ready", fg=THEME["text_on_dark"])

    def add_process_to_controller(self, pid: int, burst: int, mem: int, pri: int) -> None:
        """Agrega un proceso al controller durante la simulación (si existe)."""
        if self.controller:
            self.controller.add_process(pid, burst, mem, pri)
            self._update_proc_count()

    def remove_process_from_controller(self, pid: int) -> None:
        """Remueve un proceso del controller durante la simulación (si existe)."""
        if self.controller:
            self.controller.remove_process(pid)
            self._update_proc_count()

    def on_closing(self) -> None:
        if self.is_running and messagebox.askokcancel("Quit", "A simulation is running. Do you really want to quit?"):
            self.root.destroy()
        elif not self.is_running:
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = OSSimulatorGUI(root)
    root.mainloop()