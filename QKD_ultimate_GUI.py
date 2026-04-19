"""
Ultimate QKD GUI - Ultra-Practical Version
- Chunk size slider (50K to 10M)
- Quick presets for common configurations
- Real-time parameter preview
- Comparison mode
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import os
import sys
import re
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.patches as mpatches


class UltimateQKDGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("QKD Ultimate Analysis Suite")
        self.root.geometry("1500x850")
        
        # Data storage
        self.results = []
        self.dataset_colors = {}
        self.color_palette = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
        self.color_index = 0
        
        self.algo_markers = {
            'original': 'o',
            'yanetal': 's',
            'option7': '^',
            'option8': 'D'
        }
        
        # Configuration variables
        self.file_path = tk.StringVar(value="")
        self.chunk_size = tk.IntVar(value=2_000_000)
        self.algorithm = tk.StringVar(value="yanetal")
        self.pa_method = tk.StringVar(value="sha256")
        self.pe_sample = tk.DoubleVar(value=0.1)
        
        # NEW: Comparison mode
        self.comparison_mode = tk.BooleanVar(value=False)
        
        # Plot axis variables
        self.x_axis = tk.StringVar(value="chunk")
        self.y_axis = tk.StringVar(value="efficiency")
        
        # Available metrics
        self.available_metrics = {
            'chunk': 'Chunk Size',
            'algorithm': 'Algorithm',
            'pa_method': 'PA Method',
            'pe_sample': 'PE Sample (%)',
            'efficiency': 'Overall Efficiency (%)',
            'time': 'Processing Time (s)',
            'final_keys': 'Final Key Bits',
            'qber': 'QBER (%)',
            'cascade_eff': 'Cascade Efficiency',
            'leaked_bits': 'Leaked Bits',
            'skr': 'Secret Key Rate'
        }
        
        # Presets
        self.presets = {
            'Fast Test': {'chunk': 100_000, 'algo': 'original', 'pa': 'sha256', 'pe': 0.05},
            'Balanced ⭐': {'chunk': 2_000_000, 'algo': 'yanetal', 'pa': 'sha256', 'pe': 0.10},
            'High Quality': {'chunk': 5_000_000, 'algo': 'option8', 'pa': 'sha256', 'pe': 0.15},
            'Theoretical': {'chunk': 2_000_000, 'algo': 'yanetal', 'pa': 'toeplitz', 'pe': 0.10}
        }
        
        self.create_widgets()
    
    def create_widgets(self):
        # ═══════════════════════════════════════════════════════
        # MAIN LAYOUT: LEFT (Config) | RIGHT (Plot)
        # ═══════════════════════════════════════════════════════
        
        left_panel = tk.Frame(self.root, width=550, bg="#ecf0f1")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10)
        left_panel.pack_propagate(False)
        
        right_panel = tk.Frame(self.root, bg="white")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ═══════════════════════════════════════════════════════
        # LEFT PANEL - SCROLLABLE CONFIG
        # ═══════════════════════════════════════════════════════
        
        canvas = tk.Canvas(left_panel, bg="#ecf0f1")
        scrollbar = ttk.Scrollbar(left_panel, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Title
        title = tk.Label(scrollable, text="🚀 QKD Ultimate Suite", 
                        font=("Arial", 16, "bold"), bg="#ecf0f1")
        title.pack(pady=(10, 5))
        
        subtitle = tk.Label(scrollable, text="Advanced Post-Processing & Analysis", 
                           font=("Arial", 9), fg="gray", bg="#ecf0f1")
        subtitle.pack(pady=(0, 15))
        
        # ───────────────────────────────────────────────────────
        # QUICK PRESETS (NEW!)
        # ───────────────────────────────────────────────────────
        preset_frame = ttk.LabelFrame(scrollable, text="⚡ Quick Presets", padding="10")
        preset_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        preset_buttons_frame = tk.Frame(preset_frame, bg="white")
        preset_buttons_frame.pack(fill=tk.X)
        
        for i, (preset_name, preset_config) in enumerate(self.presets.items()):
            btn = tk.Button(preset_buttons_frame, text=preset_name,
                           command=lambda p=preset_config: self.apply_preset(p),
                           bg="#34495e", fg="white", font=("Arial", 8),
                           cursor="hand2", padx=8, pady=5)
            btn.grid(row=i//2, column=i%2, padx=5, pady=5, sticky="ew")
            preset_buttons_frame.grid_columnconfigure(i%2, weight=1)
        
        # ───────────────────────────────────────────────────────
        # FILE SELECTION
        # ───────────────────────────────────────────────────────
        file_frame = ttk.LabelFrame(scrollable, text="📁 Dataset", padding="10")
        file_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        self.file_label = tk.Label(file_frame, text="No file selected", 
                                   fg="gray", wraplength=500, justify=tk.LEFT)
        self.file_label.pack(pady=(0, 10))
        
        browse_btn = tk.Button(file_frame, text="📂 Browse", 
                              command=self.browse_file,
                              bg="#3498db", fg="white", 
                              font=("Arial", 10, "bold"),
                              cursor="hand2", padx=15, pady=8)
        browse_btn.pack()
        
        # ───────────────────────────────────────────────────────
        # CHUNK SIZE SLIDER (NEW!)
        # ───────────────────────────────────────────────────────
        chunk_frame = ttk.LabelFrame(scrollable, text="📦 Chunk Size", padding="10")
        chunk_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        # Current value display
        self.chunk_display = tk.Label(chunk_frame, 
                                     text=f"{self.chunk_size.get():,} rows (~{self.estimate_ram(self.chunk_size.get())})",
                                     font=("Arial", 11, "bold"), fg="#2c3e50")
        self.chunk_display.pack(pady=(0, 10))
        
        # Slider
        chunk_slider = tk.Scale(chunk_frame, from_=0, to=20, 
                               orient=tk.HORIZONTAL,
                               showvalue=0,
                               command=self.update_chunk_display,
                               length=450, sliderlength=30)
        chunk_slider.pack(fill=tk.X)
        
        # Map slider positions to chunk sizes (logarithmic-ish)
        self.chunk_map = {
            0: 50_000, 1: 100_000, 2: 150_000, 3: 200_000, 4: 250_000,
            5: 300_000, 6: 400_000, 7: 500_000, 8: 750_000, 9: 1_000_000,
            10: 1_500_000, 11: 2_000_000, 12: 2_500_000, 13: 3_000_000,
            14: 4_000_000, 15: 5_000_000, 16: 6_000_000, 17: 7_500_000,
            18: 8_000_000, 19: 9_000_000, 20: 10_000_000
        }
        
        # Set initial slider position
        reverse_map = {v: k for k, v in self.chunk_map.items()}
        chunk_slider.set(reverse_map.get(2_000_000, 11))
        
        # Quick buttons
        quick_chunk_frame = tk.Frame(chunk_frame, bg="white")
        quick_chunk_frame.pack(fill=tk.X, pady=(10, 0))
        
        quick_sizes = [
            ("100K", 100_000),
            ("1M", 1_000_000),
            ("2M ⭐", 2_000_000),
            ("5M", 5_000_000),
            ("10M", 10_000_000)
        ]
        
        for i, (label, size) in enumerate(quick_sizes):
            btn = tk.Button(quick_chunk_frame, text=label,
                           command=lambda s=size, sl=chunk_slider, rm=reverse_map: sl.set(rm.get(s, 11)),
                           bg="#95a5a6", fg="white", font=("Arial", 8),
                           cursor="hand2", padx=8, pady=3)
            btn.grid(row=0, column=i, padx=2, sticky="ew")
            quick_chunk_frame.grid_columnconfigure(i, weight=1)
        
        # ───────────────────────────────────────────────────────
        # ALGORITHM
        # ───────────────────────────────────────────────────────
        algo_frame = ttk.LabelFrame(scrollable, text="⚙️ Cascade Algorithm", padding="10")
        algo_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        algo_options = [
            ("original", "Original - 4 passes (fastest)"),
            ("yanetal", "Yanetal - 10 passes (balanced) ⭐"),
            ("option7", "Option7 - 14 passes (good)"),
            ("option8", "Option8 - 14 passes (best efficiency)")
        ]
        
        for value, text in algo_options:
            rb = ttk.Radiobutton(algo_frame, text=text, 
                                variable=self.algorithm, value=value)
            rb.pack(anchor=tk.W, pady=2)
        
        # ───────────────────────────────────────────────────────
        # PRIVACY AMPLIFICATION
        # ───────────────────────────────────────────────────────
        pa_frame = ttk.LabelFrame(scrollable, text="🔐 Privacy Amplification", padding="10")
        pa_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        pa_options = [
            ("sha256", "SHA-256 (fast, practical) ⭐"),
            ("toeplitz", "Toeplitz Matrix (slow, theoretical)")
        ]
        
        for value, text in pa_options:
            rb = ttk.Radiobutton(pa_frame, text=text, 
                                variable=self.pa_method, value=value)
            rb.pack(anchor=tk.W, pady=2)
        
        # ───────────────────────────────────────────────────────
        # PARAMETER ESTIMATION SLIDER (NEW!)
        # ───────────────────────────────────────────────────────
        pe_frame = ttk.LabelFrame(scrollable, text="📊 Parameter Estimation Sample", padding="10")
        pe_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        self.pe_display = tk.Label(pe_frame, 
                                  text=f"{self.pe_sample.get()*100:.0f}% (±{self.estimate_qber_error(self.pe_sample.get()):.2f}% QBER error)",
                                  font=("Arial", 10, "bold"), fg="#2c3e50")
        self.pe_display.pack(pady=(0, 10))
        
        pe_slider = tk.Scale(pe_frame, from_=5, to=20, 
                            orient=tk.HORIZONTAL,
                            showvalue=0,
                            command=self.update_pe_display,
                            length=450, sliderlength=30)
        pe_slider.set(10)
        pe_slider.pack(fill=tk.X)
        
        tk.Label(pe_frame, text="5% (Fast)", font=("Arial", 8), fg="gray").place(relx=0, rely=1, anchor="sw")
        tk.Label(pe_frame, text="20% (Accurate)", font=("Arial", 8), fg="gray").place(relx=1, rely=1, anchor="se")
        
        # ───────────────────────────────────────────────────────
        # PLOT CONFIGURATION
        # ───────────────────────────────────────────────────────
        plot_config = ttk.LabelFrame(scrollable, text="📈 Plot Axes", padding="10")
        plot_config.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        tk.Label(plot_config, text="X-axis:", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        x_dropdown = ttk.Combobox(plot_config, textvariable=self.x_axis, 
                                 values=list(self.available_metrics.keys()),
                                 state='readonly', width=40)
        x_dropdown.pack(fill=tk.X, pady=(5, 10))
        
        tk.Label(plot_config, text="Y-axis:", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        y_dropdown = ttk.Combobox(plot_config, textvariable=self.y_axis,
                                 values=list(self.available_metrics.keys()),
                                 state='readonly', width=40)
        y_dropdown.pack(fill=tk.X, pady=(5, 0))
        
        x_dropdown.bind('<<ComboboxSelected>>', lambda e: self.update_plot())
        y_dropdown.bind('<<ComboboxSelected>>', lambda e: self.update_plot())
        
        # ───────────────────────────────────────────────────────
        # COMPARISON MODE (NEW!)
        # ───────────────────────────────────────────────────────
        comp_frame = ttk.LabelFrame(scrollable, text="🔄 Comparison Mode", padding="10")
        comp_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        comp_check = ttk.Checkbutton(comp_frame, 
                                     text="Enable auto-comparison (vary one parameter)",
                                     variable=self.comparison_mode)
        comp_check.pack(anchor=tk.W)
        
        self.comp_param = tk.StringVar(value="chunk")
        tk.Label(comp_frame, text="Vary:", font=("Arial", 9)).pack(anchor=tk.W, pady=(10, 5))
        
        comp_options = [
            ("chunk", "Chunk Size"),
            ("algorithm", "Algorithm"),
            ("pa_method", "PA Method"),
            ("pe_sample", "PE Sample")
        ]
        
        for value, text in comp_options:
            rb = ttk.Radiobutton(comp_frame, text=text,
                                variable=self.comp_param, value=value)
            rb.pack(anchor=tk.W, padx=20, pady=1)
        
        # ───────────────────────────────────────────────────────
        # ACTION BUTTONS
        # ───────────────────────────────────────────────────────
        button_frame = tk.Frame(scrollable, bg="#ecf0f1")
        button_frame.pack(fill=tk.X, padx=10, pady=(20, 10))
        
        run_btn = tk.Button(button_frame, text="🚀 RUN EXPERIMENT", 
                           command=self.run_experiment,
                           bg="#27ae60", fg="white",
                           font=("Arial", 12, "bold"),
                           cursor="hand2", padx=20, pady=12)
        run_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Secondary buttons row
        secondary_frame = tk.Frame(button_frame, bg="#ecf0f1")
        secondary_frame.pack(fill=tk.X)
        
        clear_btn = tk.Button(secondary_frame, text="🗑️ Clear", 
                             command=self.clear_plot,
                             bg="#e74c3c", fg="white",
                             font=("Arial", 9),
                             cursor="hand2", padx=10, pady=6)
        clear_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        export_btn = tk.Button(secondary_frame, text="💾 Export",
                              command=self.export_results,
                              bg="#2980b9", fg="white",
                              font=("Arial", 9),
                              cursor="hand2", padx=10, pady=6)
        export_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Status
        self.status_label = tk.Label(scrollable, text="Ready to process", 
                                     bg="#ecf0f1", fg="gray",
                                     font=("Arial", 9), wraplength=520)
        self.status_label.pack(pady=10)
        
        # ═══════════════════════════════════════════════════════
        # RIGHT PANEL - PLOT
        # ═══════════════════════════════════════════════════════
        
        plot_title = tk.Label(right_panel, text="📊 Live Results", 
                             font=("Arial", 14, "bold"), bg="white")
        plot_title.pack(pady=(0, 10))
        
        self.fig = Figure(figsize=(10, 7), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_panel)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.update_plot()
    
    def estimate_ram(self, chunk_size):
        """Estimate RAM usage for chunk size"""
        mb = (chunk_size * 8 * 4) / (1024 * 1024)  # Rough estimate
        if mb < 1024:
            return f"{mb:.0f}MB RAM"
        else:
            return f"{mb/1024:.1f}GB RAM"
    
    def estimate_qber_error(self, pe_sample):
        """Estimate QBER confidence interval width"""
        # Rough estimate: error ~ 1/sqrt(sample_size)
        if pe_sample <= 0:
            return 1.0
        return 0.3 / (pe_sample ** 0.5)
    
    def update_chunk_display(self, slider_val):
        """Update chunk size display from slider"""
        slider_pos = int(float(slider_val))
        chunk_val = self.chunk_map.get(slider_pos, 2_000_000)
        self.chunk_size.set(chunk_val)
        
        self.chunk_display.config(
            text=f"{chunk_val:,} rows (~{self.estimate_ram(chunk_val)})"
        )
    
    def update_pe_display(self, slider_val):
        """Update PE sample display from slider"""
        pe_val = int(slider_val) / 100.0
        self.pe_sample.set(pe_val)
        
        self.pe_display.config(
            text=f"{pe_val*100:.0f}% (±{self.estimate_qber_error(pe_val):.2f}% QBER error)"
        )
    
    def apply_preset(self, preset_config):
        """Apply a preset configuration"""
        self.chunk_size.set(preset_config['chunk'])
        self.algorithm.set(preset_config['algo'])
        self.pa_method.set(preset_config['pa'])
        self.pe_sample.set(preset_config['pe'])
        
        # Update displays
        self.chunk_display.config(
            text=f"{preset_config['chunk']:,} rows (~{self.estimate_ram(preset_config['chunk'])})"
        )
        self.pe_display.config(
            text=f"{preset_config['pe']*100:.0f}% (±{self.estimate_qber_error(preset_config['pe']):.2f}% QBER error)"
        )
        
        messagebox.showinfo("Preset Applied", 
                           f"Configuration loaded!\n\n"
                           f"Chunk: {preset_config['chunk']:,}\n"
                           f"Algorithm: {preset_config['algo']}\n"
                           f"PA: {preset_config['pa']}\n"
                           f"PE: {preset_config['pe']*100:.0f}%")
    
    def browse_file(self):
        """Browse for dataset file"""
        filename = filedialog.askopenfilename(
            title="Select QKD Dataset",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir="raw_data" if os.path.exists("raw_data") else "."
        )
        
        if filename:
            self.file_path.set(filename)
            display_name = os.path.basename(filename)
            self.file_label.config(text=display_name, fg="black")
    
    def run_experiment(self):
        """Run single experiment or comparison batch"""
        if not self.file_path.get():
            messagebox.showerror("Error", "Please select a dataset first!")
            return
        
        if self.comparison_mode.get():
            self.run_comparison()
        else:
            self.run_single()
    
    def run_single(self):
        """Run single configuration"""
        self.status_label.config(text="Running... (may take several minutes)", fg="orange")
        self.root.update()
        
        try:
            result = self.run_processing_core()
            if result:
                self.results.append(result)
                self.update_plot()
                self.status_label.config(text=f"✅ Done! Efficiency: {result['efficiency']:.2f}%", fg="green")
            else:
                self.status_label.config(text="❌ Processing failed", fg="red")
        except Exception as e:
            messagebox.showerror("Error", f"Failed:\n{e}")
            self.status_label.config(text="❌ Error", fg="red")
    
    def run_comparison(self):
        """Run comparison mode - vary one parameter"""
        param = self.comp_param.get()
        
        if param == "chunk":
            variants = [100_000, 1_000_000, 2_000_000, 5_000_000]
            original = self.chunk_size.get()
            # Auto-adjust axes for better visualization
            suggested_x = "chunk"
            suggested_y = "time"
        elif param == "algorithm":
            variants = ['original', 'yanetal', 'option7', 'option8']
            original = self.algorithm.get()
            suggested_x = "time"
            suggested_y = "efficiency"
        elif param == "pa_method":
            variants = ['sha256', 'toeplitz']
            original = self.pa_method.get()
            suggested_x = "time"
            suggested_y = "efficiency"
        elif param == "pe_sample":
            variants = [0.05, 0.10, 0.15, 0.20]
            original = self.pe_sample.get()
            suggested_x = "qber"
            suggested_y = "efficiency"
        
        # Suggest axes adjustment
        msg = f"Run {len(variants)} experiments varying {param}?\n\n"
        msg += f"Suggested axes:\n"
        msg += f"X: {self.available_metrics[suggested_x]}\n"
        msg += f"Y: {self.available_metrics[suggested_y]}\n\n"
        msg += f"Apply suggested axes?"
        
        response = messagebox.askyesnocancel("Comparison Mode", msg)
        
        if response is None:  # Cancel
            return
        elif response is True:  # Yes - apply suggested axes
            self.x_axis.set(suggested_x)
            self.y_axis.set(suggested_y)
        # If No, keep current axes
        
        success_count = 0
        
        for i, variant in enumerate(variants):
            self.status_label.config(
                text=f"Comparison {i+1}/{len(variants)}: {param}={variant}", 
                fg="orange"
            )
            self.root.update()
            
            # Set variant
            if param == "chunk":
                self.chunk_size.set(variant)
            elif param == "algorithm":
                self.algorithm.set(variant)
            elif param == "pa_method":
                self.pa_method.set(variant)
            elif param == "pe_sample":
                self.pe_sample.set(variant)
            
            # Run
            try:
                result = self.run_processing_core()
                if result:
                    self.results.append(result)
                    success_count += 1
                    print(f"✅ Variant {variant}: Efficiency={result['efficiency']:.2f}%, Time={result['time']:.1f}s")
                    self.update_plot()
                else:
                    print(f"❌ Variant {variant}: Processing returned None")
            except Exception as e:
                print(f"❌ Variant {variant} failed: {e}")
                import traceback
                traceback.print_exc()
        
        # Restore original
        if param == "chunk":
            self.chunk_size.set(original)
        elif param == "algorithm":
            self.algorithm.set(original)
        elif param == "pa_method":
            self.pa_method.set(original)
        elif param == "pe_sample":
            self.pe_sample.set(original)
        
        self.status_label.config(text=f"✅ Comparison complete! {success_count}/{len(variants)} successful", fg="green")
        messagebox.showinfo("Done", f"Comparison of {param} complete!\n{success_count}/{len(variants)} experiments successful.\n\nCheck console for details.")
    
    def run_processing_core(self):
        """Core processing logic (same as before)"""
        cmd = [
            sys.executable,
            "process_large_file.py",
            "--data", self.file_path.get(),
            "--chunk", str(self.chunk_size.get()),
            "--algo", self.algorithm.get(),
            "--pa-method", self.pa_method.get(),
            "--pe-sample", str(self.pe_sample.get())
        ]
        
        print(f"\n{'='*60}")
        print(f"Running: {' '.join(cmd)}")
        print(f"{'='*60}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
            output = result.stdout + result.stderr
            
            print("Output preview (first 500 chars):")
            print(output[:500])
            print("...")
            
            # Parse (same as before)
            efficiency_match = re.search(r'Overall efficiency:\s+([\d.]+)%', output)
            final_keys_match = re.search(r'Total final keys:\s+([\d,]+)\s+bits', output)
            time_match = re.search(r'Elapsed time:\s+([\d.]+)\s+seconds', output)
            qber_match = re.search(r'Average QBER:\s+([\d.]+)%', output)
            cascade_eff_match = re.search(r'Cascade efficiency:\s+([\d.]+)', output)
            leaked_match = re.search(r'Total leaked:\s+([\d,]+)', output)
            
            if efficiency_match and final_keys_match:
                dataset_name = os.path.basename(self.file_path.get())
                
                if dataset_name not in self.dataset_colors:
                    self.dataset_colors[dataset_name] = self.color_palette[self.color_index % len(self.color_palette)]
                    self.color_index += 1
                
                final_keys = int(final_keys_match.group(1).replace(',', ''))
                efficiency = float(efficiency_match.group(1))
                time_val = float(time_match.group(1)) if time_match else 0
                
                result_dict = {
                    'dataset': dataset_name,
                    'chunk': self.chunk_size.get(),
                    'algorithm': self.algorithm.get(),
                    'pa_method': self.pa_method.get(),
                    'pe_sample': self.pe_sample.get(),
                    'efficiency': efficiency,
                    'final_keys': final_keys,
                    'time': time_val,
                    'qber': float(qber_match.group(1)) if qber_match else 0,
                    'cascade_eff': float(cascade_eff_match.group(1)) if cascade_eff_match else 0,
                    'leaked_bits': int(leaked_match.group(1).replace(',', '')) if leaked_match else 0,
                    'skr': final_keys / self.chunk_size.get() if self.chunk_size.get() > 0 else 0,
                    'color': self.dataset_colors[dataset_name],
                    'marker': self.algo_markers.get(self.algorithm.get(), 'o')
                }
                
                print(f"\n✅ Parsed result: Efficiency={efficiency:.2f}%, Time={time_val:.1f}s")
                return result_dict
            else:
                print(f"\n❌ Failed to parse output!")
                print(f"efficiency_match: {efficiency_match}")
                print(f"final_keys_match: {final_keys_match}")
                print(f"\nFull output:\n{output}")
                return None
                
        except subprocess.TimeoutExpired:
            print("❌ Timeout after 2 hours")
            return None
        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()
            raise e
    
    def get_axis_data(self, axis_key):
        """Extract axis data (same as before)"""
        data = []
        for result in self.results:
            if axis_key == 'algorithm':
                data.append(result.get('algorithm', 'unknown'))
            elif axis_key == 'pa_method':
                data.append(result.get('pa_method', 'unknown'))
            else:
                data.append(result.get(axis_key, 0))
        return data
    
    def update_plot(self):
        """Update plot with selected axes"""
        self.ax.clear()
        
        if not self.results:
            self.ax.text(0.5, 0.5, 'No experiments yet\nRun to see results', 
                        ha='center', va='center', fontsize=14, color='gray',
                        transform=self.ax.transAxes)
            self.ax.set_xlabel(self.available_metrics.get(self.x_axis.get(), 'X'), fontsize=12)
            self.ax.set_ylabel(self.available_metrics.get(self.y_axis.get(), 'Y'), fontsize=12)
            self.ax.grid(True, alpha=0.3)
        else:
            x_key = self.x_axis.get()
            y_key = self.y_axis.get()
            
            x_data = self.get_axis_data(x_key)
            y_data = self.get_axis_data(y_key)
            
            # Check if X or Y are categorical (algorithm or pa_method)
            x_is_categorical = x_key in ['algorithm', 'pa_method']
            y_is_categorical = y_key in ['algorithm', 'pa_method']
            
            # Convert categorical to numeric for plotting
            if x_is_categorical:
                unique_x = sorted(set(x_data))
                x_map = {val: i for i, val in enumerate(unique_x)}
                x_numeric = [x_map[val] for val in x_data]
            else:
                x_numeric = x_data
                unique_x = None
            
            if y_is_categorical:
                unique_y = sorted(set(y_data))
                y_map = {val: i for i, val in enumerate(unique_y)}
                y_numeric = [y_map[val] for val in y_data]
            else:
                y_numeric = y_data
                unique_y = None
            
            # Plot points
            for i, result in enumerate(self.results):
                self.ax.scatter(x_numeric[i], y_numeric[i],
                               c=result['color'], marker=result['marker'],
                               s=200, alpha=0.8, edgecolors='black', linewidths=2,
                               zorder=3)
                
                # Add labels for categorical axes
                if x_is_categorical or y_is_categorical:
                    label_text = ""
                    if 'algorithm' in [x_key, y_key]:
                        label_text = result['algorithm']
                    elif 'pa_method' in [x_key, y_key]:
                        label_text = result['pa_method'].upper()
                    
                    if label_text:
                        self.ax.annotate(label_text, 
                                       (x_numeric[i], y_numeric[i]),
                                       textcoords="offset points",
                                       xytext=(0, 10),
                                       ha='center',
                                       fontsize=8,
                                       bbox=dict(boxstyle='round,pad=0.3', 
                                               facecolor='yellow', 
                                               alpha=0.7))
            
            # Set axis labels
            self.ax.set_xlabel(self.available_metrics.get(x_key, 'X'), 
                              fontsize=12, fontweight='bold')
            self.ax.set_ylabel(self.available_metrics.get(y_key, 'Y'), 
                              fontsize=12, fontweight='bold')
            
            # Set ticks for categorical axes
            if x_is_categorical:
                self.ax.set_xticks(range(len(unique_x)))
                self.ax.set_xticklabels(unique_x, rotation=45, ha='right')
            
            if y_is_categorical:
                self.ax.set_yticks(range(len(unique_y)))
                self.ax.set_yticklabels(unique_y)
            
            self.ax.grid(True, alpha=0.3, linestyle='--', zorder=1)
            self.ax.set_title('QKD Processing Results', fontsize=14, fontweight='bold', pad=10)
            
            # Add legend if multiple datasets
            if len(self.dataset_colors) > 1:
                dataset_handles = [
                    mpatches.Patch(color=color, label=dataset) 
                    for dataset, color in self.dataset_colors.items()
                ]
                self.ax.legend(handles=dataset_handles, 
                             title="Datasets", 
                             loc='best',
                             fontsize=9)
        
        self.canvas.draw()
    
    def clear_plot(self):
        """Clear results"""
        if self.results and messagebox.askyesno("Clear", "Remove all results?"):
            self.results = []
            self.dataset_colors = {}
            self.color_index = 0
            self.update_plot()
            self.status_label.config(text="Cleared", fg="gray")
    
    def export_results(self):
        """Export results"""
        if not self.results:
            messagebox.showwarning("No Data", "Run experiments first.")
            return
        
        save_path = filedialog.asksaveasfilename(
            title="Export",
            initialfile="qkd_results",
            defaultextension=".csv",
            filetypes=[("CSV data", "*.csv"), ("PNG image", "*.png")]
        )
        
        if save_path:
            try:
                if save_path.endswith('.csv'):
                    with open(save_path, "w", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=list(self.results[0].keys()))
                        writer.writeheader()
                        writer.writerows(self.results)
                    messagebox.showinfo("Exported", f"Data saved to:\n{save_path}")
                else:
                    self.fig.savefig(save_path, dpi=300, bbox_inches="tight")
                    messagebox.showinfo("Exported", f"Plot saved to:\n{save_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = UltimateQKDGUI(root)
    root.mainloop()