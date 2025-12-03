from fastapi import FastAPI, BackgroundTasks
import asyncpg
import os
from datetime import datetime, timedelta

app = FastAPI(title="Agent Service", version="1.0.0")

# ================================
#  CONFIGURACIÓN DEL POOL GLOBAL
# ================================
DATABASE_URL = os.getenv("DATABASE_URL")
pool: asyncpg.Pool | None = None

if not DATABASE_URL:
    raise RuntimeError("❌ ERROR: DATABASE_URL no está configurado.")

@app.on_event("startup")
async def startup():
    global pool
    try:
        pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=5,
            timeout=10
        )
        print("✅ Pool de conexiones inicializado correctamente.")
    except Exception as e:
        print(f"❌ Error inicializando pool: {e}")
        raise

@app.on_event("shutdown")
async def shutdown():
    global pool
    if pool:
        await pool.close()
        print("🧹 Pool cerrado correctamente.")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# ===========================================
#  FUNCIONES PARA AGENTES
# ===========================================

async def crear_notificacion(titulo: str, mensaje: str):
    query = "INSERT INTO notificaciones (titulo, mensaje) VALUES ($1, $2)"
    async with pool.acquire() as conn:
        await conn.execute(query, titulo, mensaje)

async def agente_mantenimiento():
    await crear_notificacion("Mantenimiento Revisado", "Se ejecutó check-maintenance")

async def agente_obsolescencia():
    await crear_notificacion("Obsolescencia Revisada", "Se ejecutó check-obsolescence")

async def agente_garantias():
    await crear_notificacion("Garantías Revisadas", "Se ejecutó check-warranties")

async def agente_costos():
    await crear_notificacion("Costos Analizados", "Se ejecutó analyze-maintenance-costs")

# ===========================================
#  ENDPOINTS
# ===========================================

@app.post("/check-maintenance")
async def check_maintenance_reminders():
    await agente_mantenimiento()
    return {"status": "ok"}

@app.post("/check-obsolescence")
async def check_equipment_obsolescence():
    await agente_obsolescencia()
    return {"status": "ok"}

@app.post("/check-warranties")
async def check_warranty_expiration():
    await agente_garantias()
    return {"status": "ok"}

@app.post("/analyze-maintenance-costs")
async def analyze_maintenance_costs():
    await agente_costos()
    return {"status": "ok"}

@app.post("/run-all-agents")
async def run_all_agents(background_tasks: BackgroundTasks):

    async def ejecutar():
        await agente_mantenimiento()
        await agente_obsolescencia()
        await agente_garantias()
        await agente_costos()

    background_tasks.add_task(ejecutar)
    return {"message": "Agentes ejecutándose en segundo plano"}