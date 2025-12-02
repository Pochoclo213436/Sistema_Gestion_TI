from fastapi import FastAPI, HTTPException
import psycopg2
import os

app = FastAPI(title="Servicio de Mantenimiento", version="1.0.0")

# ---- Conexión a la base de datos ----
def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        database=os.getenv("POSTGRES_DB", "ti_management"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres")
    )

@app.get("/mantenimientos")
def listar_mantenimientos():
    conn = get_connection()
    cur = conn.cursor()
    # La tabla 'mantenimientos' no tiene columna 'fecha'. Usamos una fecha derivada.
    # Preferencia: realizada -> programada -> registro
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