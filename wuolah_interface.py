import tkinter as tk
from tkinter import filedialog, messagebox
import os

from wuolah_ads_remover import main  # Asegúrate de que este archivo esté en el mismo directorio


# Función para seleccionar el archivo de entrada
def select_input_file():
    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if file_path:
        input_file_var.set(file_path)


# Función para seleccionar la carpeta de salida
def select_output_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        output_folder_var.set(folder_path)


# Función principal para ejecutar el procesamiento PDF
def process_pdf():
    input_path = input_file_var.get()
    output_folder = output_folder_var.get()

    if not input_path or not os.path.isfile(input_path):
        messagebox.showerror("Error", "Por favor selecciona un archivo PDF válido de entrada.")
        return
    if not output_folder or not os.path.isdir(output_folder):
        messagebox.showerror("Error", "Por favor selecciona una carpeta de salida válida.")
        return

    # Generar el nombre del archivo de salida basado en el nombre del archivo de entrada
    input_filename = os.path.basename(input_path)
    output_filename = os.path.splitext(input_filename)[0] + "_sin_publicidad.pdf"
    output_path = os.path.join(output_folder, output_filename)

    try:
        main(input_path, output_path)
        messagebox.showinfo("Éxito", f"El PDF ha sido procesado y guardado en {output_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Ha ocurrido un error durante el procesamiento: {e}")


# Configuración de la ventana de tkinter
root = tk.Tk()
root.title("Wuolah pdf cleaner 1.0")
root.geometry("500x250")  # Ampliación de la ventana

# Variables de entrada y salida
input_file_var = tk.StringVar()
output_folder_var = tk.StringVar()

# Widgets de la interfaz
tk.Label(root, text="Archivo PDF de entrada:").pack(pady=5)
tk.Entry(root, textvariable=input_file_var, width=50).pack(pady=5)
tk.Button(root, text="Seleccionar archivo", command=select_input_file).pack(pady=5)

tk.Label(root, text="Carpeta de salida:").pack(pady=5)
tk.Entry(root, textvariable=output_folder_var, width=50).pack(pady=5)
tk.Button(root, text="Seleccionar carpeta", command=select_output_folder).pack(pady=5)

tk.Button(root, text="Procesar PDF", command=process_pdf, bg="blue", fg="white").pack(pady=20)

# Ejecutar la aplicación de tkinter
root.mainloop()
