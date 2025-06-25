from flask import Flask, render_template, request, jsonify, send_file
import sqlite3, os
import openpyxl
from io import BytesIO

app = Flask(__name__)
DB_PATH = os.path.join(os.getcwd(), "database.db")

# Inicializar base de datos y agregar correo autorizado
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
    # Agrega aquí tus correos autorizados
    cur.executemany("INSERT OR IGNORE INTO correos_autorizados (correo) VALUES (?)", [
        ("nicolle@email.com",)
    ])
    con.commit()
    con.close()

init_db()

# Página principal
@app.route("/")
def index():
    return render_template("index.html")

# Registrar un escaneo QR
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

# Descargar el archivo Excel con los registros
@app.route("/descargar_excel")
def descargar_excel():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT correo, contenido_qr, fecha_hora FROM registros_qr ORDER BY id DESC")
    registros = cur.fetchall()
    con.close()

    # Crear archivo Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Registros QR"
    ws.append(["Correo", "Texto extraído del QR", "Fecha y hora"])

    for correo, contenido_qr, fecha in registros:
        # Extraer texto después del signo "=" (si existe)
        if "=" in contenido_qr:
            extraido = contenido_qr.split("=")[-1]
        else:
            extraido = contenido_qr  # Usa todo el contenido si no hay "="

        ws.append([correo, extraido, fecha])

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, download_name="registros_qr.xlsx", as_attachment=True)
