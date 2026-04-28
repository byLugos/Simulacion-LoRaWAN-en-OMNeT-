import os
import shutil
from tkinter import (Tk, Label, Button, filedialog, messagebox,
                     IntVar, OptionMenu, Frame, StringVar)
from PIL import Image

# Variables de módulo
_sf_elegido  = 7
_cr_elegido  = 4
_freq_elegida = 915  # MHz

def load_input_files():
    global _sf_elegido, _cr_elegido, _freq_elegida

    root = Tk()
    root.title("Configuración de Simulación")
    root.resizable(False, False)

    excel_path = [None]
    image_info = [None]
    data_dir   = os.path.join(os.getcwd(), "data")
    os.makedirs(data_dir, exist_ok=True)

    sf_var          = IntVar(value=7)
    cr_var          = IntVar(value=4)
    freq_var        = IntVar(value=915)
    excel_label_var = StringVar(value="Sin seleccionar")
    image_label_var = StringVar(value="Sin seleccionar")

    BG     = "#FFFFFF"
    FG     = "#000000"
    BTN_BG = "#E0E0E0"
    BTN_OK = "#D6D6D6"
    FONT   = ("Arial", 9)
    FONT_B = ("Arial", 10, "bold")
    FONT_S = ("Arial", 8)

    root.configure(bg=BG)

    def make_section(title):
        Label(root, text=title, font=FONT_B,
              bg=BG, fg=FG).pack(anchor="w", padx=20, pady=(10, 2))

    def make_separator():
        Label(root, text="\u2500" * 50, bg=BG, fg="#B0B0B0",
              font=("Arial", 7)).pack()

    Label(root, text="Simulación LoRa",
          font=("Arial", 11, "bold"), bg=BG, fg=FG).pack(pady=(14, 4))
    make_separator()

    # === Archivos ===
    make_section("  Archivos de entrada")
    f_files = Frame(root, bg=BG)
    f_files.pack(padx=20, fill="x")

    def load_excel():
        path = filedialog.askopenfilename(
            title="Seleccionar Excel",
            filetypes=[("Excel files", "*.xlsx")]
        )
        if path:
            dest = os.path.join(data_dir, "Resultados.xlsx")
            shutil.copy(path, dest)
            excel_path[0] = dest
            name = os.path.basename(path)
            excel_label_var.set(name if len(name) < 34 else "..." + name[-30:])

    def load_image():
        path = filedialog.askopenfilename(
            title="Seleccionar imagen de la mina",
            filetypes=[("Imagenes", "*.jpg *.png")]
        )
        if path:
            img  = Image.open(path)
            ext  = os.path.splitext(path)[1]
            dest = os.path.join(data_dir, "mina" + ext)
            shutil.copy(path, dest)
            image_info[0] = {
                "path": dest, "width": img.width, "height": img.height
            }
            name = os.path.basename(path)
            image_label_var.set(name if len(name) < 34 else "..." + name[-30:])

    row_e = Frame(f_files, bg=BG)
    row_e.pack(fill="x", pady=3)
    Button(row_e, text="Excel (.xlsx)", command=load_excel,
           bg=BTN_BG, fg=FG, font=FONT, width=14,
           relief="solid", cursor="hand2").pack(side="left")
    Label(row_e, textvariable=excel_label_var,
          bg=BG, fg="#555555", font=FONT_S).pack(side="left", padx=8)

    row_i = Frame(f_files, bg=BG)
    row_i.pack(fill="x", pady=3)
    Button(row_i, text="Imagen mina", command=load_image,
           bg=BTN_BG, fg=FG, font=FONT, width=14,
           relief="solid", cursor="hand2").pack(side="left")
    Label(row_i, textvariable=image_label_var,
          bg=BG, fg="#555555", font=FONT_S).pack(side="left", padx=8)

    make_separator()

    # === Parámetros LoRa ===
    make_section("  Parametros LoRa")
    f_lora = Frame(root, bg=BG)
    f_lora.pack(padx=20, pady=4, fill="x")

    # SF
    Label(f_lora, text="Spreading Factor (SF):", bg=BG, fg=FG,
          font=FONT).grid(row=0, column=0, sticky="w", pady=4)
    om_sf = OptionMenu(f_lora, sf_var, 7, 8, 9, 10, 11, 12)
    om_sf.config(bg="#F5F5F5", fg=FG, font=FONT,
                 activebackground="#EAEAEA", relief="solid", width=6)
    om_sf["menu"].config(bg="#FFFFFF", fg=FG)
    om_sf.grid(row=0, column=1, padx=12, sticky="w")
    Label(f_lora, text="SF7=mayor velocidad   SF12=mayor alcance",
          bg=BG, fg="#666666", font=FONT_S).grid(row=0, column=2, sticky="w")

    # CR
    Label(f_lora, text="Coding Rate (4/x):", bg=BG, fg=FG,
          font=FONT).grid(row=1, column=0, sticky="w", pady=4)
    om_cr = OptionMenu(f_lora, cr_var, 3, 4, 5, 6, 7, 8)
    om_cr.config(bg="#F5F5F5", fg=FG, font=FONT,
                 activebackground="#EAEAEA", relief="solid", width=6)
    om_cr["menu"].config(bg="#FFFFFF", fg=FG)
    om_cr.grid(row=1, column=1, padx=12, sticky="w")
    Label(f_lora, text="4/4=sin redundancia   4/8=maxima proteccion",
          bg=BG, fg="#666666", font=FONT_S).grid(row=1, column=2, sticky="w")

    # Frecuencia
    Label(f_lora, text="Frecuencia (MHz):", bg=BG, fg=FG,
          font=FONT).grid(row=2, column=0, sticky="w", pady=4)
    om_freq = OptionMenu(f_lora, freq_var, 433, 868, 915)
    om_freq.config(bg="#F5F5F5", fg=FG, font=FONT,
                   activebackground="#EAEAEA", relief="solid", width=6)
    om_freq["menu"].config(bg="#FFFFFF", fg=FG)
    om_freq.grid(row=2, column=1, padx=12, sticky="w")
    Label(f_lora, text="433=Asia/Latam   868=Europa   915=Americas",
          bg=BG, fg="#666666", font=FONT_S).grid(row=2, column=2, sticky="w")

    make_separator()

    # === Confirmar ===
    def confirmar():
        if not excel_path[0]:
            messagebox.showerror("Error", "Debes cargar el archivo Excel.")
            return
        if not image_info[0]:
            messagebox.showerror("Error", "Debes cargar la imagen de la mina.")
            return

        global _sf_elegido, _cr_elegido, _freq_elegida
        _sf_elegido   = sf_var.get()
        _cr_elegido   = cr_var.get()
        _freq_elegida = freq_var.get()
        root.destroy()

    Button(root, text="  Iniciar Simulacion  ",
           command=confirmar, bg=BTN_OK, fg=FG,
           font=("Arial", 10, "bold"), relief="solid",
           cursor="hand2").pack(pady=14)

    root.mainloop()

    if excel_path[0] is None:
        raise SystemExit("Simulacion cancelada.")

    return excel_path[0], image_info[0]


def select_lora_params():
    return _sf_elegido, _cr_elegido, _freq_elegida