# -*- coding: utf-8 -*-
"""
Servidor Flask ligero para el dashboard académico:
'Visión Artificial Aplicada al Urbanismo en Lima'.

Nota para PythonAnywhere:
- Usa rutas absolutas dinámicas con os.path.abspath(os.path.dirname(__file__)) y pathlib.
- No requiere pandas ni librerías pesadas (usa el módulo estándar csv o el JSON embebido
  en templates/index.html), ahorrando ~50 MB de cuota de disco en PythonAnywhere.
"""

import os
from pathlib import Path
from flask import Flask, render_template, send_from_directory

BASE_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = Flask(
    __name__,
    template_folder=str(TEMPLATES_DIR),
    static_folder=str(STATIC_DIR)
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/descargar/<path:filename>")
def descargar_archivo(filename):
    return send_from_directory(str(STATIC_DIR), filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
