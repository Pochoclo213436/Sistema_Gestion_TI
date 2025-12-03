import psycopg2
import os
from urllib.parse import urlparse

def run_migrations():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL no está disponible en Render")

    # Parsear la URL
    url = urlparse(database_url)

    conn = psycopg2.connect(
        host=url.hostname,
        port=url.port,
        database=url.path[1:],  # remove leading /
        user=url.username,
        password=url.password
    )

    cur = conn.cursor()

    schema_path = os.path.join("/app", "database", "schema.sql")

    with open(schema_path, "r", encoding="utf-8") as file:
        sql = file.read()
        cur.execute(sql)

    conn.commit()
    cur.close()
    conn.close()

    print("Base de datos inicializada correctamente")

if __name__ == "__main__":
    run_migrations()