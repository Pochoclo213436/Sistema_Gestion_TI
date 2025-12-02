-- Tabla de categorias de equipos
CREATE TABLE categorias_equipos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    fecha_registro TIMESTAMP DEFAULT NOW(),
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla de usuarios
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre_completo VARCHAR(200) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    rol VARCHAR(50) NOT NULL DEFAULT 'usuario',
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro TIMESTAMP DEFAULT NOW()
);

-- Tabla de proveedores
CREATE TABLE proveedores (
    id SERIAL PRIMARY KEY,
    razon_social VARCHAR(100) NOT NULL,
    ruc VARCHAR(20) UNIQUE,
    direccion TEXT,
    telefono VARCHAR(50),
    email VARCHAR(100),
    contacto_nombre VARCHAR(100),
    contacto_telefono VARCHAR(50),
    sitio_web VARCHAR(100),
    calificacion DECIMAL(3,2), -- Por ejemplo, de 1.00 a 5.00
    activo BOOLEAN DEFAULT TRUE,
    notas TEXT,
    fecha_registro TIMESTAMP DEFAULT NOW()
);

-- Tabla de ubicaciones
CREATE TABLE ubicaciones (
    id SERIAL PRIMARY KEY,
    edificio VARCHAR(100) NOT NULL,
    aula_oficina VARCHAR(100) NOT NULL,
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE,
    CONSTRAINT unique_ubicacion UNIQUE (edificio, aula_oficina)
);

-- Tabla de equipos
CREATE TABLE equipos (
    id SERIAL PRIMARY KEY,
    codigo_inventario VARCHAR(50) NOT NULL UNIQUE,
    categoria_id INT REFERENCES categorias_equipos(id),
    nombre VARCHAR(100),
    marca VARCHAR(100),
    modelo VARCHAR(100),
    numero_serie VARCHAR(100) UNIQUE,
    especificaciones JSONB,
    proveedor_id INT REFERENCES proveedores(id),
    fecha_compra DATE,
    costo_compra DECIMAL(10,2),
    fecha_garantia_fin DATE,
    ubicacion_actual_id INT REFERENCES ubicaciones(id),
    estado_operativo VARCHAR(50) DEFAULT 'operativo',
    estado_fisico VARCHAR(50) DEFAULT 'bueno',
    asignado_a_id INT REFERENCES usuarios(id),
    notas TEXT,
    imagen_url TEXT,
    fecha_registro TIMESTAMP DEFAULT NOW()
);

-- Tabla de movimientos de equipos
CREATE TABLE movimientos_equipos (
    id SERIAL PRIMARY KEY,
    equipo_id INT REFERENCES equipos(id),
    ubicacion_origen_id INT REFERENCES ubicaciones(id),
    ubicacion_destino_id INT REFERENCES ubicaciones(id),
    usuario_responsable_id INT REFERENCES usuarios(id),
    fecha_movimiento TIMESTAMP DEFAULT NOW(),
    motivo TEXT,
    observaciones TEXT
);

-- Tabla de mantenimientos
CREATE TABLE mantenimientos (
    id SERIAL PRIMARY KEY,
    equipo_id INT REFERENCES equipos(id),
    fecha_registro TIMESTAMP DEFAULT NOW(),
    fecha_programada DATE,
    fecha_realizada DATE,
    tipo VARCHAR(50),
    descripcion TEXT,
    costo DECIMAL(10,2),
    estado VARCHAR(50) DEFAULT 'programado', -- programado, en_proceso, completado, cancelado
    prioridad VARCHAR(50) DEFAULT 'media' -- urgente, alta, media, baja
);

-- Tabla de contratos
CREATE TABLE contratos (
    id SERIAL PRIMARY KEY,
    proveedor_id INT REFERENCES proveedores(id),
    numero_contrato VARCHAR(100) NOT NULL UNIQUE,
    tipo VARCHAR(50),
    fecha_inicio DATE,
    fecha_fin DATE,
    monto_total DECIMAL(10,2),
    descripcion TEXT,
    estado VARCHAR(50) DEFAULT 'vigente', -- vigente, vencido, cancelado
    fecha_registro TIMESTAMP DEFAULT NOW()
);

-- Tabla de notificaciones
CREATE TABLE notificaciones (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    mensaje TEXT NOT NULL,
    leida BOOLEAN DEFAULT FALSE,
    fecha TIMESTAMP DEFAULT NOW()
);
