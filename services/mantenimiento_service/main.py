from fastapi import FastAPI, HTTPException
import psycopg2
import os

app = FastAPI(title="Servicio de Mantenimiento", version="1.0.0")

# ---- Conexión para Render ----
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no está configurada")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

# ---- Endpoints ----

@app.get("/mantenimientos")
def listar_mantenimientos():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id,
               equipo_id,
               COALESCE(fecha_realizada, fecha_programada, fecha_registro) AS fecha,
               tipo,
               costo
        FROM mantenimientos;
        """
    )
    data = cur.fetchall()
    cur.close()
    conn.close()

    return {"mantenimientos": data}

@app.post("/mantenimientos")
def crear_mantenimiento(equipo_id: int, tipo: str, costo: float):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO mantenimientos (equipo_id, tipo, costo) VALUES (%s, %s, %s) RETURNING id;",
        (equipo_id, tipo, costo)
    )
    new_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Mantenimiento registrado", "id": new_id}
