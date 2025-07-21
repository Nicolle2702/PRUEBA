
from flask import Flask, request, render_template, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

def init_db():
    with sqlite3.connect("database.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS registros (
                correo TEXT PRIMARY KEY,
                contenido_qr TEXT,
                hora_entrada TEXT,
                hora_salida TEXT
            )
        """)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/registrar", methods=["POST"])
def registrar():
    correo = request.form["correo"]
    accion = request.form["accion"]
    contenido_qr = request.form["contenido_qr"]
    ahora = datetime.now().isoformat()

    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        if accion == "inicio":
            cursor.execute("INSERT OR REPLACE INTO registros (correo, contenido_qr, hora_entrada) VALUES (?, ?, ?)", 
                           (correo, contenido_qr, ahora))
        elif accion == "final":
            cursor.execute("UPDATE registros SET hora_salida = ? WHERE correo = ?", (ahora, correo))
        conn.commit()

    return redirect("/")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
