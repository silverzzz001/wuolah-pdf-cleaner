import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import requests
import time
import re
import webbrowser
import threading
from wuolah_ads_remover import main
from version import VERSION  # Importar la versión local desde version.py


# Obtener la versión desde GitHub sin caché y extraer VERSION de version.py
def get_github_version():
    try:
        # Agregar un parámetro de tiempo a la URL para evitar caché
        url = f"https://raw.githubusercontent.com/silverzzz001/wuolah-pdf-cleaner/refs/heads/main/version.py?t={int(time.time() * 1000)}"
        response = requests.get(url)
        response.raise_for_status()  # Verificar si la solicitud fue exitosa

        # Extraer la versión usando una expresión regular
        match = re.search(r'VERSION\s*=\s*"(.+?)"', response.text)
        if match:
            return match.group(1)
        else:
            print("No se pudo encontrar la versión en el archivo version.py de GitHub.")
            return None
    except requests.RequestException as e:
        print(f"Error al comprobar la versión en GitHub: {e}")
        return None


# Comprobar si hay una nueva versión (se ejecuta en un hilo separado)
def check_for_updates():
    github_version = get_github_version()
    download_url = "https://github.com/silverzzz001/wuolah-pdf-cleaner/releases"

    if github_version and github_version > VERSION:
        if messagebox.askyesno(
                "Nueva versión disponible",
                f"Hay una nueva versión ({github_version}) disponible.\n"
                "¿Quieres abrir el enlace de descarga?\n"
        ):
            webbrowser.open(download_url)
    else:
        print("Estás usando la versión más reciente.")


# Llamar a check_for_updates en un hilo separado
def start_update_check():
    threading.Thread(target=check_for_updates).start()


# Configuración de la ventana de tkinter
root = tk.Tk()
root.title(f"Wuolah PDF Cleaner {VERSION}")
#icon_image = tk.PhotoImage(file="logo.png")  # Reemplaza "icon.png" con la ruta de tu icono
#root.iconphoto(False, icon_image)
root.geometry("500x300")

# Llama a la función de verificación de actualizaciones al iniciar el programa en segundo plano
root.after(100, start_update_check)

# Variables de entrada y salida
input_file_var = tk.StringVar()
output_folder_var = tk.StringVar()
input_folder_var = tk.StringVar()


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


# Función para seleccionar la carpeta de entrada para procesar todos los PDFs
def select_input_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        input_folder_var.set(folder_path)


# Función principal para procesar un único PDF
def process_single_pdf():
    input_path = input_file_var.get()
    output_folder = output_folder_var.get()

    if not input_path or not os.path.isfile(input_path):
        messagebox.showerror("Error", "Por favor selecciona un archivo PDF válido de entrada.")
        return
    if not output_folder or not os.path.isdir(output_folder):
        messagebox.showerror("Error", "Por favor selecciona una carpeta de salida válida.")
        return

    output_filename = os.path.splitext(os.path.basename(input_path))[0] + "_sin_publicidad.pdf"
    output_path = os.path.join(output_folder, output_filename)

    try:
        main(input_path, output_path)
        messagebox.showinfo("Éxito", f"El PDF ha sido procesado y guardado en {output_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Ha ocurrido un error durante el procesamiento: {e}")


# Función para procesar todos los archivos PDF en una carpeta
def process_all_pdfs():
    input_folder = input_folder_var.get()
    output_folder = output_folder_var.get()

    if not input_folder or not os.path.isdir(input_folder):
        messagebox.showerror("Error", "Por favor selecciona una carpeta válida de entrada.")
        return
    if not output_folder or not os.path.isdir(output_folder):
        messagebox.showerror("Error", "Por favor selecciona una carpeta de salida válida.")
        return

    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')]
    if not pdf_files:
        messagebox.showwarning("Aviso", "No se encontraron archivos PDF en la carpeta seleccionada.")
        return

    for pdf_file in pdf_files:
        input_path = os.path.join(input_folder, pdf_file)
        output_filename = os.path.splitext(pdf_file)[0] + "_sin_publicidad.pdf"
        output_path = os.path.join(output_folder, output_filename)

        try:
            main(input_path, output_path)
            print(f"Procesado {pdf_file} y guardado en {output_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar {pdf_file}: {e}")

    messagebox.showinfo("Éxito", f"Todos los archivos PDF han sido procesados y guardados en {output_folder}")


# Crear el widget de pestañas
notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

# Pestaña para procesar un único PDF
single_pdf_frame = ttk.Frame(notebook)
notebook.add(single_pdf_frame, text="Procesar PDF único")

tk.Label(single_pdf_frame, text="Archivo PDF de entrada:").pack(pady=5)
tk.Entry(single_pdf_frame, textvariable=input_file_var, width=50).pack(pady=5)
tk.Button(single_pdf_frame, text="Seleccionar archivo", command=select_input_file).pack(pady=5)

tk.Label(single_pdf_frame, text="Carpeta de salida:").pack(pady=5)
tk.Entry(single_pdf_frame, textvariable=output_folder_var, width=50).pack(pady=5)
tk.Button(single_pdf_frame, text="Seleccionar carpeta", command=select_output_folder).pack(pady=5)

tk.Button(single_pdf_frame, text="Procesar PDF", command=process_single_pdf, bg="blue", fg="white").pack(pady=20)

# Pestaña para procesar todos los PDFs de una carpeta
batch_pdf_frame = ttk.Frame(notebook)
notebook.add(batch_pdf_frame, text="Procesar todos los PDFs de una carpeta")

tk.Label(batch_pdf_frame, text="Carpeta de entrada con archivos PDF:").pack(pady=5)
tk.Entry(batch_pdf_frame, textvariable=input_folder_var, width=50).pack(pady=5)
tk.Button(batch_pdf_frame, text="Seleccionar carpeta", command=select_input_folder).pack(pady=5)

tk.Label(batch_pdf_frame, text="Carpeta de salida:").pack(pady=5)
tk.Entry(batch_pdf_frame, textvariable=output_folder_var, width=50).pack(pady=5)
tk.Button(batch_pdf_frame, text="Seleccionar carpeta", command=select_output_folder).pack(pady=5)

tk.Button(batch_pdf_frame, text="Procesar todos los PDFs", command=process_all_pdfs, bg="green", fg="white").pack(
    pady=20)

# Ejecutar la aplicación de tkinter
root.mainloop()
