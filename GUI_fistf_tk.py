import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import threading
import subprocess
import os
import shutil
import sys
import time
from datetime import datetime
import math

# =====================================================
#  CONFIGURAZIONE TEMA
# =====================================================
class Colors:
    PRIMARY = "#2C3E50"      # Blu scuro
    SECONDARY = "#3498DB"     # Blu chiaro
    ACCENT = "#E74C3C"        # Rosso
    SUCCESS = "#27AE60"       # Verde
    WARNING = "#F39C12"       # Arancione
    BACKGROUND = "#1A2634"    # Grigio molto scuro
    SURFACE = "#2C3E50"       # Superfici
    TEXT = "#ECF0F1"          # Testo chiaro
    TEXT_SECONDARY = "#BDC3C7" # Testo secondario
    BORDER = "#34495E"        # Bordi
    HOVER = "#3498DB"         # Hover

# =====================================================
#  WIDGET PERSONALIZZATI
# =====================================================
class ModernButton(tk.Canvas):
    """Bottone moderno con effetti hover e animazioni"""
    def __init__(self, master, text, command=None, bg=Colors.SECONDARY, 
                 fg=Colors.TEXT, width=200, height=40, corner_radius=10, state='normal', **kwargs):
        super().__init__(master, width=width, height=height, 
                        bg=master["bg"], highlightthickness=0, **kwargs)
        
        self.command = command
        self.text = text
        self.bg = bg
        self.fg = fg
        self.width = width
        self.height = height
        self.corner_radius = corner_radius
        self.is_hovered = False
        self.is_pressed = False
        self.state = state
        
        # Crea il bottone
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)
        
        self.draw_button(bg)
        
    def draw_button(self, color):
        """Disegna il bottone"""
        self.delete("all")
        
        # Sfondo con angoli arrotondati
        self.create_rounded_rect(0, 0, self.width, self.height, 
                                 self.corner_radius, fill=color, outline="")
        
        # Testo
        self.create_text(self.width//2, self.height//2, text=self.text, 
                        fill=self.fg, font=("Segoe UI", 10, "bold"))
        
    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        """Crea un rettangolo con angoli arrotondati"""
        points = []
        # In senso orario partendo dall'alto a sinistra
        points = [x1 + radius, y1,
                  x2 - radius, y1,
                  x2, y1,
                  x2, y1 + radius,
                  x2, y2 - radius,
                  x2, y2,
                  x2 - radius, y2,
                  x1 + radius, y2,
                  x1, y2,
                  x1, y2 - radius,
                  x1, y1 + radius,
                  x1, y1]
        
        self.create_polygon(points, smooth=True, **kwargs)
        
    def on_enter(self, event):
        """Mouse entra nel bottone"""
        if self.state != 'disabled' and not self.is_hovered:
            self.is_hovered = True
            self.animate_color(self.bg, Colors.HOVER)
            
    def on_leave(self, event):
        """Mouse esce dal bottone"""
        if self.state != 'disabled' and self.is_hovered:
            self.is_hovered = False
            self.animate_color(Colors.HOVER, self.bg)
            
    def on_press(self, event):
        """Click sul bottone"""
        if self.state != 'disabled':
            self.is_pressed = True
            self.animate_color(self.bg, Colors.ACCENT, speed=50)
        
    def on_release(self, event):
        """Rilascio del click"""
        if self.state != 'disabled' and self.is_pressed:
            self.is_pressed = False
            self.animate_color(Colors.ACCENT, Colors.HOVER if self.is_hovered else self.bg)
            if self.command:
                self.command()
                
    def animate_color(self, from_color, to_color, steps=10, speed=20):
        """Animazione cambio colore"""
        def interpolate(c1, c2, step):
            # Converte colori esadecimali in RGB
            r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
            r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
            
            r = int(r1 + (r2 - r1) * step / steps)
            g = int(g1 + (g2 - g1) * step / steps)
            b = int(b1 + (b2 - b1) * step / steps)
            
            return f"#{r:02x}{g:02x}{b:02x}"
        
        def animate_step(step=0):
            if step <= steps:
                color = interpolate(from_color, to_color, step)
                self.draw_button(color)
                self.after(speed, lambda: animate_step(step + 1))
        
        animate_step()
        
    def config(self, **kwargs):
        """Configura il bottone"""
        if 'state' in kwargs:
            self.state = kwargs['state']
            if self.state == 'disabled':
                self.draw_button(Colors.BORDER)
            else:
                self.draw_button(self.bg)
        return super().config(**kwargs)

class ModernEntry(tk.Frame):
    """Campo di input moderno"""
    def __init__(self, master, label="", **kwargs):
        super().__init__(master, bg=master["bg"])
        
        self.label = tk.Label(self, text=label, bg=master["bg"], 
                              fg=Colors.TEXT_SECONDARY, font=("Segoe UI", 9))
        self.label.pack(anchor="w", pady=(0, 2))
        
        # Frame per bordo
        self.border = tk.Frame(self, bg=Colors.BORDER, bd=0)
        self.border.pack(fill="x", ipady=2)
        
        self.entry = tk.Entry(self.border, bg=Colors.SURFACE, fg=Colors.TEXT,
                               font=("Segoe UI", 10), bd=0, **kwargs)
        self.entry.pack(fill="x", padx=1, pady=1, ipady=5)
        
        self.entry.bind("<FocusIn>", self.on_focus_in)
        self.entry.bind("<FocusOut>", self.on_focus_out)
        
    def on_focus_in(self, event):
        self.border.config(bg=Colors.SECONDARY)
        
    def on_focus_out(self, event):
        self.border.config(bg=Colors.BORDER)
        
    def get(self):
        return self.entry.get()
        
    def insert(self, index, string):
        self.entry.insert(index, string)
        
    def delete(self, first, last=None):
        self.entry.delete(first, last)

class ModernCheckbutton(tk.Frame):
    """Checkbox moderna"""
    def __init__(self, master, text="", variable=None, **kwargs):
        super().__init__(master, bg=master["bg"])
        
        if variable is None:
            variable = tk.BooleanVar()
        self.variable = variable
        
        self.checkbox = tk.Canvas(self, width=20, height=20, bg=master["bg"],
                                   highlightthickness=0)
        self.checkbox.pack(side="left", padx=(0, 8))
        
        self.label = tk.Label(self, text=text, bg=master["bg"], fg=Colors.TEXT,
                              font=("Segoe UI", 10), cursor="hand2")
        self.label.pack(side="left")
        
        self.draw_checkbox()
        
        self.checkbox.bind("<Button-1>", self.toggle)
        self.label.bind("<Button-1>", self.toggle)
        
        # Traccia i cambiamenti della variabile
        self.variable.trace_add("write", lambda *args: self.draw_checkbox())
        
    def draw_checkbox(self):
        """Disegna la checkbox"""
        self.checkbox.delete("all")
        
        if self.variable.get():
            # Checkbox selezionata
            self.checkbox.create_rectangle(2, 2, 18, 18, fill=Colors.SECONDARY,
                                           outline=Colors.SECONDARY, width=0)
            self.checkbox.create_line(5, 10, 9, 14, 15, 6, 
                                      fill=Colors.TEXT, width=2, capstyle="round")
        else:
            # Checkbox non selezionata
            self.checkbox.create_rectangle(2, 2, 18, 18, fill=Colors.SURFACE,
                                           outline=Colors.BORDER, width=1)
            
    def toggle(self, event=None):
        """Toggle checkbox"""
        self.variable.set(not self.variable.get())

class ProgressCircle(tk.Canvas):
    """Cerchio di progresso animato"""
    def __init__(self, master, size=100, **kwargs):
        super().__init__(master, width=size, height=size, bg=master["bg"],
                         highlightthickness=0, **kwargs)
        self.size = size
        self.value = 0
        self.draw(0)
        
    def draw(self, value):
        """Disegna il cerchio di progresso"""
        self.delete("all")
        
        center = self.size // 2
        radius = self.size // 2 - 10
        
        # Cerchio di sfondo
        self.create_oval(center - radius, center - radius,
                        center + radius, center + radius,
                        outline=Colors.BORDER, width=3)
        
        if value > 0:
            # Arco di progresso
            extent = value * 360 / 100
            self.create_arc(center - radius, center - radius,
                           center + radius, center + radius,
                           start=90, extent=extent,
                           outline=Colors.SECONDARY, width=4, style="arc")
            
        # Testo percentuale
        self.create_text(center, center, text=f"{int(value)}%",
                        fill=Colors.TEXT, font=("Segoe UI", 12, "bold"))
        
    def set_value(self, value):
        """Imposta il valore di progresso"""
        self.value = value
        self.draw(value)

# =====================================================
#  CLASSE PRINCIPALE
# =====================================================
class FistfGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FISTF Tournament Manager")
        self.root.geometry("900x750")
        self.root.configure(bg=Colors.BACKGROUND)
        
        # Variabili
        self.input_file = None
        self.output_folder = None
        self.output_filename = tk.StringVar(value="FISTF_Tournament_Maker")
        self.engine_loaded = False
        self.processing = False
        
        # Stile ttk
        self.setup_styles()
        
        # Setup UI
        self.setup_ui()
        
        # Carica motore
        self.root.after(100, self.load_engine)
        
        # Centra la finestra
        self.center_window()
        
    def center_window(self):
        """Centra la finestra sullo schermo"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def setup_styles(self):
        """Configura gli stili ttk"""
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configura colori per ttk
        style.configure("TLabel", background=Colors.BACKGROUND, foreground=Colors.TEXT)
        style.configure("TFrame", background=Colors.BACKGROUND)
        style.configure("TLabelframe", background=Colors.BACKGROUND, foreground=Colors.TEXT)
        style.configure("TLabelframe.Label", background=Colors.BACKGROUND, foreground=Colors.TEXT)
        style.configure("TProgressbar", background=Colors.SECONDARY, troughcolor=Colors.BORDER)
        
        # Separatore
        style.configure("TSeparator", background=Colors.BORDER)
        
    def create_card(self, parent, title):
        """Crea una card con titolo"""
        card = tk.Frame(parent, bg=Colors.SURFACE, bd=0)
        card.pack(fill="x", pady=10, padx=20)
        
        # Titolo card
        title_label = tk.Label(card, text=title, bg=Colors.SURFACE, fg=Colors.TEXT,
                               font=("Segoe UI", 12, "bold"))
        title_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        # Separatore
        sep = tk.Frame(card, bg=Colors.BORDER, height=1)
        sep.pack(fill="x", padx=15, pady=(0, 10))
        
        # Content frame
        content = tk.Frame(card, bg=Colors.SURFACE)
        content.pack(fill="x", padx=15, pady=(0, 15))
        
        return content
        
    def setup_ui(self):
        """Setup dell'interfaccia"""
        
        # Header con gradiente
        self.create_header()
        
        # Main content con scroll
        self.create_main_content()
        
        # Footer
        self.create_footer()
        
    def create_header(self):
        """Crea l'header con logo e titolo"""
        header = tk.Frame(self.root, bg=Colors.PRIMARY, height=120)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Logo e titolo in orizzontale
        content = tk.Frame(header, bg=Colors.PRIMARY)
        content.pack(expand=True, fill="both", padx=30)
        
        # Logo
        try:
            img = Image.open(resource_path("logo.png"))
            img = img.resize((80, 80), Image.Resampling.LANCZOS)
            self.logo = ImageTk.PhotoImage(img)
            
            logo_frame = tk.Frame(content, bg=Colors.PRIMARY)
            logo_frame.pack(side="left", padx=(0, 20))
            
            tk.Label(logo_frame, image=self.logo, bg=Colors.PRIMARY).pack()
        except:
            # Fallback: icona testo
            logo_frame = tk.Frame(content, bg=Colors.PRIMARY)
            logo_frame.pack(side="left", padx=(0, 20))
            
            tk.Label(logo_frame, text="🏆", font=("Segoe UI", 40), 
                    bg=Colors.PRIMARY, fg=Colors.TEXT).pack()
        
        # Titolo e sottotitolo
        title_frame = tk.Frame(content, bg=Colors.PRIMARY)
        title_frame.pack(side="left", fill="both", expand=True)
        
        tk.Label(title_frame, text="FISTF Tournament Manager", 
                font=("Segoe UI", 24, "bold"), bg=Colors.PRIMARY, fg=Colors.TEXT).pack(anchor="w")
        
        tk.Label(title_frame, text=f"Versione 2.0 Elegante - {datetime.now().strftime('%d/%m/%Y')}", 
                font=("Segoe UI", 10), bg=Colors.PRIMARY, fg=Colors.TEXT_SECONDARY).pack(anchor="w")
        
    def create_main_content(self):
        """Crea il contenuto principale con scroll"""
        
        # Canvas per scroll
        canvas = tk.Canvas(self.root, bg=Colors.BACKGROUND, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        
        # Frame interno
        self.main_frame = tk.Frame(canvas, bg=Colors.BACKGROUND)
        self.main_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Abilita scroll con mousewheel
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # ==================== CARDS ====================
        
        # Card Input File
        input_card = self.create_card(self.main_frame, "📂 File Input")
        
        self.input_label = tk.Label(input_card, text="Nessun file selezionato", 
                                    bg=Colors.SURFACE, fg=Colors.TEXT_SECONDARY,
                                    font=("Segoe UI", 10), relief="flat")
        self.input_label.pack(fill="x", pady=(0, 10))
        
        # Pulsanti input
        btn_frame = tk.Frame(input_card, bg=Colors.SURFACE)
        btn_frame.pack()
        
        ModernButton(btn_frame, text="📂 Seleziona file", 
                    command=self.select_input, bg=Colors.SECONDARY,
                    width=140, height=35).pack(side="left", padx=5)
        
        ModernButton(btn_frame, text="📋 Usa esempio", 
                    command=self.use_example, bg=Colors.SUCCESS,
                    width=140, height=35).pack(side="left", padx=5)
        
        # Card Output Folder
        output_card = self.create_card(self.main_frame, "📁 Cartella Output")
        
        self.output_label = tk.Label(output_card, 
                                     text="Stessa cartella del file input (default)", 
                                     bg=Colors.SURFACE, fg=Colors.TEXT_SECONDARY,
                                     font=("Segoe UI", 10))
        self.output_label.pack(fill="x", pady=(0, 10))
        
        ModernButton(output_card, text="📁 Seleziona cartella", 
                    command=self.select_output, bg=Colors.SECONDARY,
                    width=200, height=35).pack()
        
        # Card Nome File
        name_card = self.create_card(self.main_frame, "📝 Nome file output")
        
        self.name_entry = ModernEntry(name_card, label="Nome file (senza estensione)")
        self.name_entry.pack(fill="x", pady=(0, 10))
        self.name_entry.insert(0, "FISTF_Tournament_Maker")
        
        # Suggerimenti
        hint_frame = tk.Frame(name_card, bg=Colors.SURFACE)
        hint_frame.pack()
        
        ModernButton(hint_frame, text="📅 Data corrente", 
                    command=self.insert_current_date, bg=Colors.SECONDARY,
                    width=120, height=30).pack(side="left", padx=5)
        
        ModernButton(hint_frame, text="🏆 Torneo", 
                    command=lambda: self.insert_text("Torneo"), bg=Colors.SECONDARY,
                    width=120, height=30).pack(side="left", padx=5)
        
        # Card Opzioni
        opt_card = self.create_card(self.main_frame, "⚙️ Opzioni")
        
        self.var_placeholders = tk.BooleanVar(value=True)
        ModernCheckbutton(opt_card, text="Inserisci placeholder per categorie vuote",
                         variable=self.var_placeholders).pack(anchor="w", pady=5)
        
        self.var_open_output = tk.BooleanVar(value=True)
        ModernCheckbutton(opt_card, text="Apri file generato automaticamente",
                         variable=self.var_open_output).pack(anchor="w", pady=5)
        
        # Card Progresso
        progress_card = self.create_card(self.main_frame, "🎯 Progresso")
        
        # Progress circle
        progress_frame = tk.Frame(progress_card, bg=Colors.SURFACE)
        progress_frame.pack(pady=10)
        
        self.progress_circle = ProgressCircle(progress_frame, size=80)
        self.progress_circle.pack()
        
        # Progress bar classica
        self.progress = ttk.Progressbar(progress_card, mode='determinate', 
                                        length=400, style="TProgressbar")
        self.progress.pack(fill="x", pady=10)
        
        # Card Log
        log_card = self.create_card(self.main_frame, "📋 Log Operazioni")
        
        # Log area con stile
        log_frame = tk.Frame(log_card, bg=Colors.BACKGROUND, bd=1, relief="flat")
        log_frame.pack(fill="both", expand=True)
        
        self.log_text = tk.Text(log_frame, height=8, wrap='word',
                                bg=Colors.BACKGROUND, fg=Colors.TEXT,
                                font=("Consolas", 9), bd=0)
        self.log_text.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Bottone Genera
        button_frame = tk.Frame(self.main_frame, bg=Colors.BACKGROUND)
        button_frame.pack(pady=20)
        
        self.run_btn = ModernButton(button_frame, text="🎲 GENERA TORNEO", 
                                    command=self.run_process, bg=Colors.SUCCESS,
                                    width=300, height=50)
        self.run_btn.pack()
        self.run_btn.config(state='disabled')
        
    def create_footer(self):
        """Crea il footer con status"""
        footer = tk.Frame(self.root, bg=Colors.PRIMARY, height=30)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        
        self.status = tk.Label(footer, text="✅ Pronto", bg=Colors.PRIMARY, 
                               fg=Colors.TEXT, font=("Segoe UI", 9))
        self.status.pack(side="left", padx=15)
        
        # Versione
        tk.Label(footer, text="FISTF Tournament Manager v2.0 Elegante", 
                bg=Colors.PRIMARY, fg=Colors.TEXT_SECONDARY,
                font=("Segoe UI", 8)).pack(side="right", padx=15)
        
    def log(self, msg):
        """Aggiunge messaggio al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert('end', f"[{timestamp}] {msg}\n")
        self.log_text.see('end')
        self.root.update()
        
    def insert_text(self, text):
        """Inserisce testo nel campo nome file"""
        current = self.name_entry.get()
        if current == "FISTF_Tournament_Maker" or not current:
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, text)
        else:
            self.name_entry.insert(tk.END, f"_{text}")
            
    def insert_current_date(self):
        """Inserisce la data corrente"""
        date_str = datetime.now().strftime("%d_%m_%Y")
        current = self.name_entry.get()
        if current == "FISTF_Tournament_Maker" or not current:
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, date_str)
        else:
            self.name_entry.insert(tk.END, f"_{date_str}")
            
    def load_engine(self):
        """Carica il motore"""
        self.log("🔄 Caricamento motore...")
        if import_engine():
            self.engine_loaded = True
            self.run_btn.config(state='normal')
            self.log("✅ Motore caricato correttamente")
        else:
            self.log("❌ ERRORE: Impossibile caricare il motore!")
            
    def select_input(self):
        """Seleziona file input"""
        file = filedialog.askopenfilename(
            title="Seleziona Categorie.xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if file:
            self.input_file = file
            self.input_label.config(text=os.path.basename(file))
            
            if not self.output_folder:
                self.output_folder = os.path.dirname(file)
                self.output_label.config(text=self.output_folder)
                
            self.log(f"✅ File input: {file}")
            self.preview_file()
            
    def select_output(self):
        """Seleziona cartella output"""
        folder = filedialog.askdirectory(title="Seleziona cartella output")
        if folder:
            self.output_folder = folder
            self.output_label.config(text=folder)
            self.log(f"📁 Cartella output: {folder}")
            
    def use_example(self):
        """Usa file di esempio"""
        example = resource_path("Categorie_ESEMPIO.xlsx")
        if os.path.exists(example):
            self.input_file = example
            self.input_label.config(text="Categorie_ESEMPIO.xlsx (file incluso)")
            self.output_folder = os.path.dirname(example)
            self.output_label.config(text=self.output_folder)
            self.log("📋 Usando file di esempio")
            self.preview_file()
            
    def preview_file(self):
        """Analizza il file selezionato"""
        try:
            import pandas as pd
            xl = pd.ExcelFile(self.input_file)
            sheets = xl.sheet_names
            self.log(f"📊 Fogli trovati: {', '.join(sheets)}")
        except Exception as e:
            self.log(f"⚠️ Errore lettura file: {e}")
            
    def run_process(self):
        """Avvia generazione"""
        if not self.engine_loaded:
            messagebox.showerror("Errore", "Motore non caricato")
            return
        if not self.input_file:
            messagebox.showerror("Errore", "Seleziona un file input")
            return
        if self.processing:
            return
            
        filename = self.name_entry.get().strip()
        if not filename:
            filename = "FISTF_Tournament_Maker"
        
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
            
        final_filename = f"{filename}.xlsx"
        
        self.processing = True
        self.run_btn.config(state='disabled')
        self.progress['value'] = 0
        self.progress_circle.set_value(0)
        
        self.log("="*50)
        self.log("🚀 AVVIO GENERAZIONE TORNEO")
        self.log(f"📂 Input: {self.input_file}")
        self.log(f"📁 Output: {self.output_folder or 'Default'}")
        self.log(f"📝 File: {final_filename}")
        
        thread = threading.Thread(target=self._process_thread, args=(final_filename,))
        thread.daemon = True
        thread.start()
        
    def _process_thread(self, output_filename):
        """Processo in thread"""
        try:
            self.root.after(0, lambda: self.update_progress(10, "📂 Verifica file..."))
            
            if not os.path.exists(self.input_file):
                raise Exception(f"File non trovato: {self.input_file}")
            
            # Prepara ambiente
            if getattr(sys, 'frozen', False):
                work_dir = os.path.dirname(sys.executable)
            else:
                work_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Imposta variabili d'ambiente
            os.environ['FISTF_CATEGORIE_PATH'] = self.input_file
            os.environ['FISTF_PLACEHOLDER_MODE'] = str(self.var_placeholders.get())
            
            if self.output_folder:
                final_output_path = os.path.join(self.output_folder, output_filename)
            else:
                final_output_path = os.path.join(work_dir, output_filename)
            
            os.environ['FISTF_OUTPUT_PATH'] = final_output_path
            
            self.root.after(0, lambda: self.update_progress(30, "⚙️ Generazione in corso..."))
            
            # Esegui motore
            original_dir = os.getcwd()
            os.chdir(work_dir)
            
            try:
                generated_file = engine.run_v4d_full_export()
                self.root.after(0, lambda: self.log(f"✅ File generato: {generated_file}"))
            finally:
                os.chdir(original_dir)
            
            self.root.after(0, lambda: self.update_progress(90, "✅ Completato!"))
            
            # Apri file
            if self.var_open_output.get() and os.path.exists(final_output_path):
                try:
                    subprocess.Popen([final_output_path], shell=True)
                    self.root.after(0, lambda: self.log("📂 File aperto"))
                except Exception as e:
                    self.root.after(0, lambda e=e: self.log(f"⚠️ Errore apertura: {e}"))
            
            self.root.after(0, lambda: self.progress.config(value=100))
            self.root.after(0, lambda: self.progress_circle.set_value(100))
            self.root.after(0, lambda: self.log("🎉 GENERAZIONE COMPLETATA!"))
            
            # Animazione successo
            self.root.after(0, self.flash_success)
            
            # Messaggio di successo
            self.root.after(0, lambda f=output_filename, p=final_output_path: messagebox.showinfo(
                "Successo", 
                f"Torneo generato correttamente!\n\nFile: {f}\n\nSalvato in: {os.path.dirname(p)}"
            ))
            
        except PermissionError:
            self.root.after(0, lambda: self.log("❌ File bloccato da Excel!"))
            self.root.after(0, lambda: messagebox.showerror(
                "File bloccato", 
                "Chiudi Excel e riprova."
            ))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.log(f"❌ ERRORE: {msg}"))
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("Errore", msg))
            
        finally:
            self.processing = False
            self.root.after(0, lambda: self.run_btn.config(state='normal'))
            self.root.after(0, lambda: self.status.config(text="✅ Pronto"))
            
    def flash_success(self):
        """Animazione di successo"""
        def flash(count=0):
            if count < 3:
                color = Colors.SUCCESS if count % 2 == 0 else Colors.BACKGROUND
                self.main_frame.config(bg=color)
                self.root.after(200, lambda: flash(count + 1))
            else:
                self.main_frame.config(bg=Colors.BACKGROUND)
                
        flash()
            
    def update_progress(self, value, message):
        """Aggiorna progresso"""
        self.progress['value'] = value
        self.progress_circle.set_value(value)
        self.status.config(text=message)
        self.log(message)

# =====================================================
#  FUNZIONI DI SUPPORTO
# =====================================================
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# =====================================================
#  IMPORTA MOTORE
# =====================================================
def import_engine():
    """Importa il motore di generazione del torneo"""
    global engine
    try:
        # Prova prima con l'import normale
        import Torneo_FISTF_v4d_FINAL_FIXED as engine
        # Verifica che la funzione esista
        if hasattr(engine, 'run_v4d_full_export'):
            print("✅ Motore caricato con funzione run_v4d_full_export")
            return True
        else:
            print("❌ Il modulo non ha la funzione run_v4d_full_export")
            return False
    except ImportError as e:
        print(f"❌ Errore import motore: {e}")
        
        # Prova percorsi alternativi
        try:
            import sys
            import os
            
            # Aggiungi la directory corrente al path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            
            # Prova a importare di nuovo
            import Torneo_FISTF_v4d_FINAL_FIXED as engine
            if hasattr(engine, 'run_v4d_full_export'):
                print("✅ Motore caricato (secondo tentativo)")
                return True
        except ImportError:
            pass
            
        return False

# =====================================================
#  MAIN
# =====================================================
if __name__ == "__main__":
    app = FistfGUI()
    app.root.mainloop()