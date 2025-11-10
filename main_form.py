import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from kirimoto_gcode import emco_gcode_from_kirimoto_gcode

class MainForm:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Formateador de GCode para CNC Emco")
        self.root.geometry("600x500")
        
        # Variables
        self.file_path = tk.StringVar()
        self.spindle_speed = tk.StringVar(value="1000")
        self.feed_rate = tk.StringVar(value="100")
        self.unit_system = tk.StringVar(value="mm")
        self.subprograms = tk.BooleanVar(value=False)
        self.source_gcode = tk.StringVar(value="Fusion 360")
        
        self.create_widgets()
    
    def create_widgets(self):
        # Marco principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="Formateador de GCode para CNC Emco", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Selección de archivo
        ttk.Label(main_frame, text="Archivo GCode:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        file_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(file_frame, textvariable=self.file_path).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(file_frame, text="Seleccionar", command=self.select_file).grid(row=0, column=1, padx=(5, 0))
        
        # Velocidades
        ttk.Label(main_frame, text="Velocidad husillo (S):").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.spindle_speed, width=15).grid(row=2, column=1, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text="RPM").grid(row=2, column=2, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="Velocidad avance (F):").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.feed_rate, width=15).grid(row=3, column=1, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text="mm/min o in/min").grid(row=3, column=2, sticky=tk.W, pady=5)
        
        # Sistema de unidades
        ttk.Label(main_frame, text="Sistema de unidades:").grid(row=4, column=0, sticky=tk.W, pady=5)
        
        unit_frame = ttk.Frame(main_frame)
        unit_frame.grid(row=4, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(unit_frame, text="Milímetros (G71)", 
                       variable=self.unit_system, value="mm").grid(row=0, column=0, sticky=tk.W)
        ttk.Radiobutton(unit_frame, text="Pulgadas (G70)", 
                       variable=self.unit_system, value="inches").grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        
        # Checkbox para subprogramas
        ttk.Checkbutton(main_frame, text="Crear subprogramas", 
                       variable=self.subprograms).grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=10)
        
        # Combobox para fuente GCode
        ttk.Label(main_frame, text="Fuente GCode:").grid(row=6, column=0, sticky=tk.W, pady=5)
        
        source_combo = ttk.Combobox(main_frame, textvariable=self.source_gcode, 
                                   state="readonly", width=20)
        source_combo['values'] = ('Fusion 360', 'Mastercam', 'Aspire', 'Kiri:Moto', 'Otro')
        source_combo.grid(row=6, column=1, sticky=tk.W, pady=5)
        
        # Botón de formateo
        ttk.Button(main_frame, text="Iniciar Formateo de GCode", 
                  command=self.format_gcode, style="Accent.TButton").grid(row=7, column=0, columnspan=3, pady=20)
        
        # Área de información
        info_label = ttk.Label(main_frame, text="Información del proceso:", 
                              font=("Arial", 10, "bold"))
        info_label.grid(row=8, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        
        self.info_text = tk.Text(main_frame, height=8, width=60, state=tk.DISABLED)
        self.info_text.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Barra de desplazamiento para el área de texto
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        scrollbar.grid(row=9, column=3, sticky=(tk.N, tk.S))
        self.info_text.configure(yscrollcommand=scrollbar.set)
    
    def select_file(self):
        filetypes = (
            ('Archivos GCode', '*.nc *.txt *.gcode *.cnc'),
            ('Todos los archivos', '*.*')
        )
        
        filename = filedialog.askopenfilename(
            title='Seleccionar archivo GCode',
            filetypes=filetypes
        )
        
        if filename:
            self.file_path.set(filename)
            self.add_info(f"Archivo seleccionado: {os.path.basename(filename)}")
    
    def add_info(self, message):
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, message + "\n")
        self.info_text.see(tk.END)
        self.info_text.config(state=tk.DISABLED)
    
    def format_gcode(self):
        # Validaciones
        if not self.file_path.get():
            messagebox.showerror("Error", "Por favor selecciona un archivo GCode")
            return
        
        if not os.path.exists(self.file_path.get()):
            messagebox.showerror("Error", "El archivo seleccionado no existe")
            return
        
        try:
            spindle_speed = int(self.spindle_speed.get())
            feed_rate = float(self.feed_rate.get())
        except ValueError:
            messagebox.showerror("Error", "Las velocidades deben ser valores numéricos")
            return
        
        # Mostrar parámetros seleccionados
        self.add_info("=" * 50)
        self.add_info("INICIANDO FORMATEO DE GCODE")
        self.add_info(f"Archivo: {os.path.basename(self.file_path.get())}")
        self.add_info(f"Velocidad husillo: {spindle_speed} RPM")
        self.add_info(f"Velocidad avance: {feed_rate}")
        self.add_info(f"Sistema: {self.unit_system.get()}")
        self.add_info(f"Subprogramas: {'Sí' if self.subprograms.get() else 'No'}")
        self.add_info(f"Fuente: {self.source_gcode.get()}")
        
        # Aquí llamarías a tu función de formateo
        self.process_gcode_file()
    
    def process_gcode_file(self):
        """
        Esta función procesará el archivo GCode según los parámetros seleccionados.
        Debes implementar aquí tu lógica de formateo.
        """
        try:
            # Ejemplo de procesamiento - reemplaza con tu lógica real
            input_file = self.file_path.get()
            output_file = self.generate_output_filename(input_file)
            
            # Simulación de procesamiento
            self.add_info("Procesando archivo...")
            
            # Aquí iría tu lógica de formateo real
            # Por ejemplo:
            # formatted_gcode = self.format_gcode_logic(input_file)
            # self.save_formatted_gcode(output_file, formatted_gcode)

            if (self.source_gcode.get() == "Kiri:Moto"):
                emco_gcode_from_kirimoto_gcode(input_file, output_file, int(self.spindle_speed.get()), int(self.feed_rate.get()), self.unit_system.get())
            
            self.add_info(f"Archivo formateado guardado como: {output_file}")
            self.add_info("Formateo completado exitosamente!")
            
        except Exception as e:
            self.add_info(f"Error durante el formateo: {str(e)}")
            messagebox.showerror("Error", f"Ocurrió un error: {str(e)}")
    
    def generate_output_filename(self, input_file):
        """Genera el nombre del archivo de salida"""
        base_name = os.path.splitext(input_file)[0]
        return f"{base_name}_FOR_EMCO.SPF"
    
    def launch(self):
        self.root.mainloop()