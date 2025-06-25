
from flask import Flask, render_template, request, jsonify
import sqlite3, os

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

    # Inserta correos autorizados (agrega todos los que quieras)
    correos = [
        ("nicolle@email.com",),
        ("ejemplo@dominio.com",)
    ]
    cur.executemany("INSERT OR IGNORE INTO correos_autorizados (correo) VALUES (?)", correos)

    con.commit()
    con.close()

# ✅ Ejecutar al iniciar el servidor (en vez de usar before_first_request)
init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/registrar_qr", methods=["POST"])
def registrar():
    data = request.json
    correo, contenido_qr, fecha_hora = data.get("correo"), data.get("contenido_qr"), data.get("fecha_hora")

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

