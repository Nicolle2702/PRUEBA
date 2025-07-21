from flask import Flask, render_template, request, jsonify, send_file
import sqlite3, os
import openpyxl
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
DB_PATH = os.path.join(os.getcwd(), "database.db")

# Inicializar base de datos
def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS correos_autorizados(correo TEXT PRIMARY KEY)")
    cur.execute("""CREATE TABLE IF NOT EXISTS registros_qr(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        correo TEXT,
        entrada TEXT,
        salida TEXT
    )""")
    cur.executemany("INSERT OR IGNORE INTO correos_autorizados (correo) VALUES (?)", [
        ("nicolle@email.com",)
    ])
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
    tipo = data.get("tipo")  # "inicio" o "final"
    hora = datetime.now().isoformat()

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("SELECT 1 FROM correos_autorizados WHERE correo=?", (correo,))
    if not cur.fetchone():
        return jsonify(mensaje="Correo no autorizado"), 403

    if tipo == "inicio":
        cur.execute("INSERT INTO registros_qr (correo, entrada) VALUES (?, ?)", (correo, hora))
        mensaje = f"{correo} registrado como INICIO a las {hora}"
    else:
        cur.execute("""
            UPDATE registros_qr
            SET salida = ?
            WHERE correo = ? AND salida IS NULL
            ORDER BY id DESC
            LIMIT 1
        """, (hora, correo))
        if cur.rowcount == 0:
            mensaje = "No se encontró un registro de entrada para completar con salida."
        else:
            mensaje = f"{correo} registrado como FINAL a las {hora}"

    con.commit()
    con.close()
    return jsonify(mensaje=mensaje)

@app.route("/descargar_excel")
def descargar_excel():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT correo, entrada, salida FROM registros_qr ORDER BY id DESC")
    registros = cur.fetchall()
    con.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Registros QR"
    ws.append(["Correo", "Hora de Entrada", "Hora de Salida"])

    for fila in registros:
        ws.append(fila)

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, download_name="registros_qr.xlsx", as_attachment=True)
