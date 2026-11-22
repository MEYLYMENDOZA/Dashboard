# -*- coding: utf-8 -*-
"""
Script auxiliar para recortar las figuras de verificación (verificacion_visual_1.png,
verificacion_visual_2.png) en tríos individuales (original, clasificacion, superpuesto)
y generar además el caso real del campo de golf de San Isidro (San Isidro_008.tif)
para el control deslizante de cortinilla y la sección de limitaciones.
"""

from pathlib import Path
from PIL import Image
import numpy as np

STATIC_DIR = Path(r"D:\2026-2\ML\WEB_DASHBOARD\static")
MUESTRAS_DIR = STATIC_DIR / "muestras"
MUESTRAS_DIR.mkdir(parents=True, exist_ok=True)


def encontrar_cajas_figura(img_path, nombres_filas):
    """
    Detecta automáticamente las 3 filas y 3 columnas de sub-imágenes en las figuras
    de verificación exportadas por Matplotlib (2400x2400 px), ignorando márgenes y títulos.
    """
    img = Image.open(img_path).convert("RGB")
    arr = np.asarray(img)

    # Un píxel no es fondo blanco si algún canal es < 245
    no_blanco = np.any(arr < 245, axis=2)

    # Detectar intervalos horizontales (las 3 columnas: Original, Clasificación, Superpuesto)
    # Miramos la banda central vertical o sumamos por columna
    col_density = no_blanco.mean(axis=0)
    cols_activas = col_density > 0.15

    def obtener_segmentos(mask_1d, min_len=300):
        segs = []
        in_seg = False
        start = 0
        for i, val in enumerate(mask_1d):
            if val and not in_seg:
                in_seg = True
                start = i
            elif not val and in_seg:
                in_seg = False
                if i - start >= min_len:
                    segs.append((start, i))
        if in_seg and len(mask_1d) - start >= min_len:
            segs.append((start, len(mask_1d)))
        return segs

    col_segs = obtener_segmentos(cols_activas, min_len=400)
    print(f"{img_path.name} -> Columnas detectadas: {col_segs}")

    # Para las filas, miramos dentro de la primera columna (la imagen satelital original nunca tiene blanco puro)
    c0_start, c0_end = col_segs[0]
    row_density = no_blanco[:, c0_start:c0_end].mean(axis=1)
    rows_activas = row_density > 0.50
    row_segs = obtener_segmentos(rows_activas, min_len=400)
    print(f"{img_path.name} -> Filas detectadas: {row_segs}")

    resultados = []
    tipos = ["orig", "mask", "over"]

    for r_idx, (r0, r1) in enumerate(row_segs[:len(nombres_filas)]):
        info = nombres_filas[r_idx]
        alto = r1 - r0
        for c_idx, (c0, c1) in enumerate(col_segs[:3]):
            ancho = c1 - c0
            # Asegurar recorte cuadrado exacto
            lado = min(alto, ancho)
            crop = img.crop((c0, r0, c0 + lado, r0 + lado))
            # Redimensionar a 512x512 para nitidez óptima y peso ligero
            crop_resized = crop.resize((512, 512), Image.LANCZOS)
            out_name = f"{info['id']}_{tipos[c_idx]}.jpg"
            out_path = MUESTRAS_DIR / out_name
            crop_resized.save(out_path, format="JPEG", quality=88, optimize=True)
        resultados.append(info)
        print(f"  [+] Guardado trío para {info['titulo']} ({info['id']})")

    return resultados


def generar_caso_golf_san_isidro():
    """
    Genera el trío real (Original, Clasificación, Superposición) de San Isidro_008.tif
    (el campo de golf de San Isidro donde los búnkeres de arena se clasifican como agua)
    usando el modelo ONNX unet_lima.onnx con inferencia por ventanas de 384x384.
    """
    tif_path = Path(r"D:\2026-2\ML\dataset limaa\dataset_lima\San Isidro\San Isidro_008.tif")
    onnx_path = Path(r"D:\2026-2\ML\dataset limaa\unet_lima.onnx")

    if not tif_path.is_file():
        print("[!] No se encontró San Isidro_008.tif")
        return

    img = Image.open(tif_path).convert("RGB")
    arr = np.asarray(img, dtype=np.float32)
    H, W, _ = arr.shape

    # Paleta oficial OpenEarthMap
    CLASES_RGB = np.array([
        [0, 0, 0],         # 0 Background
        [128, 0, 0],       # 1 Bareland
        [0, 255, 36],      # 2 Rangeland
        [148, 148, 148],   # 3 Developed space
        [255, 255, 255],   # 4 Road
        [34, 97, 38],      # 5 Tree
        [0, 69, 255],      # 6 Water
        [75, 181, 73],     # 7 Agriculture land
        [222, 31, 7],      # 8 Building
    ], dtype=np.uint8)

    try:
        import onnxruntime as ort
        sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
        input_name = sess.get_inputs()[0].name

        # Inferencia por ventanas deslizantes de 384x384 con solape
        ventana = 384
        paso = 320
        coords = [0, 320, 640]
        probs_acc = np.zeros((H, W, 9), dtype=np.float32)
        pesos_acc = np.zeros((H, W, 1), dtype=np.float32)

        for y0 in coords:
            for x0 in coords:
                parche = arr[y0:y0 + ventana, x0:x0 + ventana]
                salida = sess.run(None, {input_name: parche[None, ...]})[0][0]
                probs_acc[y0:y0 + ventana, x0:x0 + ventana] += salida
                pesos_acc[y0:y0 + ventana, x0:x0 + ventana] += 1.0

        mapa = np.argmax(probs_acc / np.maximum(pesos_acc, 1.0), axis=-1).astype(np.uint8)
        agua_px = int((mapa == 6).sum())
        print(f"  [+] Inferencia ONNX en San Isidro_008.tif completada. Píxeles de agua (búnkeres): {agua_px}")

        mask_rgb = CLASES_RGB[mapa]
        mask_img = Image.fromarray(mask_rgb, mode="RGB")
        over_img = Image.blend(img, mask_img, 0.45)

        img.resize((512, 512), Image.LANCZOS).save(MUESTRAS_DIR / "san_isidro_008_orig.jpg", "JPEG", quality=88, optimize=True)
        mask_img.resize((512, 512), Image.NEAREST).save(MUESTRAS_DIR / "san_isidro_008_mask.jpg", "JPEG", quality=90, optimize=True)
        over_img.resize((512, 512), Image.LANCZOS).save(MUESTRAS_DIR / "san_isidro_008_over.jpg", "JPEG", quality=88, optimize=True)
        print("  [+] Trío de San Isidro_008 (Campo de Golf) guardado en static/muestras/")
    except Exception as e:
        print(f"[!] No se pudo ejecutar ONNX para San Isidro_008: {e}")


if __name__ == "__main__":
    f1 = STATIC_DIR / "verificacion_visual_1.png"
    f2 = STATIC_DIR / "verificacion_visual_2.png"

    if f1.is_file():
        encontrar_cajas_figura(f1, [
            {"id": "ves_005", "distrito": "Villa El Salvador", "archivo": "Villa El Salvador_005.tif", "titulo": "Villa El Salvador — Villa El Salvador_005.tif"},
            {"id": "ves_004", "distrito": "Villa El Salvador", "archivo": "Villa El Salvador_004.tif", "titulo": "Villa El Salvador — Villa El Salvador_004.tif"},
            {"id": "san_borja_003", "distrito": "San Borja", "archivo": "San Borja_003.tif", "titulo": "San Borja — San Borja_003.tif"},
        ])

    if f2.is_file():
        encontrar_cajas_figura(f2, [
            {"id": "san_borja_006", "distrito": "San Borja", "archivo": "San Borja_006.tif", "titulo": "San Borja — San Borja_006.tif"},
            {"id": "ancon_015", "distrito": "Ancón", "archivo": "Ancon_015.tif", "titulo": "Ancón — Ancon_015.tif"},
            {"id": "ancon_009", "distrito": "Ancón", "archivo": "Ancon_009.tif", "titulo": "Ancón — Ancon_009.tif"},
        ])

    generar_caso_golf_san_isidro()
