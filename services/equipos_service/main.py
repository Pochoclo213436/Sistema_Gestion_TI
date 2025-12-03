from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncpg
import os
from datetime import date
import json

app = FastAPI(title="Equipos Service", version="1.0.0")

# ================================
#  CONFIG DB
# ================================
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL no está configurada")

pool: asyncpg.Pool | None = None


# ================================
#  EVENTOS DE INICIO / CIERRE
# ================================
@app.on_event("startup")
async def on_startup():
    global pool
    pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=1,
        max_size=5
    )
    print("✅ Pool creado en equipos_service")


@app.on_event("shutdown")
async def on_shutdown():
    global pool
    if pool is not None:
        await pool.close()
        print("🧹 Pool cerrado en equipos_service")
        pool = None


# ================================
#  Verificación centralizada
# ================================
async def get_pool() -> asyncpg.Pool:
    if pool is None:
        raise RuntimeError("❌ Pool no inicializado (startup falló)")
    return pool


# ================================
#  MODELOS
# ================================
class EquipoCreate(BaseModel):
    codigo_inventario: str
    categoria_id: int
    nombre: str
    marca: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    especificaciones: Optional[dict] = None
    proveedor_id: Optional[int] = None
    fecha_compra: Optional[date] = None
    costo_compra: Optional[float] = None
    fecha_garantia_fin: Optional[date] = None
    ubicacion_actual_id: Optional[int] = None
    estado_operativo: str = "operativo"
    estado_fisico: str = "bueno"
    asignado_a_id: Optional[int] = None
    notas: Optional[str] = None
    imagen_url: Optional[str] = None


class EquipoUpdate(BaseModel):
    nombre: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    especificaciones: Optional[dict] = None
    ubicacion_actual_id: Optional[int] = None
    estado_operativo: Optional[str] = None
    estado_fisico: Optional[str] = None
    asignado_a_id: Optional[int] = None
    notas: Optional[str] = None


class MovimientoCreate(BaseModel):
    equipo_id: int
    ubicacion_destino_id: int
    usuario_responsable_id: int
    motivo: str
    observaciones: Optional[str] = None


# ================================
#  ENDPOINTS
# ================================
@app.get("/health")
async def health():
    return {"service": "equipos", "status": "ok"}



# =====================================
# LISTAR EQUIPOS
# =====================================
@app.get("/equipos")
async def get_equipos(categoria: Optional[str] = None,
                      estado: Optional[str] = None,
                      ubicacion: Optional[int] = None):

    pool = await get_pool()

    query = """
        SELECT e.*,
               c.nombre AS categoria_nombre,
               COALESCE(u.edificio, '') || ' - ' || COALESCE(u.aula_oficina, '') AS ubicacion_nombre,
               p.razon_social AS proveedor_nombre
        FROM equipos e
        LEFT JOIN categorias_equipos c ON e.categoria_id = c.id
        LEFT JOIN ubicaciones u ON e.ubicacion_actual_id = u.id
        LEFT JOIN proveedores p ON e.proveedor_id = p.id
        WHERE 1=1
    """

    params = []
    px = 1

    if categoria:
        query += f" AND c.nombre = ${px}"
        params.append(categoria)
        px += 1

    if estado:
        query += f" AND e.estado_operativo = ${px}"
        params.append(estado)
        px += 1

    if ubicacion:
        query += f" AND e.ubicacion_actual_id = ${px}"
        params.append(ubicacion)
        px += 1

    query += " ORDER BY e.fecha_registro DESC"

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

        result = []
        for row in rows:
            item = dict(row)
            if item.get("especificaciones"):
                try:
                    item["especificaciones"] = json.loads(item["especificaciones"])
                except:
                    pass
            result.append(item)

        return result


# =====================================
# OBTENER EQUIPO POR ID
# =====================================
@app.get("/equipos/{equipo_id}")
async def get_equipo(equipo_id: int):
    pool = await get_pool()

    query = """
        SELECT e.*,
               c.nombre AS categoria_nombre,
               COALESCE(u.edificio, '') || ' - ' || COALESCE(u.aula_oficina, '') AS ubicacion_nombre,
               p.razon_social AS proveedor_nombre
        FROM equipos e
        LEFT JOIN categorias_equipos c ON e.categoria_id = c.id
        LEFT JOIN ubicaciones u ON e.ubicacion_actual_id = u.id
        LEFT JOIN proveedores p ON e.proveedor_id = p.id
        WHERE e.id = $1
    """

    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, equipo_id)
        if not row:
            raise HTTPException(404, "Equipo no encontrado")

        item = dict(row)
        if item.get("especificaciones"):
            try:
                item["especificaciones"] = json.loads(item["especificaciones"])
            except:
                pass

        return item



# =====================================
# CREAR EQUIPO
# =====================================
@app.post("/equipos")
async def create_equipo(data: EquipoCreate):

    pool = await get_pool()

    especificaciones_json = json.dumps(data.especificaciones) if data.especificaciones else None

    query = """
        INSERT INTO equipos (
            codigo_inventario, categoria_id, nombre, marca, modelo, numero_serie,
            especificaciones, proveedor_id, fecha_compra, costo_compra,
            fecha_garantia_fin, ubicacion_actual_id, estado_operativo, estado_fisico,
            asignado_a_id, notas, imagen_url
        )
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17)
        RETURNING id
    """

    async with pool.acquire() as conn:
        new_id = await conn.fetchval(
            query,
            data.codigo_inventario,
            data.categoria_id,
            data.nombre,
            data.marca,
            data.modelo,
            data.numero_serie,
            especificaciones_json,
            data.proveedor_id,
            data.fecha_compra,
            data.costo_compra,
            data.fecha_garantia_fin,
            data.ubicacion_actual_id,
            data.estado_operativo,
            data.estado_fisico,
            data.asignado_a_id,
            data.notas,
            data.imagen_url
        )

    return {"id": new_id, "message": "Equipo creado exitosamente"}



# =====================================
# ACTUALIZAR EQUIPO
# =====================================
@app.put("/equipos/{equipo_id}")
async def update_equipo(equipo_id: int, data: EquipoUpdate):
    pool = await get_pool()

    updates = []
    params = []
    px = 1
    body = data.dict(exclude_unset=True)

    if not body:
        raise HTTPException(400, "No hay campos para actualizar")

    for k, v in body.items():
        if k == "especificaciones" and v is not None:
            v = json.dumps(v)

        updates.append(f"{k} = ${px}")
        params.append(v)
        px += 1

    params.append(equipo_id)

    query = f"""
        UPDATE equipos
        SET {', '.join(updates)}
        WHERE id = ${px}
    """

    async with pool.acquire() as conn:
        result = await conn.execute(query, *params)
        if result == "UPDATE 0":
            raise HTTPException(404, "Equipo no encontrado")

    return {"message": "Equipo actualizado exitosamente"}



# =====================================
# BORRAR EQUIPO
# =====================================
@app.delete("/equipos/{equipo_id}")
async def delete_equipo(equipo_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM equipos WHERE id = $1", equipo_id)

        if result == "DELETE 0":
            raise HTTPException(404, "Equipo no encontrado")

    return {"message": "Equipo eliminado"}



# =====================================
# MOVIMIENTOS (CON TRANSACCIÓN)
# =====================================
@app.post("/movimientos")
async def create_movimiento(data: MovimientoCreate):
    pool = await get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():

            ubicacion_origen = await conn.fetchval(
                "SELECT ubicacion_actual_id FROM equipos WHERE id = $1",
                data.equipo_id
            )

            await conn.execute(
                """
                INSERT INTO movimientos_equipos (
                    equipo_id, ubicacion_origen_id, ubicacion_destino_id,
                    usuario_responsable_id, motivo, observaciones
                )
                VALUES ($1,$2,$3,$4,$5,$6)
                """,
                data.equipo_id,
                ubicacion_origen,
                data.ubicacion_destino_id,
                data.usuario_responsable_id,
                data.motivo,
                data.observaciones
            )

            await conn.execute(
                "UPDATE equipos SET ubicacion_actual_id = $1 WHERE id = $2",
                data.ubicacion_destino_id,
                data.equipo_id
            )

    return {"message": "Movimiento registrado exitosamente"}



# =====================================
# LISTAR CATEGORÍAS
# =====================================
@app.get("/categorias")
async def get_categorias():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM categorias_equipos ORDER BY nombre")
        return [dict(r) for r in rows]


# =====================================
# LISTAR UBICACIONES
# =====================================
@app.get("/ubicaciones")
async def get_ubicaciones():
    pool = await get_pool()

    query = """
        SELECT *,
        COALESCE(edificio, '') || ' - ' || COALESCE(aula_oficina, '') AS nombre_completo
        FROM ubicaciones
        ORDER BY edificio, aula_oficina
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query)
        return [dict(r) for r in rows]



# =====================================
# EXEC DIRECTO
# =====================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)