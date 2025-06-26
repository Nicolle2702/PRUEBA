from flask import Flask, render_template, request, jsonify, send_file
import sqlite3, os
import openpyxl
from io import BytesIO
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
DB_PATH = os.path.join(os.getcwd(), "database.db")

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS correos_autorizados(correo TEXT PRIMARY KEY)")
    cur.execute("""CREATE TABLE IF NOT EXISTS registros_qr(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        correo TEXT,
        contenido_qr TEXT,
        fecha_hora TEXT
    )""")
    cur.executemany("INSERT OR IGNORE INTO correos_autorizados (correo) VALUES (?)",
                    [("nicolle@email.com",)])
    con.commit()
    con.close()

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/registrar_qr", methods=["POST"])
def registrar():
    data = request.json
    correo = data.get("correo")
    contenido_qr = data.get("contenido_qr")
    fecha_hora = data.get("fecha_hora")

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT 1 FROM correos_autorizados WHERE correo=?", (correo,))
    if not cur.fetchone():
        return jsonify(mensaje="Correo no autorizado"), 403
    cur.execute("INSERT INTO registros_qr (correo, contenido_qr, fecha_hora) VALUES (?, ?, ?)",
                (correo, contenido_qr, fecha_hora))
    con.commit()
    con.close()
    return jsonify(mensaje=f"Registrado: {correo} → {contenido_qr} a las {fecha_hora}")

@app.route("/descargar_excel")
def descargar_excel():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT correo, contenido_qr, fecha_hora FROM registros_qr ORDER BY id DESC")
    registros = cur.fetchall()
    con.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Registros QR"
    ws.append(["Correo", "Texto extraído del QR", "Fecha y hora"])

    for correo, contenido_qr, fecha in registros:
        try:
            resp = requests.get(contenido_qr, timeout=5)
            soup = BeautifulSoup(resp.text, 'html.parser')
            extraido = soup.get_text(strip=True)
        except Exception:
            extraido = contenido_qr

        ws.append([correo, extraido, fecha])

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, download_name="registros_qr.xlsx", as_attachment=True)
