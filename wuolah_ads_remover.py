import fitz  # PyMuPDF
import re  # Biblioteca para expresiones regulares

# Desplazamientos para el ajuste de posicion del contenido
offset_x = -100  # Desplazamiento hacia la izquierda en puntos
offset_y = -100  # Desplazamiento hacia arriba en puntos
scale_adjustment = 1.20  # Ajuste de escala para maximizar el contenido

# Definir tamanios de los banners a eliminar
target_sizes = [(1246, 218), (147, 1538), (217, 1094), (1769, 148)]
tolerance = 5

# Dominio de hipervinculos a eliminar
domain_to_remove = "track.wlh.es"

# Funcion para verificar si el tamanio de la imagen esta dentro del margen de tolerancia
def is_within_tolerance(width, height, target_width, target_height):
    return abs(width - target_width) <= tolerance and abs(height - target_height) <= tolerance

# Paso 1: Identificar las paginas con imagenes especificas y guardarlas
def find_pages_with_target_images(pdf_document):
    pages_with_images = []
    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        for img in page.get_images(full=True):
            width, height = img[2], img[3]
            if any(is_within_tolerance(width, height, w, h) for w, h in target_sizes):
                pages_with_images.append(page_number)
                print(f"Pagina {page_number + 1} contiene imagen de {width}x{height}.")
                break  # Si encontramos una imagen especifica, pasamos a la siguiente pagina
    return pages_with_images

# Funcion para eliminar imagenes especificas en la pagina
def remove_target_images(page):
    modified = False
    for img in page.get_images(full=True):
        width, height = img[2], img[3]
        if any(is_within_tolerance(width, height, w, h) for w, h in target_sizes):
            print(f"Eliminando imagen de tamanio {width}x{height} en la pagina {page.number + 1}")
            xref = img[0]
            page.delete_image(xref)
            modified = True
    return modified

# Funcion para eliminar hipervinculos
def remove_links(pdf_document, domain="track.wlh.es"):
    # Iterar sobre cada pagina del PDF
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]

        # Eliminar enlaces con el dominio especificado
        links = page.get_links()
        for link in links:
            uri = link.get("uri", "")
            if domain in uri:
                print(f"Eliminando enlace con URI '{uri}' en la pagina {page_num + 1}")
                page.delete_link(link)
    return pdf_document

def remove_watermark(pdf_document, target_image_size=(395, 72), tolerance=5):
    # Eliminar imagenes especificas directamente sin redaccion
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        for img in page.get_images(full=True):
            xref = img[0]  # Referencia de la imagen
            width = img[2]
            height = img[3]
            # Verificar si el tamanio de la imagen esta dentro del rango de tolerancia
            if (abs(width - target_image_size[0]) <= tolerance) and (abs(height - target_image_size[1]) <= tolerance):
                print(f"Eliminando imagen de tamanio {width}x{height} en la pagina {page_num + 1}")
                page.delete_image(xref)  # Elimina la imagen usando su referencia

    return pdf_document


def remove_text(pdf_document):
    text_patterns = [
        r"1 coin = 1 pdf sin publicidad",
        r"Reservados todos los derechos\.? No se permite la explotación económica ni la transformación de esta obra\.? Queda permitida la impresión en su totalidad\.?",
        r"[a-fA-F0-9]{40}-\d{7}",  # Patron ajustado para detectar el formato hexadecimal-numerico
        r"Las descargas sin publicidad se realizan con las coins"
    ]

    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]

        # Obtener los bloques de texto en la pagina
        text_blocks = page.get_text("blocks")

        # Iterar sobre cada bloque de texto y verificar si coincide con los patrones
        for block in text_blocks:
            text = block[4]
            for pattern in text_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    # Si el texto coincide, crear una redaccion para cubrirlo
                    rect = fitz.Rect(block[:4])
                    page.add_redact_annot(rect, fill=(1, 1, 1))  # Redacta en blanco
                    print(f"Texto eliminado en pagina {page_num + 1}: '{text}'")

        page.apply_redactions()
    return pdf_document

# Funcion para obtener los limites del contenido restante en la pagina
def get_content_bounds(page):
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')
    has_text = False  # Variable para verificar si hay texto en la pagina

    # Obtener cuadros delimitadores de texto e imagenes
    for block in page.get_text("blocks"):
        has_text = True  # Si hay bloques de texto, marcamos has_text como True
        x0, y0, x1, y1 = block[:4]
        min_x, min_y = min(min_x, x0), min(min_y, y0)
        max_x, max_y = max(max_x, x1), max(max_y, y1)

    for img in page.get_images(full=True):
        try:
            img_rect = page.get_image_bbox(img[0])
            min_x, min_y = min(min_x, img_rect.x0), min(min_y, img_rect.y0)
            max_x, max_y = max(max_x, img_rect.x1), max(max_y, img_rect.y1)
        except ValueError:
            pass

    return fitz.Rect(min_x, min_y, max_x, max_y) if min_x != float('inf') else page.rect, has_text

# Paso 2: Procesar las paginas identificadas y aplicar modificaciones
def process_pages(pdf_document, pages_with_images, output_pdf_path):
    new_pdf = fitz.open()  # Crear un nuevo documento de salida

    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)

        if page_number in pages_with_images:
            # Si la pagina contiene una imagen especifica, eliminamos imagenes, hipervinculos y textos
            remove_target_images(page)

            # Obtener el tamanio exacto de la pagina y la rotacion
            page_rect = page.rect
            page_rotation = page.rotation
            content_bounds, has_text = get_content_bounds(page)

            # Condicion para aplicar el escalado sin desplazamiento si solo hay imagenes
            if has_text:
                # Aplicar escalado y desplazamiento normal
                new_rect = fitz.Rect(offset_x, offset_y, offset_x + content_bounds.width * scale_adjustment, offset_y + content_bounds.height * scale_adjustment)
            else:
                # Aplicar escalado centrado sin desplazamiento si solo hay imagenes
                center_x, center_y = page_rect.width / 2, page_rect.height / 2
                new_rect = fitz.Rect(
                    center_x - (content_bounds.width * scale_adjustment) / 2,
                    center_y - (content_bounds.height * scale_adjustment) / 2,
                    center_x + (content_bounds.width * scale_adjustment) / 2,
                    center_y + (content_bounds.height * scale_adjustment) / 2
                )

            # Crear una nueva pagina en el documento de salida con el mismo tamanio
            new_page = new_pdf.new_page(width=page_rect.width, height=page_rect.height)

            # Mostrar el contenido de la pagina original en la nueva pagina, respetando la rotacion y el rectangulo ajustado
            new_page.show_pdf_page(
                rect=new_rect,
                src=page.parent,  # Documento original
                pno=page.number,  # Numero de la pagina original
                rotate=page_rotation
            )
            print(f"Pagina {page_number + 1} modificada y copiada con tamanio y rotacion exactos.")
        else:
            # Copiar la pagina original sin modificaciones
            new_pdf.insert_pdf(pdf_document, from_page=page_number, to_page=page_number)
            print(f"Pagina {page_number + 1} copiada sin modificaciones.")

    return new_pdf

# Funcion principal para procesar el PDF
def main(input_pdf_path, output_pdf_path):
    pdf_document = fitz.open(input_pdf_path)

    # Paso 1: Eliminar hipervinculos y marcas de agua
    pdf_document = remove_links(pdf_document)
    pdf_document = remove_watermark(pdf_document)

    # Verificar si el PDF tiene 6 o mas paginas
    if len(pdf_document) >= 6:
        print("El documento tiene 6 o mas paginas. Procediendo a eliminar paginas 4 y 5.")

        # Eliminar las paginas 4 y 5 si existen
        pages_to_remove = [3, 4]  # Paginas 4 y 5 (indice 3 y 4)
        for page_number in sorted(pages_to_remove, reverse=True):
            if page_number < len(pdf_document):
                pdf_document.delete_page(page_number)
                print(f"Pagina {page_number + 1} eliminada.")
    else:
        print("El documento tiene menos de 6 paginas. No se eliminan paginas.")

    # Paso 2: Identificar paginas con banners
    pages_with_images = find_pages_with_target_images(pdf_document)

    # Paso 3: Procesar y copiar solo las paginas identificadas
    pdf_document = process_pages(pdf_document, pages_with_images, output_pdf_path)

    # Eliminacion de texto y guardado del documento
    pdf_document = remove_text(pdf_document)
    pdf_document.save(output_pdf_path)
    pdf_document.close()
    print("Proceso completado.")
