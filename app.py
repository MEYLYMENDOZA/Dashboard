# -*- coding: utf-8 -*-
"""
Servidor Flask para el dashboard:
'Visión Artificial Aplicada al Urbanismo en Lima'.
"""

import base64
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import quote
from flask import Flask, jsonify, render_template, request, send_file, send_from_directory

BASE_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
REPORTE_TXT_PATH = BASE_DIR / "ultimo_reporte_ejecucion.txt"
REPORTE_HTML_PATH = BASE_DIR / "ultimo_reporte_enviado.html"
RADAR_PNG_PATH = BASE_DIR / "ultimo_grafico_inspector.png"

# Opcional: solo si algún día deseas envío silencioso sin abrir pestaña de Gmail
REMITENTE_CORREO = os.environ.get("SMTP_USER", "").strip()
REMITENTE_CLAVE_APP = os.environ.get("SMTP_PASS", "").strip()

app = Flask(
    __name__,
    template_folder=str(TEMPLATES_DIR),
    static_folder=str(STATIC_DIR)
)


def construir_html_notificacion(remitente, destinatario, distritos, fecha, radar_b64=""):
    filas_barras = ""
    tarjetas_inspector = ""

    for d in distritos:
        nombre = d.get("nombre", "Distrito")
        area = f"{float(d.get('area', 0)):.2f}".replace(".", ",")
        veg = float(d.get("veg", 0))
        vias = float(d.get("vias", 0))
        urb = float(d.get("urb", 0))
        suelo = float(d.get("suelo", 0))

        ha_veg = f"{float(d.get('ha_veg', 0)):.2f}".replace(".", ",")
        ha_vias = f"{float(d.get('ha_vias', 0)):.2f}".replace(".", ",")
        ha_urb = f"{float(d.get('ha_urb', 0)):.2f}".replace(".", ",")
        ha_suelo = f"{float(d.get('ha_suelo', 0)):.2f}".replace(".", ",")

        s_veg = f"{veg:.2f}".replace(".", ",")
        s_vias = f"{vias:.2f}".replace(".", ",")
        s_urb = f"{urb:.2f}".replace(".", ",")
        s_suelo = f"{suelo:.2f}".replace(".", ",")

        filas_barras += f"""
        <tr>
          <td style="padding: 8px 10px; font-weight: 700; color: #18202c; width: 155px; border-bottom: 1px solid #e2e8f0;">
            {nombre}<br><span style="font-size: 11px; font-weight: 400; color: #64748b;">{area} ha</span>
          </td>
          <td style="padding: 8px 10px; border-bottom: 1px solid #e2e8f0;">
            <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse: collapse; height: 18px; border-radius: 3px; overflow: hidden;">
              <tr>
                <td style="width: {veg}%; background-color: #2d6a4f;"></td>
                <td style="width: {vias}%; background-color: #5c677d;"></td>
                <td style="width: {urb}%; background-color: #b5483a;"></td>
                <td style="width: {suelo}%; background-color: #c88a2b;"></td>
              </tr>
            </table>
            <div style="font-size: 11px; color: #475569; margin-top: 4px;">
              <span style="color:#2d6a4f;font-weight:700;">■ Veg:</span> {s_veg}% ({ha_veg} ha) &nbsp;|&nbsp;
              <span style="color:#5c677d;font-weight:700;">■ Vías:</span> {s_vias}% ({ha_vias} ha) &nbsp;|&nbsp;
              <span style="color:#b5483a;font-weight:700;">■ Urb:</span> {s_urb}% ({ha_urb} ha) &nbsp;|&nbsp;
              <span style="color:#c88a2b;font-weight:700;">■ Suelo:</span> {s_suelo}% ({ha_suelo} ha)
            </div>
          </td>
        </tr>
        """

        tarjetas_inspector += f"""
        <div style="border: 1px solid #dce2ea; border-radius: 6px; padding: 10px 12px; margin-bottom: 8px; background: #f8fafc;">
          <div style="font-weight: 700; color: #18202c; margin-bottom: 4px;">{nombre} — {area} ha (20 recortes satelitales)</div>
          <div style="font-size: 12px; color: #334155;">
            Vegetación: <strong>{s_veg}%</strong> ({ha_veg} ha) ·
            Vías: <strong>{s_vias}%</strong> ({ha_vias} ha) ·
            Urbanizada: <strong>{s_urb}%</strong> ({ha_urb} ha) ·
            Suelo descubierto: <strong>{s_suelo}%</strong> ({ha_suelo} ha)
          </div>
        </div>
        """

    bloque_radar = ""
    if radar_b64.startswith("data:image/png;base64,"):
        bloque_radar = f"""
        <div style="margin-top: 18px; text-align: center; border: 1px solid #dce2ea; border-radius: 8px; padding: 12px; background: #ffffff;">
          <div style="font-size: 12px; font-weight: 700; color: #475569; margin-bottom: 8px; text-transform: uppercase;">
            Gráfico — Inspector de Distrito Activo (Perfil vs. Promedio Lima)
          </div>
          <img src="{radar_b64}" alt="Gráfico Inspector de Distrito Activo" style="max-width: 100%; height: auto; border-radius: 4px;" />
        </div>
        """

    nombres_titulo = ", ".join(d.get("nombre", "") for d in distritos)
    linea_remitente = f"De: {remitente} · " if remitente else ""

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="utf-8"><title>Reporte UrbanVision Lima</title></head>
    <body style="font-family: Arial, Helvetica, sans-serif; background-color: #f4f6f8; margin: 0; padding: 20px; color: #18202c;">
      <div style="max-width: 680px; margin: 0 auto; background: #ffffff; border: 1px solid #dce2ea; border-radius: 8px; overflow: hidden;">
        <div style="background: #2d6a4f; color: #ffffff; padding: 16px 20px;">
          <div style="font-size: 16px; font-weight: 700;">UrbanVision Lima — Reporte de Cobertura Urbana</div>
          <div style="font-size: 12px; opacity: 0.92; margin-top: 3px;">{linea_remitente}Para: {destinatario} · {fecha}</div>
        </div>
        <div style="padding: 18px 20px;">
          <div style="font-size: 13px; font-weight: 700; text-transform: uppercase; color: #2d6a4f; margin-bottom: 8px;">
            Distribución Seleccionada ({len(distritos)} {"distrito" if len(distritos) == 1 else "distritos"}: {nombres_titulo})
          </div>
          <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse: collapse; border: 1px solid #e2e8f0;">
            {filas_barras}
          </table>
          <div style="font-size: 13px; font-weight: 700; text-transform: uppercase; color: #2d6a4f; margin: 18px 0 8px;">
            Inspector de Distrito Activo
          </div>
          {tarjetas_inspector}
          {bloque_radar}
          <div style="margin-top: 16px; padding-top: 12px; border-top: 1px solid #e2e8f0; font-size: 11px; color: #64748b;">
            Modelo: U-Net + EfficientNet-B4 (mIoU global: 0,6356) · Estudio satelital Lima Metropolitana.
          </div>
        </div>
      </div>
    </body>
    </html>
    """


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/descargar/<path:filename>")
def descargar_archivo(filename):
    return send_from_directory(str(STATIC_DIR), filename, as_attachment=True)


@app.route("/ultimo-reporte")
def ver_ultimo_reporte():
    if REPORTE_HTML_PATH.exists():
        return send_file(str(REPORTE_HTML_PATH))
    return "Aún no se ha generado ningún reporte.", 404


@app.route("/enviar-notificacion", methods=["POST"])
def enviar_notificacion():
    datos = request.get_json(silent=True) or {}
    remitente = (datos.get("remitente") or "").strip()
    destinatario = (datos.get("correo") or "").strip()
    distritos = datos.get("distritos") or []
    radar_b64 = (datos.get("radar_chart_base64") or "").strip()

    if not destinatario or "@" not in destinatario:
        return jsonify({
            "ok": False,
            "estado": "Correo inválido",
            "detalle": "Ingresa un correo electrónico válido para el destinatario."
        }), 400

    if not distritos:
        distritos = [{
            "nombre": datos.get("distrito", "San Isidro"),
            "area": datos.get("area", 174.64),
            "veg": datos.get("veg", 27.02),
            "ha_veg": datos.get("ha_veg", 47.19),
            "vias": datos.get("vias", 12.43),
            "ha_vias": datos.get("ha_vias", 21.70),
            "urb": datos.get("urb", 60.11),
            "ha_urb": datos.get("ha_urb", 104.99),
            "suelo": datos.get("suelo", 0.44),
            "ha_suelo": datos.get("ha_suelo", 0.76),
        }]

    distritos = distritos[:3]
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    nombres_str = ", ".join(d.get("nombre", "") for d in distritos)
    asunto = f"Reporte UrbanVision Lima — {nombres_str}"

    if radar_b64.startswith("data:image/png;base64,"):
        try:
            radar_bytes = base64.b64decode(radar_b64.split(",", 1)[1])
            with open(RADAR_PNG_PATH, "wb") as f_img:
                f_img.write(radar_bytes)
        except Exception:
            pass

    lineas_txt = [
        "REPORTE DE COBERTURA URBANA SATELITAL — URBANVISION LIMA",
        "==========================================================",
        f"Fecha y hora: {fecha}",
        f"Distritos seleccionados ({len(distritos)}): {nombres_str}",
        ""
    ]
    for d in distritos:
        lineas_txt.extend([
            f"* {d.get('nombre')} ({d.get('area')} ha):",
            f"  - Vegetación:            {d.get('veg')}% ({d.get('ha_veg')} ha)",
            f"  - Vías:                  {d.get('vias')}% ({d.get('ha_vias')} ha)",
            f"  - Superficie urbanizada: {d.get('urb')}% ({d.get('ha_urb')} ha)",
            f"  - Suelo descubierto:     {d.get('suelo')}% ({d.get('ha_suelo')} ha)",
            ""
        ])
    lineas_txt.append("Modelo: U-Net + EfficientNet-B4 (mIoU global: 0,6356)")
    texto_plano = "\n".join(lineas_txt)

    html_cuerpo = construir_html_notificacion(
        remitente=remitente,
        destinatario=destinatario,
        distritos=distritos,
        fecha=fecha,
        radar_b64=radar_b64
    )

    with open(REPORTE_TXT_PATH, "w", encoding="utf-8") as f_txt:
        f_txt.write(texto_plano)

    with open(REPORTE_HTML_PATH, "w", encoding="utf-8") as f_html:
        f_html.write(html_cuerpo)

    if REMITENTE_CORREO and REMITENTE_CLAVE_APP:
        try:
            msg = EmailMessage()
            msg["Subject"] = asunto
            msg["From"] = f"UrbanVision Lima <{REMITENTE_CORREO}>"
            msg["To"] = destinatario
            msg.set_content(texto_plano)
            msg.add_alternative(html_cuerpo, subtype="html")
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
                server.login(REMITENTE_CORREO, REMITENTE_CLAVE_APP)
                server.send_message(msg)
            return jsonify({
                "ok": True,
                "estado": "Enviado",
                "detalle": f"Correo enviado directamente a {destinatario}."
            })
        except Exception as exc:
            return jsonify({
                "ok": False,
                "estado": "Error SMTP",
                "detalle": str(exc)
            }), 500

    gmail_url = (
        f"https://mail.google.com/mail/?view=cm&fs=1"
        f"&to={quote(destinatario)}"
        f"&su={quote(asunto)}"
        f"&body={quote(texto_plano)}"
    )

    return jsonify({
        "ok": True,
        "estado": "Listo para enviar",
        "gmail_url": gmail_url,
        "detalle": f"Abriendo Gmail para enviar a {destinatario} (gráfico guardado en ultimo_grafico_inspector.png)."
    })


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, host="127.0.0.1", port=5000)