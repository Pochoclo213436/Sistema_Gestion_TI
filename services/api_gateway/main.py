from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
import httpx

app = FastAPI(title="API Gateway", version="1.0.0")

SERVICES = {
    "equipos": "https://equipos-service-oy17.onrender.com",
    "proveedores": "https://proveedores-service-cgvs.onrender.com",
    "mantenimiento": "https://mantenimiento-service.onrender.com",
    "reportes": "https://reportes-service-e03k.onrender.com",
    "agent": "https://agent-service-odqo.onrender.com",
}

# Endpoints que devuelven archivos binarios
BINARY_ENDPOINTS = [
    "/reportes/export/excel",
    "/reportes/export/pdf",
    "/reportes/export/file"
]

@app.get("/")
def root():
    return {"message": "API Gateway funcionando"}

@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway(service: str, path: str, request: Request):
    if service not in SERVICES:
        return JSONResponse(content={"detail": f"Servicio '{service}' no encontrado"}, status_code=404)

    target_url = f"{SERVICES[service]}/{path}"
    full_path = f"/{service}/{path}"

    async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
        body = await request.body()
        headers = {k: v for k, v in request.headers.items() if k.lower() not in ["content-length", "host"]}
        headers["accept-encoding"] = "gzip, deflate"

        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=request.query_params,
            )

            # Verificar si es un endpoint de archivo binario
            is_binary = any(full_path.startswith(endpoint) for endpoint in BINARY_ENDPOINTS)
            
            # También detectar por content-type
            content_type = response.headers.get("content-type", "")
            is_file = any(ct in content_type.lower() for ct in [
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-excel",
                "application/octet-stream"
            ])

            # Si es un archivo binario, devolver el contenido sin procesarlo
            if is_binary or is_file:
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers={
                        "Content-Type": response.headers.get("Content-Type", "application/octet-stream"),
                        "Content-Disposition": response.headers.get("Content-Disposition", ""),
                        "Content-Length": response.headers.get("Content-Length", str(len(response.content))),
                        "Cache-Control": "no-cache"
                    }
                )

            # Para respuestas normales, intentar parsear JSON
            try:
                data = response.json()
                return JSONResponse(content=data, status_code=response.status_code)
            except Exception:
                # Si no es JSON, devolver como texto
                return Response(
                    content=response.text,
                    media_type=response.headers.get("content-type", "text/plain"),
                    status_code=response.status_code
                )

        except httpx.TimeoutException:
            return JSONResponse(
                content={"detail": f"Timeout al conectar con el microservicio '{service}'"},
                status_code=504
            )
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