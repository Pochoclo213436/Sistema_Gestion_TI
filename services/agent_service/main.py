from fastapi import FastAPI, BackgroundTasks
import asyncpg
import os
from datetime import datetime, date, timedelta

app = FastAPI(title="Agent Service", version="1.0.0")

DATABASE_URL = os.getenv("DATABASE_URL")

async def get_db_pool():
    return await asyncpg.create_pool(DATABASE_URL)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# ===========================
#  NOTIFICACIONES SIMPLES
# ===========================

async def crear_notificacion(pool, titulo: str, mensaje: str):
    """Inserta una notificación (solo columnas reales)."""
    query = """
        INSERT INTO notificaciones (titulo, mensaje)
        VALUES ($1, $2)
    """
    async with pool.acquire() as conn:
        await conn.execute(query, titulo, mensaje)

@app.get("/notificaciones")
async def get_notificaciones(leida: bool | None = None, limit: int = 50):
    pool = await get_db_pool()

    query = """
        SELECT id, titulo, mensaje, leida, fecha
        FROM notificaciones
        WHERE ($1::boolean IS NULL OR leida = $1)
        ORDER BY fecha DESC
        LIMIT $2
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, leida, limit)
        return [dict(r) for r in rows]

@app.put("/notificaciones/{notif_id}/marcar-leida")
async def marcar_notificacion_leida(notif_id: int):
    pool = await get_db_pool()

    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE notificaciones SET leida = TRUE WHERE id = $1",
            notif_id
        )

    return {"message": "Notificación marcada como leída"}

# ===========================================
#   ENDPOINTS (NO OPERATIVOS) PERO SE MANTIENEN
#   → Generarán notificaciones simples
# ===========================================

@app.post("/check-maintenance")
async def check_maintenance_reminders():
    pool = await get_db_pool()

    await crear_notificacion(pool, "Mantenimiento Revisado", "Se ejecutó check-maintenance")
    return {"status": "ok"}

@app.post("/check-obsolescence")
async def check_equipment_obsolescence():
    pool = await get_db_pool()

    await crear_notificacion(pool, "Obsolescencia Revisada", "Se ejecutó check-obsolescence")
    return {"status": "ok"}

@app.post("/check-warranties")
async def check_warranty_expiration():
    pool = await get_db_pool()

    await crear_notificacion(pool, "Garantías Revisadas", "Se ejecutó check-warranties")
    return {"status": "ok"}

@app.post("/analyze-maintenance-costs")
async def analyze_maintenance_costs():
    pool = await get_db_pool()

    await crear_notificacion(pool, "Costos Analizados", "Se ejecutó analyze-maintenance-costs")
    return {"status": "ok"}

@app.post("/run-all-agents")
async def run_all_agents(background_tasks: BackgroundTasks):

    async def ejecutar():
        await check_maintenance_reminders()
        await check_equipment_obsolescence()
        await check_warranty_expiration()
        await analyze_maintenance_costs()

    background_tasks.add_task(ejecutar)

    return {"message": "Agentes ejecutándose en segundo plano"}
