from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx

app = FastAPI(title="API Gateway", version="1.0.0")

# ==========================
# Definición de servicios
# ==========================
SERVICES = {
    "equipos": "https://equipos-service-oy17.onrender.com",
    "proveedores": "https://proveedores-service-cgvs.onrender.com",
    "mantenimiento": "https://mantenimiento-service-onrender.com",
    "reportes": "https://reportes-service-e03k.onrender.com",
    "agent": "https://agent-service-odqo.onrender.com",
}

# ==========================
# Ruta raíz
# ==========================
@app.get("/")
def root():
    return {"message": "API Gateway funcionando"}

# ==========================
# Proxy a los microservicios
# ==========================
@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway(service: str, path: str, request: Request):
    if service not in SERVICES:
        return JSONResponse(content={"detail": f"Servicio '{service}' no encontrado"}, status_code=404)

    target_url = f"{SERVICES[service]}/{path}"

    async with httpx.AsyncClient() as client:
        # Extraer cuerpo de la solicitud
        body = await request.body()

        # Filtrar headers, evitando conflictos
        headers = {k: v for k, v in request.headers.items() if k.lower() not in ["content-length", "host"]}

        try:
            # Enviar solicitud al microservicio
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=request.query_params,
                timeout=30  # timeout opcional
            )

            # Intentar parsear JSON
            try:
                data = response.json()
            except Exception:
                return JSONResponse(
                    content={"detail": "El microservicio no devolvió JSON válido", "raw": response.text},
                    status_code=500
                )

            return JSONResponse(content=data, status_code=response.status_code)

        except httpx.RequestError as exc:
            return JSONResponse(
                content={"detail": f"No se pudo conectar con el microservicio '{service}'", "error": str(exc)},
                status_code=500
            )

        except Exception as exc:
            return JSONResponse(
                content={"detail": "Error inesperado en el Gateway", "error": str(exc)},
                status_code=500
            )
