from flask import Flask, render_template, request, jsonify, send_file
import sqlite3, os
import openpyxl
from io import BytesIO

app = Flask(__name__)
DB_PATH = os.path.join(os.getcwd(), "database.db")

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS correos_autorizados(correo TEXT PRIMARY KEY)")
    cur.execute("""CREATE TABLE IF NOT EXISTS registros_qr(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        correo TEXT,
        zona TEXT,
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
    tipo = data.get("tipo")
    zona = data.get("zona")
    hora = data.get("hora")  # viene del frontend en formato legible

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT 1 FROM correos_autorizados WHERE correo=?", (correo,))
    if not cur.fetchone():
        return jsonify(mensaje="Correo no autorizado"), 403

    if tipo == "inicio":
        cur.execute("""
            INSERT INTO registros_qr (correo, zona, entrada)
            VALUES (?, ?, ?)
        """, (correo, zona, hora))
        mensaje = f"{correo} registrado como INICIO en {zona} a las {hora}"
    else:
        cur.execute("""
            SELECT id FROM registros_qr
            WHERE correo=? AND salida IS NULL
            ORDER BY id DESC LIMIT 1
        """, (correo,))
        fila = cur.fetchone()
        if fila:
            cur.execute("UPDATE registros_qr SET salida=? WHERE id=?", (hora, fila[0]))
            mensaje = f"{correo} registrado como FINAL en {zona} a las {hora}"
        else:
            mensaje = "No se encontró un registro previo de INICIO sin FINAL."

    con.commit()
    con.close()
    return jsonify(mensaje=mensaje)

@app.route("/descargar_excel")
def descargar_excel():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT correo, zona, entrada, salida FROM registros_qr ORDER BY id DESC")
    registros = cur.fetchall()
    con.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Registros QR"
    ws.append(["Correo", "Zona", "Hora de Entrada", "Hora de Salida"])
    for fila in registros:
        ws.append(fila)

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, download_name="registros_qr.xlsx", as_attachment=True)
