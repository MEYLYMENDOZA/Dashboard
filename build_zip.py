# -*- coding: utf-8 -*-
"""
Empaqueta el dashboard para PythonAnywhere en despliegue_pythonanywhere.zip.
Excluye las figuras gigantes crudas de 9 MB y conserva los recortes optimizados
en static/muestras/ y los CSV corregidos para mantener el paquete ligero (~2 MB).
"""

import os
import zipfile
from pathlib import Path

BASE_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
OUTPUT_ZIP = BASE_DIR / "despliegue_pythonanywhere.zip"

FILES_TO_INCLUDE = [
    "app.py",
    "requirements.txt",
    "dashboard_sustentacion.html",
]

DIRS_TO_INCLUDE = [
    "templates",
    "static",
]

# Excluimos los mosaicos gigantes crudos (21 MB) porque ya están recortados y
# optimizados en static/muestras/ para la cortinilla interactiva.
EXCLUDED_STATIC_FILES = {
    "verificacion_visual.png",
    "verificacion_visual_1.png",
    "verificacion_visual_2.png",
    "composicion_distritos.png",
    "vegetacion_distritos.png",
    "leyenda_clases.png",
}


def build_zip():
    print(f"Generando paquete optimizado para PythonAnywhere en: {OUTPUT_ZIP}")
    added_count = 0

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename in FILES_TO_INCLUDE:
            file_path = BASE_DIR / filename
            if file_path.is_file():
                zf.write(file_path, arcname=filename)
                print(f"  [+] Archivo agregado: {filename}")
                added_count += 1

        for dirname in DIRS_TO_INCLUDE:
            dir_path = BASE_DIR / dirname
            if not dir_path.is_dir():
                continue

            for item in sorted(dir_path.rglob("*")):
                if item.is_file():
                    if item.name in EXCLUDED_STATIC_FILES:
                        continue
                    arcname = item.relative_to(BASE_DIR).as_posix()
                    zf.write(item, arcname=arcname)
                    print(f"  [+] Agregado: {arcname}")
                    added_count += 1

    size_kb = OUTPUT_ZIP.stat().st_size / 1024
    print("-" * 55)
    print(f"¡Completado! Total de archivos empaquetados: {added_count}")
    print(f"Archivo listo: {OUTPUT_ZIP} ({size_kb:.2f} KB)")


if __name__ == "__main__":
    build_zip()
