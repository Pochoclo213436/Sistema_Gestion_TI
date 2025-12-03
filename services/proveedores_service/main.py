from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncpg
import os
from datetime import date

app = FastAPI(title="Proveedores Service", version="1.0.0")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no está configurada para proveedores_service")     

# Pool global para evitar demasiadas conexiones
pool: asyncpg.Pool | None = None

@app.on_event("startup")
async def on_startup():
    global pool
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL no está configurada")
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)

@app.on_event("shutdown")
async def on_shutdown():
    global pool
    if pool is not None:
        await pool.close()
        pool = None

async def get_db_pool() -> asyncpg.Pool:
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    return pool

class ProveedorCreate(BaseModel):
    razon_social: str
    ruc: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    contacto_nombre: Optional[str] = None
    contacto_telefono: Optional[str] = None
    sitio_web: Optional[str] = None
    notas: Optional[str] = None

class ProveedorUpdate(BaseModel):
    razon_social: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    contacto_nombre: Optional[str] = None
    contacto_telefono: Optional[str] = None
    sitio_web: Optional[str] = None
    calificacion: Optional[float] = None
    activo: Optional[bool] = None
    notas: Optional[str] = None

class ContratoCreate(BaseModel):
    proveedor_id: int
    numero_contrato: str
    tipo: str
    fecha_inicio: date
    fecha_fin: date
    monto_total: Optional[float] = None
    descripcion: Optional[str] = None

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "proveedores"}

@app.get("/proveedores")
async def get_proveedores(activo: Optional[bool] = None):
    pool = await get_db_pool()
    
    query = "SELECT * FROM proveedores"
    params = []
    
    if activo is not None:
        query += " WHERE activo = $1"
        params.append(activo)
    
    query += " ORDER BY razon_social"
    
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]

@app.get("/proveedores/{proveedor_id}")
async def get_proveedor(proveedor_id: int):
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        proveedor = await conn.fetchrow(
            "SELECT * FROM proveedores WHERE id = $1",
            proveedor_id
        )
        
        if not proveedor:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        
        resultado = dict(proveedor)
        
        equipos = await conn.fetch(
            """
            SELECT COUNT(*) as total, 
                   SUM(costo_compra) as total_comprado
            FROM equipos 
            WHERE proveedor_id = $1
            """,
            proveedor_id
        )
        resultado['estadisticas_compras'] = dict(equipos[0])
        
        contratos = await conn.fetch(
            """
            SELECT * FROM contratos 
            WHERE proveedor_id = $1 
            ORDER BY fecha_inicio DESC
            """,
            proveedor_id
        )
        resultado['contratos'] = [dict(c) for c in contratos]
        
        return resultado

@app.post("/proveedores")
async def create_proveedor(proveedor: ProveedorCreate):
    pool = await get_db_pool()
    
    query = """
        INSERT INTO proveedores (
            razon_social, ruc, direccion, telefono, email,
            contacto_nombre, contacto_telefono, sitio_web, notas
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING id
    """
    
    async with pool.acquire() as conn:
        try:
            proveedor_id = await conn.fetchval(
                query,
                proveedor.razon_social,
                proveedor.ruc,
                proveedor.direccion,
                proveedor.telefono,
                proveedor.email,
                proveedor.contacto_nombre,
                proveedor.contacto_telefono,
                proveedor.sitio_web,
                proveedor.notas
            )
            return {"id": proveedor_id, "message": "Proveedor creado exitosamente"}
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="El RUC ya está registrado")

@app.put("/proveedores/{proveedor_id}")
async def update_proveedor(proveedor_id: int, proveedor: ProveedorUpdate):
    pool = await get_db_pool()
    
    updates = []
    params = []
    param_count = 1
    
    for field, value in proveedor.dict(exclude_unset=True).items():
        updates.append(f"{field} = ${param_count}")
        params.append(value)
        param_count += 1
    
    if not updates:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")
    
    params.append(proveedor_id)
    query = f"UPDATE proveedores SET {', '.join(updates)} WHERE id = ${param_count}"
    
    async with pool.acquire() as conn:
        result = await conn.execute(query, *params)
        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        
        return {"message": "Proveedor actualizado exitosamente"}

@app.get("/contratos")
async def get_contratos(proveedor_id: Optional[int] = None):
    pool = await get_db_pool()
    
    query = """
        SELECT c.*, p.razon_social as proveedor_nombre
        FROM contratos c
        JOIN proveedores p ON c.proveedor_id = p.id
    """
    params = []
    
    if proveedor_id:
        query += " WHERE c.proveedor_id = $1"
        params.append(proveedor_id)
    
    query += " ORDER BY c.fecha_inicio DESC"
    
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]

@app.post("/contratos")
async def create_contrato(contrato: ContratoCreate):
    pool = await get_db_pool()
    
    query = """
        INSERT INTO contratos (
            proveedor_id, numero_contrato, tipo, fecha_inicio, fecha_fin,
            monto_total, estado, descripcion
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id
    """
    
    estado = "vigente" if contrato.fecha_fin >= date.today() else "vencido"
    
    async with pool.acquire() as conn:
        try:
            contrato_id = await conn.fetchval(
                query,
                contrato.proveedor_id,
                contrato.numero_contrato,
                contrato.tipo,
                contrato.fecha_inicio,
                contrato.fecha_fin,
                contrato.monto_total,
                estado,
                contrato.descripcion
            )
            return {"id": contrato_id, "message": "Contrato creado exitosamente"}
        except asyncpg.ForeignKeyViolationError:
            raise HTTPException(status_code=400, detail="Proveedor no existe")
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="El número de contrato ya existe")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)