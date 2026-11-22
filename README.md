# UrbanVision Lima — Dashboard Interactivo de Cobertura Urbana Satelital

Dashboard interactivo de segmentación semántica satelital (**U-Net + EfficientNet-B4**) sobre **240 imágenes (2 115,19 ha)** en **12 distritos de Lima Metropolitana**.

---

## 🚀 Cómo abrir o correr el proyecto (Para compañeros del equipo)

Después de clonar este repositorio:

```bash
git clone https://github.com/dessDario01/ML_DASBOARD_F.git
cd ML_DASBOARD_F
```

Tienes **dos formas** de usarlo:

### Opción 1: Sin instalar nada (Doble Clic directo)
1. Abre la carpeta del proyecto en tu explorador de archivos.
2. Haz **doble clic** sobre **`dashboard_sustentacion.html`**.
3. Se abrirá directamente en tu navegador con todos los gráficos animados, el inspector con radar, el escáner satelital de cortinilla y la descarga de CSV funcionando al 100 %.

---

### Opción 2: Con el servidor Flask (en Visual Studio Code / Terminal)
1. Instala la única dependencia (`Flask`):
   ```bash
   pip install -r requirements.txt
   ```
2. Ejecuta el servidor:
   ```bash
   python app.py
   ```
3. Abre en tu navegador:
   👉 **http://127.0.0.1:5000**

---

## 📦 Despliegue en PythonAnywhere

El repositorio ya incluye el archivo **`despliegue_pythonanywhere.zip`** (1,68 MB) listo para subir a PythonAnywhere. Si haces algún cambio y deseas regenerar el archivo `.zip`, ejecuta:

```bash
python build_zip.py
```

---

## 📁 Estructura del Repositorio

```text
├── app.py                              # Servidor Flask ligero
├── requirements.txt                    # Dependencia (Flask)
├── build_zip.py                        # Empaquetador automático para PythonAnywhere
├── dashboard_sustentacion.html         # Versión autocontenida (abre con doble clic sin servidor)
├── despliegue_pythonanywhere.zip       # Paquete listo para PythonAnywhere
├── templates/
│   └── index.html                      # Plantilla principal del Dashboard
└── static/
    ├── tabla_porcentajes.csv           # Porcentajes de los 4 indicadores por distrito
    ├── indicadores_por_distrito.csv    # Conteos de píxeles, hectáreas y porcentajes
    ├── conteos_por_imagen.csv          # Conteos detallados de las 240 imágenes
    └── muestras/                       # Tríos recortados para el escáner de cortinilla
```
