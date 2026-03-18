"""
QKD Configuration GUI with Interactive Plotting
Allows running experiments and visualizing results in real-time
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


class QKDPlotterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("QKD Post-Processing - Interactive Analysis")
        self.root.geometry("1200x700")
        
        # Data storage
        self.results = []  # List of dicts: {dataset, chunk, algo, efficiency, ...}
        
        # Color mapping for datasets (based on file size)
        self.dataset_colors = {}
        self.color_palette = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
        self.color_index = 0
        
        # Marker mapping for algorithms
        self.algo_markers = {
            'original': 'o',
            'yanetal': 's',
            'option7': '^',
            'option8': 'D'
        }
        
        # Variables
        self.file_path = tk.StringVar(value="")
        self.chunk_size = tk.IntVar(value=2_000_000)
        self.algorithm = tk.StringVar(value="yanetal")
        
        self.create_widgets()
    
    def create_widgets(self):
        # ═══════════════════════════════════════════════════════
        # MAIN LAYOUT: LEFT (Config) | RIGHT (Plot)
        # ═══════════════════════════════════════════════════════
        
        # Left panel (Configuration)
        left_panel = tk.Frame(self.root, width=400, bg="#ecf0f1")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10)
        left_panel.pack_propagate(False)
        
        # Right panel (Plot)
        right_panel = tk.Frame(self.root, bg="white")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ═══════════════════════════════════════════════════════
        # LEFT PANEL - CONFIGURATION
        # ═══════════════════════════════════════════════════════
        
        # Title
        title = tk.Label(left_panel, text="Configuration", 
                        font=("Arial", 16, "bold"), bg="#ecf0f1")
        title.pack(pady=(10, 20))
        
        # File Selection
        file_frame = ttk.LabelFrame(left_panel, text="Dataset File", padding="10")
        file_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        self.file_label = tk.Label(file_frame, text="No file selected", 
                                   fg="gray", wraplength=350, justify=tk.LEFT)
        self.file_label.pack(pady=(0, 10))
        
        browse_btn = tk.Button(file_frame, text="Browse File", 
                              command=self.browse_file,
                              bg="#3498db", fg="white", 
                              font=("Arial", 10, "bold"),
                              cursor="hand2", padx=15, pady=8)
        browse_btn.pack()
        
        # Chunk Size
        chunk_frame = ttk.LabelFrame(left_panel, text="Chunk Size", padding="10")
        chunk_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        chunk_options = [
            ("50K", 50_000),
            ("100K", 100_000),
            ("200K", 200_000),
            ("500K", 500_000),
            ("1M", 1_000_000),
            ("2M", 2_000_000),
            ("5M", 5_000_000)
        ]
        
        for text, value in chunk_options:
            rb = ttk.Radiobutton(chunk_frame, text=text, 
                                variable=self.chunk_size, value=value)
            rb.pack(anchor=tk.W, pady=2)
        
        # Algorithm
        algo_frame = ttk.LabelFrame(left_panel, text="Algorithm", padding="10")
        algo_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        algo_options = [
            ("original", "Original (○)"),
            ("yanetal", "Yanetal (□) - Recommended"),
            ("option7", "Option7 (△)"),
            ("option8", "Option8 (◇)")
        ]
        
        for value, text in algo_options:
            rb = ttk.Radiobutton(algo_frame, text=text, 
                                variable=self.algorithm, value=value)
            rb.pack(anchor=tk.W, pady=2)
        
        # Action Buttons
        button_frame = tk.Frame(left_panel, bg="#ecf0f1")
        button_frame.pack(fill=tk.X, padx=10, pady=(20, 10))
        
        run_btn = tk.Button(button_frame, text="RUN & PLOT", 
                           command=self.run_and_plot,
                           bg="#27ae60", fg="white",
                           font=("Arial", 12, "bold"),
                           cursor="hand2", padx=20, pady=12)
        run_btn.pack(fill=tk.X, pady=(0, 10))
        
        clear_btn = tk.Button(button_frame, text="Clear Plot", 
                             command=self.clear_plot,
                             bg="#e74c3c", fg="white",
                             font=("Arial", 10),
                             cursor="hand2", padx=15, pady=8)
        clear_btn.pack(fill=tk.X)

        export_btn = tk.Button(button_frame, text="Export (PNG/CSV)",
                      command=self.export_results,
                      bg="#2980b9", fg="white",
                      font=("Arial", 10),
                      cursor="hand2", padx=15, pady=8)
        export_btn.pack(fill=tk.X, pady=(10, 0))
        
        # Status Label
        self.status_label = tk.Label(left_panel, text="Ready", 
                                     bg="#ecf0f1", fg="gray",
                                     font=("Arial", 9), wraplength=380)
        self.status_label.pack(side=tk.BOTTOM, pady=10)
        
        # ═══════════════════════════════════════════════════════
        # RIGHT PANEL - PLOT
        # ═══════════════════════════════════════════════════════
        
        plot_title = tk.Label(right_panel, text="Results Visualization", 
                             font=("Arial", 14, "bold"), bg="white")
        plot_title.pack(pady=(0, 10))
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)

        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_panel)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Initial empty plot
        self.update_plot()
    
    def browse_file(self):
        """Open file dialog to select dataset"""
        filename = filedialog.askopenfilename(
            title="Select QKD Dataset",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir="raw_data" if os.path.exists("raw_data") else "."
        )
        
        if filename:
            self.file_path.set(filename)
            display_name = os.path.basename(filename)
            self.file_label.config(text=display_name, fg="black")
    
    def run_and_plot(self):
        """Run processing and add result to plot"""
        
        # Validate
        if not self.file_path.get():
            messagebox.showerror("Error", "Please select a dataset file first!")
            return
        
        if not os.path.exists(self.file_path.get()):
            messagebox.showerror("Error", f"File not found:\n{self.file_path.get()}")
            return
        
        # Confirm
        dataset_name = os.path.basename(self.file_path.get())
        chunk_name = f"{self.chunk_size.get():,}"
        
        confirm_text = f"""Run processing with:

📁 Dataset: {dataset_name}
📦 Chunk: {chunk_name} rows
⚙️ Algorithm: {self.algorithm.get()}

This will take some time depending on dataset size.
Continue?"""
        
        if not messagebox.askyesno("Confirm Run", confirm_text):
            return
        
        # Update status
        self.status_label.config(text=f"Running... (this may take several minutes)", fg="orange")
        self.root.update()
        
        # Run processing
        try:
            result = self.run_processing()
            
            if result:
                # Add to results
                self.results.append(result)
                
                # Update plot
                self.update_plot()
                
                # Update status
                self.status_label.config(
                    text=f"✅ Success! Efficiency: {result['efficiency']:.2f}%", 
                    fg="green"
                )
                
                messagebox.showinfo("Success", 
                    f"Processing completed!\n\n"
                    f"Overall Efficiency: {result['efficiency']:.2f}%\n"
                    f"Final Keys: {result['final_keys']:,} bits\n"
                    f"Time: {result.get('time', 'N/A')}")
            else:
                self.status_label.config(text="Processing failed", fg="red")
                
        except Exception as e:
            messagebox.showerror("Error", f"Processing failed:\n{e}")
            self.status_label.config(text="Error occurred", fg="red")
    
    def run_processing(self):
        """Execute process_large_file.py and parse output"""
        
        # Prepare command
        cmd = [
            sys.executable,
            "process_large_file.py",
            "--data", self.file_path.get(),
            "--chunk", str(self.chunk_size.get()),
            "--algo", self.algorithm.get()
        ]
        
        try:
            # Run subprocess and capture output
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            output = result.stdout + result.stderr
            
            # Parse output for key metrics
            efficiency_match = re.search(r'Overall efficiency:\s+([\d.]+)%', output)
            final_keys_match = re.search(r'Total final keys:\s+([\d,]+)\s+bits', output)
            time_match = re.search(r'Elapsed time:\s+(.+)', output)
            
            if efficiency_match and final_keys_match:
                dataset_name = os.path.basename(self.file_path.get())
                
                # Assign color to dataset if new
                if dataset_name not in self.dataset_colors:
                    self.dataset_colors[dataset_name] = self.color_palette[self.color_index % len(self.color_palette)]
                    self.color_index += 1
                
                return {
                    'dataset': dataset_name,
                    'dataset_path': self.file_path.get(),
                    'chunk': self.chunk_size.get(),
                    'algorithm': self.algorithm.get(),
                    'efficiency': float(efficiency_match.group(1)),
                    'final_keys': int(final_keys_match.group(1).replace(',', '')),
                    'time': time_match.group(1) if time_match else 'N/A',
                    'color': self.dataset_colors[dataset_name],
                    'marker': self.algo_markers[self.algorithm.get()]
                }
            else:
                messagebox.showerror("Parse Error", 
                    "Could not parse results from output.\n"
                    "Make sure process_large_file.py completed successfully.")
                return None
                
        except subprocess.TimeoutExpired:
            messagebox.showerror("Timeout", "Processing took too long (>2 hours)")
            return None
        except Exception as e:
            raise e
    
    def update_plot(self):
        """Redraw the plot with all results"""
        
        self.ax.clear()
        
        if not self.results:
            # Empty plot
            self.ax.text(0.5, 0.5, 'No data yet\nRun experiments to see results', 
                        ha='center', va='center', fontsize=14, color='gray',
                        transform=self.ax.transAxes)
            self.ax.set_xlabel('Chunk Size (rows)', fontsize=12)
            self.ax.set_ylabel('Overall Efficiency (%)', fontsize=12)
            self.ax.set_title('QKD Processing Results', fontsize=14, fontweight='bold')
            self.ax.grid(True, alpha=0.3)
        else:
            # Plot all results
            for result in self.results:
                self.ax.scatter(
                    result['chunk'], 
                    result['efficiency'],
                    c=result['color'],
                    marker=result['marker'],
                    s=150,
                    alpha=0.7,
                    edgecolors='black',
                    linewidths=1.5,
                    label=f"{result['dataset']} - {result['algorithm']}"
                )
            
            # Configure plot
            self.ax.set_xlabel('Chunk Size (rows)', fontsize=12, fontweight='bold')
            self.ax.set_ylabel('Overall Efficiency (%)', fontsize=12, fontweight='bold')
            self.ax.set_title('QKD Processing Results', fontsize=14, fontweight='bold', pad=15)
            self.ax.grid(True, alpha=0.3, linestyle='--')
            
            # Format x-axis (chunk sizes)
            chunk_values = sorted(set(r['chunk'] for r in self.results))
            self.ax.set_xticks(chunk_values)
            self.ax.set_xticklabels([f"{v//1000}K" if v < 1_000_000 else f"{v//1_000_000}M" 
                                    for v in chunk_values])
            
            # Create custom legend
            # Dataset colors
            dataset_handles = [
                mpatches.Patch(color=color, label=dataset) 
                for dataset, color in self.dataset_colors.items()
            ]
            
            # Algorithm markers
            algo_handles = [
                plt.Line2D([0], [0], marker=marker, color='w', 
                          markerfacecolor='gray', markersize=10, 
                          label=f"{algo} ({marker})")
                for algo, marker in self.algo_markers.items()
                if any(r['algorithm'] == algo for r in self.results)
            ]
            
            # Add legends
            if dataset_handles:
                legend1 = self.ax.legend(handles=dataset_handles, 
                                        title="Datasets", 
                                        loc='upper left',
                                        fontsize=9)
                self.ax.add_artist(legend1)
            
            if algo_handles:
                self.ax.legend(handles=algo_handles, 
                              title="Algorithms", 
                              loc='upper right',
                              fontsize=9)
            
            # Add hover annotations (show on plot)
            for result in self.results:
                self.ax.annotate(
                    f"{result['efficiency']:.1f}%",
                    xy=(result['chunk'], result['efficiency']),
                    xytext=(5, 5),
                    textcoords='offset points',
                    fontsize=8,
                    alpha=0.7
                )
        
        if hasattr(self, 'canvas'):
            self.canvas.draw()
    
    def clear_plot(self):
        """Clear all results and reset plot"""
        if not self.results:
            return
        
        if messagebox.askyesno("Clear Plot", "Remove all results from the plot?"):
            self.results = []
            self.dataset_colors = {}
            self.color_index = 0
            self.update_plot()
            self.status_label.config(text="Plot cleared", fg="gray")

    def export_results(self):
        """Export current plot as PNG or plotted data as CSV."""
        if not self.results:
            messagebox.showwarning("No Data", "Run at least one experiment before exporting.")
            return

        save_path = filedialog.asksaveasfilename(
            title="Export Plot/Data",
            initialfile="qkd_results",
            defaultextension=".png",
            filetypes=[
                ("PNG image", "*.png"),
                ("CSV data", "*.csv")
            ]
        )

        if not save_path:
            return

        file_ext = os.path.splitext(save_path)[1].lower()

        try:
            if file_ext == ".csv":
                with open(save_path, "w", newline="", encoding="utf-8") as csv_file:
                    writer = csv.DictWriter(
                        csv_file,
                        fieldnames=[
                            "dataset",
                            "dataset_path",
                            "chunk",
                            "algorithm",
                            "efficiency",
                            "final_keys",
                            "time"
                        ]
                    )
                    writer.writeheader()
                    for result in self.results:
                        writer.writerow({
                            "dataset": result["dataset"],
                            "dataset_path": result["dataset_path"],
                            "chunk": result["chunk"],
                            "algorithm": result["algorithm"],
                            "efficiency": result["efficiency"],
                            "final_keys": result["final_keys"],
                            "time": result["time"]
                        })

                self.status_label.config(text=f"CSV exported: {os.path.basename(save_path)}", fg="green")
                messagebox.showinfo("Export Complete", f"Data exported successfully:\n{save_path}")
            else:
                if file_ext != ".png":
                    save_path = f"{save_path}.png"

                self.fig.savefig(save_path, dpi=300, bbox_inches="tight")
                self.status_label.config(text=f"PNG exported: {os.path.basename(save_path)}", fg="green")
                messagebox.showinfo("Export Complete", f"Plot exported successfully:\n{save_path}")
        except Exception as exc:
            messagebox.showerror("Export Error", f"Failed to export file:\n{exc}")
            self.status_label.config(text="Export failed", fg="red")


if __name__ == "__main__":
    root = tk.Tk()
    app = QKDPlotterGUI(root)
    root.mainloop()