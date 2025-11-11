from tkinter import *
from tkinter import filedialog, messagebox
import random
import datetime
import operator
from typing import Dict, List, Tuple

# ==============================================================
# 🌟 CONFIGURATION & CONSTANTS 🌟
# ==============================================================

MENU_CATEGORIES = {
    'food': {
        'items': ['Ramen', 'Salmon', 'Giyosas', 'Sushi', 'Hanbaga', 'Mochi', 'Onigiri', 'Curry'],
        'prices': [1.32, 1.65, 2.31, 3.22, 1.22, 1.99, 2.05, 2.65],
        'display_name': 'Food'
    },
    'drinks': {
        'items': ['Water', 'Soda', 'Juice', 'Beer', 'Wine', 'Lemonade', 'Soft Drink', 'Chicha'],
        'prices': [0.25, 0.99, 1.21, 1.54, 1.08, 1.10, 2.00, 1.58],
        'display_name': 'Drinks'
    },
    'desserts': {
        'items': ['Ice Cream', 'Fruit', 'Brownies', 'Flan', 'Mousse', 'Tiramisu', 'Cheesecake', 'Cupcake'],
        'prices': [1.54, 1.68, 1.32, 1.97, 2.55, 2.14, 1.94, 1.74],
        'display_name': 'Desserts'
    }
}

TAX_RATE = 0.07
WINDOW_TITLE = "Resutoranto - POS System"
WINDOW_BG = '#FFFFFF'
ACCENT_COLOR = '#0066CC'
LIGHT_GRAY = '#EAEAEA'
DARK_GRAY = '#333333'

# ==============================================================
# 🌟 SAFE CALCULATOR CLASS (Elimina eval()) 🌟
# ==============================================================

class Calculator:
    """Calculadora segura sin eval()"""
    
    OPERATORS = {
        '+': operator.add,
        '-': operator.sub,
        'x': operator.mul,
        '*': operator.mul,
        '/': operator.truediv,
    }

    @staticmethod
    def calculate(expression: str) -> str:
        """Evalúa expresiones matemáticas de forma segura"""
        try:
            # Dividir por operadores
            for op_char, op_func in Calculator.OPERATORS.items():
                if op_char in expression:
                    parts = expression.split(op_char)
                    if len(parts) == 2:
                        left = float(parts[0].strip())
                        right = float(parts[1].strip())
                        result = op_func(left, right)
                        return f"{result:.2f}"
            
            # Si no hay operador, retornar el número
            return f"{float(expression):.2f}"
        
        except ZeroDivisionError:
            return "Zero Division Error"
        except (ValueError, AttributeError):
            return "Syntax Error"

# ==============================================================
# 🌟 CLASS DEFINITIONS (POO CORE) 🌟
# ==============================================================

class RestaurantApp(Tk):
    def __init__(self):
        # 1. NON-TKINTER VARIABLES (SAFE TO DECLARE HERE)
        self.operator_buffer = ''
        self.menu_data = MENU_CATEGORIES
        
        # Diccionarios para almacenar variables por categoría (MEJOR ESTRUCTURA)
        self.category_data: Dict[str, Dict] = {}
        self.menu_panels: Dict[str, Frame] = {}
        self.cost_vars: Dict[str, StringVar] = {}
        
        # --- 2. CREATE THE ROOT WINDOW (PASO CRÍTICO DE TKINTER) ---
        super().__init__() 

        # --- 3. TKINTER VARIABLES (Declaradas AHORA, después de super().__init__()) ---
        self._initialize_variables()
        
        # WIDGET REFERENCES
        self.receipt_text_area = None
        self.calculator_display = None
        self.cost_frame = None
        self.right_frame = None
        self.main_body_frame = None 

        # --- 4. START GUI CONSTRUCTION ---
        self.configure_window()
        self.create_panels()
        self.create_menu_frames() 
        self.create_menu_items() 
        self.create_cost_section() 
        self.create_receipt_and_calculator()

    # ==============================================================
    # --- INITIALIZATION & CONFIGURATION ---
    # ==============================================================

    def _initialize_variables(self):
        """Inicializa todas las variables Tkinter de forma centralizada"""
        # Crear diccionarios para cada categoría con sus variables
        for category_key, category_info in self.menu_data.items():
            self.category_data[category_key] = {
                'check_vars': [],
                'quantity_vars': [],
                'entries': [],
                'items': category_info['items'],
                'prices': category_info['prices'],
                'display_name': category_info['display_name']
            }
        
        # Variables para costos
        self.cost_vars = {
            'food': StringVar(),
            'drinks': StringVar(),
            'desserts': StringVar(),
            'subtotal': StringVar(),
            'tax': StringVar(),
            'total': StringVar()
        }

    # ==============================================================
    # --- CALCULATOR LOGIC & CORE BUSINESS LOGIC ---
    # ==============================================================

    def click_button(self, number: str):
        """Añade número/operador al buffer del calculador"""
        self.operator_buffer += number
        self.calculator_display.delete(0, END)
        self.calculator_display.insert(END, self.operator_buffer)

    def clear_calculator(self):
        """Limpia el calculador"""
        self.operator_buffer = ''
        self.calculator_display.delete(0, END)

    def get_result(self):
        """Calcula el resultado de forma SEGURA (sin eval)"""
        result = Calculator.calculate(self.operator_buffer)
        self.calculator_display.delete(0, END)
        self.calculator_display.insert(0, result)
        self.operator_buffer = ''

    def check_input_status(self):
        """Habilita/Deshabilita campos de entrada basado en estado de checkbox"""
        for category_key in self.category_data:
            self._update_category_entries(category_key)

    def _update_category_entries(self, category_key: str):
        """Actualiza el estado de las entradas para una categoría específica"""
        cat_data = self.category_data[category_key]
        for i in range(len(cat_data['check_vars'])):
            if cat_data['check_vars'][i].get() == 1:
                cat_data['entries'][i].config(state=NORMAL)
                if cat_data['quantity_vars'][i].get() == '0':
                    cat_data['quantity_vars'][i].set('')
                cat_data['entries'][i].focus()
            else:
                cat_data['entries'][i].config(state=DISABLED)
                cat_data['quantity_vars'][i].set('0')

    def _validate_quantity(self, value: str) -> float:
        """Valida y convierte cantidad a float, retorna 0 si es inválido"""
        try:
            amount = float(value) if value else 0
            return max(0, amount)  # No permitir números negativos
        except ValueError:
            return 0

    def calculate_total(self):
        """Calcula todos los subtotales, impuestos y total general"""
        totals = {}
        grand_subtotal = 0

        # Calcular subtotal para cada categoría
        for category_key, cat_data in self.category_data.items():
            subtotal = 0
            for i in range(len(cat_data['items'])):
                amount = self._validate_quantity(cat_data['quantity_vars'][i].get())
                subtotal += amount * cat_data['prices'][i]
            
            totals[category_key] = subtotal
            grand_subtotal += subtotal

        # Calcular impuesto y total
        tax = grand_subtotal * TAX_RATE
        grand_total = grand_subtotal + tax

        # Actualizar variables de costo
        self.cost_vars['food'].set(f'${totals.get("food", 0):.2f}')
        self.cost_vars['drinks'].set(f'${totals.get("drinks", 0):.2f}')
        self.cost_vars['desserts'].set(f'${totals.get("desserts", 0):.2f}')
        self.cost_vars['subtotal'].set(f'${grand_subtotal:.2f}')
        self.cost_vars['tax'].set(f'${tax:.2f}')
        self.cost_vars['total'].set(f'${grand_total:.2f}')

    def generate_receipt(self):
        """Genera y muestra el recibo final con alineación profesional"""
        self.receipt_text_area.delete(1.0, END)
        receipt_number = f'N# - {random.randint(1000, 9999)}'
        receipt_date = datetime.datetime.now().strftime('%d/%m/%Y - %H:%M:%S')
        
        # Encabezado del recibo
        self.receipt_text_area.insert(END, f'Data: {receipt_number:<20} {receipt_date}\n')
        self.receipt_text_area.insert(END, f'=' * 54 + '\n')
        self.receipt_text_area.insert(END, f'{"Item":<20} {"QTY":<10} {"Cost":>10}\n')
        self.receipt_text_area.insert(END, f'-' * 54 + '\n')

        # Insertar items
        for category_key, cat_data in self.category_data.items():
            for i in range(len(cat_data['items'])):
                amount_str = cat_data['quantity_vars'][i].get()
                if amount_str and amount_str != '0':
                    try:
                        amount = float(amount_str)
                        item_cost = amount * cat_data['prices'][i]
                        self.receipt_text_area.insert(END, 
                            f'{cat_data["items"][i]:<20}{amount_str:<10}${item_cost:.2f}\n')
                    except ValueError:
                        pass

        # Resumen de costos
        self.receipt_text_area.insert(END, f'-' * 54 + '\n')
        self.receipt_text_area.insert(END, f'Cost of Food: \t\t\t\t{self.cost_vars["food"].get()}\n')
        self.receipt_text_area.insert(END, f'Cost of Drinks: \t\t\t\t{self.cost_vars["drinks"].get()}\n')
        self.receipt_text_area.insert(END, f'Cost of Desserts: \t\t\t{self.cost_vars["desserts"].get()}\n')
        self.receipt_text_area.insert(END, f'-' * 54 + '\n')
        self.receipt_text_area.insert(END, f'Subtotal: \t\t\t\t{self.cost_vars["subtotal"].get()}\n')
        self.receipt_text_area.insert(END, f'Tax ({TAX_RATE*100:.0f}%): \t\t\t\t{self.cost_vars["tax"].get()}\n')
        self.receipt_text_area.insert(END, f'Total: \t\t\t\t{self.cost_vars["total"].get()}\n')
        self.receipt_text_area.insert(END, f'-' * 54 + '\n')
        self.receipt_text_area.insert(END, f'Please come again')

    def save_receipt(self):
        """Abre diálogo para guardar el recibo"""
        receipt_content = self.receipt_text_area.get(1.0, END)
        if not receipt_content.strip():
            messagebox.showwarning('Warning', 'Receipt is empty!')
            return

        file = filedialog.asksaveasfile(mode='w', defaultextension='.txt')
        if file:
            file.write(receipt_content)
            file.close()
            messagebox.showinfo('Information', 'File saved successfully')

    def reset_all(self):
        """Reinicia todos los campos, checkboxes y variables de costo"""
        self.receipt_text_area.delete(1.0, END)
        
        for category_key, cat_data in self.category_data.items():
            for i in range(len(cat_data['items'])):
                cat_data['quantity_vars'][i].set('0')
                cat_data['entries'][i].config(state=DISABLED)
                cat_data['check_vars'][i].set(0)

        for key in self.cost_vars:
            self.cost_vars[key].set('')
    
    def configure_window(self):
        """Sets up window geometry, title, and background color (PROFESSIONAL STYLE)."""
        self.state('zoomed') # Inicia maximizada
        self.title("Resutoranto - POS System")
        self.config(bg='#FFFFFF') 

    def create_panels(self):
        """Sets up the main panel structure (Top, Main Body, and Right Side)."""
        
        # --- TOP PANEL (Title) ---
        self.top_panel = Frame(self, bd=1, relief='flat', bg='#FFFFFF')
        self.top_panel.pack(side='top', fill=X)

        Label(self.top_panel,
              text="Restaurant Point of Sale System",
              fg="#0066CC", 
              font=("Arial Bold", 32),
              bg="#FFFFFF",
              width=30).grid(row=0, column=0, pady=10)

        # --- MAIN BODY FRAME (Usando GRID para la distribución ESTABLE) ---
        self.main_body_frame = Frame(self, bg='#FFFFFF')
        self.main_body_frame.pack(fill=BOTH, expand=True) 
        
        # Asignar pesos para expansión (3 columnas de menú, 1 columna para recibo/calc)
        self.main_body_frame.grid_columnconfigure(0, weight=1)
        self.main_body_frame.grid_columnconfigure(1, weight=1)
        self.main_body_frame.grid_columnconfigure(2, weight=1)
        self.main_body_frame.grid_columnconfigure(3, weight=1)

    def create_menu_frames(self):
        """Configura las secciones de menú (Food, Drinks, Desserts) en Fila 0"""
        frame_options = {
            'font': ("Dosis Bold", 14), 
            'bd': 1, 
            'relief': 'groove', 
            'fg': DARK_GRAY, 
            'bg': LIGHT_GRAY,
            'padx': 5, 'pady': 5 
        }

        col_index = 0
        for category_key, category_info in self.menu_data.items():
            panel = LabelFrame(self.main_body_frame, 
                             text=category_info['display_name'], 
                             **frame_options)
            panel.grid(row=0, column=col_index, sticky='nsew', padx=10, pady=10)
            self.menu_panels[category_key] = panel
            col_index += 1

        # Marco de Resumen de Costos (debajo de menús, abarcando 3 columnas)
        self.cost_frame = LabelFrame(self.main_body_frame, text="Cost Summary", 
                                    font=("Dosis Bold", 14), bd=1, relief='groove', 
                                    fg=DARK_GRAY, bg=WINDOW_BG)
        self.cost_frame.grid(row=1, column=0, columnspan=3, sticky='ew', padx=10, pady=10)

        # Marco Derecho (Columna 3 para Recibo y Calculadora)
        self.right_frame = Frame(self.main_body_frame, bg=WINDOW_BG)
        self.right_frame.grid(row=0, column=3, rowspan=2, sticky='nsew', padx=10, pady=10)

    def create_menu_items(self):
        """Genera todos los Checkbuttons, Etiquetas de Precio y Campos de Entrada"""
        for category_key, panel in self.menu_panels.items():
            self._create_items_section(category_key, panel)

    def _create_items_section(self, category_key: str, parent_panel: Frame):
        """Crea una sección de items para una categoría específica"""
        cat_data = self.category_data[category_key]
        menu_list = cat_data['items']
        prices_list = cat_data['prices']
        display_name = cat_data['display_name']

        # Encabezado de sección
        Label(parent_panel, text=display_name, font=('Dosis Bold', 16), 
              fg=ACCENT_COLOR, bg=LIGHT_GRAY).grid(row=0, columnspan=3, pady=(0, 10))

        # Encabezados de columna
        Label(parent_panel, text="Item", font=('Dosis Bold', 12), 
              fg=DARK_GRAY, bg=LIGHT_GRAY).grid(row=1, column=0, sticky=W)
        Label(parent_panel, text="Price", font=('Dosis Bold', 12), 
              fg=ACCENT_COLOR, bg=LIGHT_GRAY).grid(row=1, column=1, padx=10)
        Label(parent_panel, text="Qty", font=('Dosis Bold', 12), 
              fg=DARK_GRAY, bg=LIGHT_GRAY).grid(row=1, column=2, padx=5)

        # Crear items
        for i, item in enumerate(menu_list):
            row_index = i + 2
            
            # Variables
            check_var = IntVar()
            qty_var = StringVar(value='0')
            
            cat_data['check_vars'].append(check_var)
            cat_data['quantity_vars'].append(qty_var)
            
            # Checkbutton
            Checkbutton(parent_panel, text=item.title(), font=('Dosis', 12), 
                       variable=check_var, command=self.check_input_status,
                       bg=WINDOW_BG, fg=DARK_GRAY, 
                       selectcolor=ACCENT_COLOR).grid(row=row_index, column=0, sticky=W, padx=5, pady=2)

            # Etiqueta de Precio
            Label(parent_panel, text=f'${prices_list[i]:.2f}', font=('Dosis', 12), 
                 fg=ACCENT_COLOR, bg=WINDOW_BG).grid(row=row_index, column=1, sticky=W, padx=10, pady=2)

            # Campo de Entrada (Cantidad)
            entry_widget = Entry(parent_panel, font=('Dosis bold', 12), bd=1, width=4, 
                                state="disabled", textvariable=qty_var, bg='white', fg='black')
            entry_widget.grid(row=row_index, column=2, padx=5, pady=2)
            cat_data['entries'].append(entry_widget)

    def create_cost_section(self):
        """Crea la sección de resumen de costos usando GRID"""
        cost_labels = [
            ('Food Cost', 'food'), 
            ('Drink Cost', 'drinks'), 
            ('Dessert Cost', 'desserts'), 
            ('Subtotal', 'subtotal'), 
            (f'Tax ({TAX_RATE*100:.0f}%)', 'tax'), 
            ('Total', 'total')
        ]

        row_index = 1
        col_index = 0
        
        for label_text, var_key in cost_labels:
            # Etiqueta
            Label(self.cost_frame, text=label_text, font=('Dosis', 12), 
                 bg=WINDOW_BG, fg=DARK_GRAY, anchor=W).grid(row=row_index, column=col_index, 
                 sticky=W, padx=10, pady=2)
            
            # Campo de entrada (solo lectura)
            Entry(self.cost_frame, font=('Dosis', 12), bd=1, width=15, state="readonly", 
                 textvariable=self.cost_vars[var_key], bg=LIGHT_GRAY, 
                 fg=DARK_GRAY).grid(row=row_index, column=col_index + 1, padx=10, pady=2, sticky=W)
            
            if col_index == 0:
                col_index += 2
            else:
                col_index = 0
                row_index += 1

    def create_receipt_and_calculator(self):
        """Crea el recibo, calculadora y botones de control (Columna 3)"""
        self.calc_receipt_frame = Frame(self.right_frame, bg=WINDOW_BG)
        self.calc_receipt_frame.pack(fill=BOTH, expand=True)

        # Calculadora
        self.calculator_panel = Frame(self.calc_receipt_frame, bd=1, relief='solid', 
                                     bg=LIGHT_GRAY, padx=5, pady=5)
        self.calculator_panel.pack(side='top', padx=10, pady=10, fill=X)

        self.calculator_display = Entry(self.calculator_panel, font=('Dosis', 16), bd=1, 
                                       width=20, bg=WINDOW_BG, fg=DARK_GRAY)
        self.calculator_display.grid(row=0, columnspan=4, padx=5, pady=5)

        # Botones de calculadora
        calculator_buttons = ['7', '8', '9', '+', '4', '5', '6', '-', '1', '2', '3', 'x', 
                            'C', '/', '0', '=']
        row = 1
        col = 0
        
        for button_text in calculator_buttons:
            if button_text == 'C':
                cmd = self.clear_calculator
            elif button_text == '=':
                cmd = self.get_result
            else:
                cmd = lambda t=button_text: self.click_button(t)

            Button(self.calculator_panel, text=button_text.title(), font=('Dosis', 12),
                  fg='white', bg=ACCENT_COLOR, bd=1, width=5, 
                  command=cmd).grid(row=row, column=col, padx=3, pady=3)

            col += 1
            if col == 4:
                col = 0
                row += 1

        # Área de Recibo
        self.receipt_panel = Frame(self.calc_receipt_frame, bd=1, relief='groove', bg=WINDOW_BG)
        self.receipt_panel.pack(side='left', fill=BOTH, expand=True, padx=10, pady=10)

        self.receipt_text_area = Text(self.receipt_panel, font=('Dosis', 12), bd=1, 
                                     width=40, height=15, bg=WINDOW_BG, fg=DARK_GRAY)
        self.receipt_text_area.pack(fill=BOTH, expand=True)

        # Botones Principales
        self.buttons_panel = Frame(self.right_frame, bd=1, relief='flat', bg=WINDOW_BG)
        self.buttons_panel.pack(side='bottom', fill=X, padx=10, pady=5)

        buttons_config = [
            ('Total', self.calculate_total), 
            ('Receipt', self.generate_receipt), 
            ('Save', self.save_receipt), 
            ('Reset', self.reset_all)
        ]

        for col, (name, command) in enumerate(buttons_config):
            Button(self.buttons_panel, text=name.title(), font=('Dosis', 12),
                  fg='white', bg=ACCENT_COLOR, bd=1, width=9,
                  command=command).grid(row=0, column=col, padx=5, pady=5)


# ==============================================================
# -------------------- FINAL EXECUTION BLOCK -------------------
# ==============================================================

if __name__ == "__main__":
    app = RestaurantApp()
    app.mainloop()