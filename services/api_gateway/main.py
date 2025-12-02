from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import httpx

app = FastAPI(title="API Gateway", version="1.0.0")

# Rutas internas de servicios
SERVICES = {
    "equipos": "http://equipos-service:8001",
    "proveedores": "http://proveedores-service:8002",
    "mantenimiento": "http://mantenimiento-service:8003",
    "reportes": "http://reportes-service:8004",
    "agent": "http://agent-service:8005",
}

@app.get("/")
def root():
    return {"message": "API Gateway funcionando"}

@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway(service: str, path: str, request: Request):
    if service not in SERVICES:
        return {"detail": f"Servicio '{service}' no encontrado"}, 404

    target_url = f"{SERVICES[service]}/{path}"

    async with httpx.AsyncClient() as client:
        # Extraer el cuerpo de la solicitud original
        body = await request.body()
        
        # Extraer headers, excluyendo Content-Length y Host para evitar conflictos
        headers = {key: value for key, value in request.headers.items() if key.lower() not in ["content-length", "host"]}

        try:
            # Reenviar la solicitud al microservicio correspondiente
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body, # Usar 'content' para enviar el cuerpo raw
                params=request.query_params # Reenviar parámetros de consulta
            )
            # Intentar devolver JSON si es posible
            try:
                data = response.json()
                return JSONResponse(content=data, status_code=response.status_code)
            except ValueError:
                # Si no es JSON válido, pasar el contenido crudo con su content-type original
                content_type = response.headers.get('content-type', 'text/plain')
                return Response(content=response.content, media_type=content_type, status_code=response.status_code)
        except httpx.HTTPStatusError as exc:
            # Manejar errores HTTP del microservicio
            return {"detail": f"Error del microservicio: {exc.response.status_code} - {exc.response.text}"}, exc.response.status_code
        except httpx.RequestError as exc:
            # Manejar errores de red o de conexión
            return {"detail": f"Error de conexión con el microservicio '{service}': {exc}"}, 500
        except Exception as exc:
            # Manejar cualquier otro error inesperado
            return {"detail": f"Error inesperado en el gateway: {exc}"}, 500
