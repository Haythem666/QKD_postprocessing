"""
QKD Configuration GUI - Compact Version with Scrollbar

This GUI modifies the configuration in process_large_file.py and launches it.
Works on small screens by using a scrollbar.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys


class QKDConfigGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("QKD Post-Processing")
        
        # SMALLER WINDOW SIZE for small screens
        self.root.geometry("650x550")
        self.root.resizable(True, True)  # Allow resizing
        
        # Available datasets
        self.datasets = [
            "raw_data/parsed_qkd_data_partial_100k.csv",
            "raw_data/parsed_qkd_data_partial_1M.csv",
            "raw_data/parsed_qkd_data_partial_10M.csv",
            "raw_data/parsed_qkd_data.csv",
        ]
        
        # Variables
        self.file_path = tk.StringVar(value=self.datasets[-1])  # Default to full dataset
        self.chunk_size = tk.IntVar(value=2_000_000)
        self.algorithm = tk.StringVar(value="yanetal")
        
        self.create_widgets()
    
    def create_widgets(self):
        # Title (fixed at top)
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=50)
        title_frame.pack(fill=tk.X, side=tk.TOP)
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="QKD Post-Processing", 
                font=("Arial", 16, "bold"), fg="white", bg="#2c3e50").pack(pady=12)
        
        # SCROLLABLE AREA
        canvas = tk.Canvas(self.root, bg="#ecf0f1")
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Main frame inside scrollable area
        main_frame = ttk.Frame(scrollable_frame, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ═══════════════════════════════════════════════════════
        # FILE SELECTION
        # ═══════════════════════════════════════════════════════
        file_frame = ttk.LabelFrame(main_frame, text="Dataset", padding="12")
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        for dataset in self.datasets:
            # Extract size info
            if "100k" in dataset:
                size_info = "100K rows (~30s)"
            elif "1M" in dataset:
                size_info = "1M rows (~5min)"
            elif "10M" in dataset:
                size_info = "10M rows (~1h)"
            else:
                size_info = "355M rows (~5h)"
            
            display_name = os.path.basename(dataset).replace('.csv', '').replace('parsed_qkd_data_partial_', '')
            
            rb = ttk.Radiobutton(
                file_frame, 
                text=f"{display_name}\n  → {size_info}", 
                variable=self.file_path, 
                value=dataset
            )
            rb.pack(anchor=tk.W, pady=3)
        
        # ═══════════════════════════════════════════════════════
        # CHUNK SIZE
        # ═══════════════════════════════════════════════════════
        chunk_frame = ttk.LabelFrame(main_frame, text="Chunk Size", padding="12")
        chunk_frame.pack(fill=tk.X, pady=(0, 10))
        
        chunk_options = [
            ("100k (300MB RAM)", 100_000),
            ("500K (1GB RAM)", 500_000),
            ("1M (2GB RAM)", 1_000_000),
            ("2M (3GB RAM) ", 2_000_000),
            ("5M (6GB RAM)", 5_000_000)
        ]
        
        for text, value in chunk_options:
            rb = ttk.Radiobutton(chunk_frame, text=text, variable=self.chunk_size, value=value)
            rb.pack(anchor=tk.W, pady=3)
        
        # ═══════════════════════════════════════════════════════
        # CASCADE ALGORITHM
        # ═══════════════════════════════════════════════════════
        algo_frame = ttk.LabelFrame(main_frame, text="Algorithm", padding="12")
        algo_frame.pack(fill=tk.X, pady=(0, 10))
        
        algo_options = [
            ("original", "Original (4 passes)"),
            ("yanetal", "Yanetal (10 passes) "),
            ("option7", "Option7 (14 passes)"),
            ("option8", "Option8 (best efficiency)")
        ]
        
        for value, text in algo_options:
            ttk.Radiobutton(algo_frame, text=text, variable=self.algorithm, 
                           value=value).pack(anchor=tk.W, pady=3)
        
        # ═══════════════════════════════════════════════════════
        # START BUTTON (ALWAYS VISIBLE AT BOTTOM)
        # ═══════════════════════════════════════════════════════
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 10))
        
        start_btn = tk.Button(
            button_frame, 
            text="▶️  START PROCESSING", 
            command=self.start_processing,
            font=("Arial", 12, "bold"),
            bg="#27ae60", 
            fg="white",
            activebackground="#229954",
            activeforeground="white",
            padx=30, 
            pady=12,
            cursor="hand2",
            relief=tk.RAISED,
            bd=2
        )
        start_btn.pack()
        
        # Info label
        info_label = tk.Label(
            main_frame,
            text="💡 The processing will run in a separate terminal window",
            font=("Arial", 8),
            fg="gray"
        )
        info_label.pack(pady=(5, 0))
    
    def start_processing(self):
        # Check if file exists
        if not os.path.exists(self.file_path.get()):
            messagebox.showerror("Error", f"File not found:\n{self.file_path.get()}")
            return
        
        # Confirm
        dataset_name = os.path.basename(self.file_path.get())
        
        config_text = f"""Ready to start:

📁 {dataset_name}
📦 Chunk: {self.chunk_size.get():,} rows
⚙️ Algorithm: {self.algorithm.get()}

Processing will start in a new terminal.
This window will close.

Continue?"""
        
        if not messagebox.askyesno("Start Processing?", config_text):
            return
        
        # Modify process_large_file.py
        self.update_process_file()
        
        # Launch processing
        self.launch_processing()
        
        # Close GUI
        messagebox.showinfo("Started!", 
                   "Processing started.\nCheck your terminal output.")
        self.root.quit()
    
    def update_process_file(self):
        """Modify process_large_file.py with selected configuration"""
        
        try:
            # Read current file
            with open("process_large_file.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            # Replace configuration values
            lines = content.split('\n')
            new_lines = []
            
            for line in lines:
                if line.strip().startswith('CHUNK_SIZE ='):
                    new_lines.append(f'CHUNK_SIZE = {self.chunk_size.get()}  # Modified by GUI')
                elif line.strip().startswith('CASCADE_ALGORITHM ='):
                    new_lines.append(f'CASCADE_ALGORITHM = \'{self.algorithm.get()}\'  # Modified by GUI')
                elif line.strip().startswith('LARGE_FILE ='):
                    new_lines.append(f'    LARGE_FILE = "{self.file_path.get()}"  # Modified by GUI')
                else:
                    new_lines.append(line)
            
            # Write back
            with open("process_large_file.py", "w", encoding="utf-8") as f:
                f.write('\n'.join(new_lines))
            
            print(f"   Configuration updated:")
            print(f"   Dataset: {self.file_path.get()}")
            print(f"   Chunk: {self.chunk_size.get():,}")
            print(f"   Algorithm: {self.algorithm.get()}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not update config:\n{e}")
            raise
    
    def launch_processing(self):
        """Launch process_large_file.py with the current Python interpreter"""
        
        try:
            if sys.platform == "win32":
                venv_python = os.path.join(os.getcwd(), ".venv", "Scripts", "python.exe")
            else:
                venv_python = os.path.join(os.getcwd(), ".venv", "bin", "python")

            python_executable = venv_python if os.path.exists(venv_python) else (sys.executable or "python")
            subprocess.Popen(
                [python_executable, "process_large_file.py"],
                cwd=os.getcwd()
            )
        except Exception as e:
            messagebox.showerror("Error", f"Could not launch processing:\n{e}")



if __name__ == "__main__":
    root = tk.Tk()
    app = QKDConfigGUI(root)
    
    # Bind mousewheel to scroll
    def on_mousewheel(event):
        canvas = root.winfo_children()[1]  # Get canvas
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    root.bind_all("<MouseWheel>", on_mousewheel)  # Windows/Mac
    root.bind_all("<Button-4>", lambda e: root.winfo_children()[1].yview_scroll(-1, "units"))  # Linux up
    root.bind_all("<Button-5>", lambda e: root.winfo_children()[1].yview_scroll(1, "units"))   # Linux down
    
    root.mainloop()