-- ============================================
-- ARCHIVO 1/10: ESQUEMA DE BASE DE DATOS
-- ============================================
-- Este archivo crea la base de datos y las tablas
-- Ejecútalo en SQLyog para tener la BD lista
-- ============================================

-- Crear la base de datos (si no existe)
CREATE DATABASE IF NOT EXISTS learnify_db;
USE learnify_db;

-- ============================================
-- TABLA: usuarios
-- Guarda la información de maestros y alumnos
-- ============================================
CREATE TABLE usuarios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,  -- Aquí irá la contraseña encriptada
    rol ENUM('maestro', 'alumno') NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- DATOS DE PRUEBA (opcional)
-- ============================================
-- Insertamos dos usuarios de prueba con contraseña '123456' (encriptada en SHA256)
-- El hash de '123456' es: 8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92
INSERT INTO usuarios (nombre, email, password, rol) VALUES 
('Profesor Juan', 'juan@test.com', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'maestro'),
('Ana Alumna', 'ana@test.com', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'alumno');

-- ============================================
-- VERIFICAR QUE SE CREÓ BIEN
-- ============================================
-- SELECT * FROM usuarios;


-- ============================================
-- ARCHIVO 11/20: AGREGAR TABLAS DE EQUIPOS
-- ============================================

USE learnify_db;

-- ============================================
-- TABLA 1: equipos
-- Almacena los equipos creados por los maestros
-- ============================================
CREATE TABLE IF NOT EXISTS equipos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    -- id: número único para cada equipo
    
    nombre VARCHAR(100) NOT NULL,
    -- nombre: el nombre del equipo (Ej: "Equipo Verde")
    
    descripcion TEXT,
    -- descripcion: qué hace el equipo (opcional)
    
    lider_id INT NOT NULL,
    -- lider_id: el ID del maestro que creó el equipo
    -- Relaciona con la tabla usuarios
    
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- fecha_creacion: cuándo se creó el equipo
    
    FOREIGN KEY (lider_id) REFERENCES usuarios(id) ON DELETE CASCADE
    -- Si se borra un maestro, se borran sus equipos
);

-- ============================================
-- TABLA 2: equipo_miembros
-- Relaciona alumnos con equipos (muchos a muchos)
-- ============================================
CREATE TABLE IF NOT EXISTS equipo_miembros (
    equipo_id INT NOT NULL,
    -- equipo_id: qué equipo
    
    usuario_id INT NOT NULL,
    -- usuario_id: qué alumno pertenece
    
    fecha_union TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- fecha_union: cuándo se unió
    
    PRIMARY KEY (equipo_id, usuario_id),
    -- Un alumno no puede estar dos veces en el mismo equipo
    
    FOREIGN KEY (equipo_id) REFERENCES equipos(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- ============================================
-- VERIFICAR QUE SE CREARON
-- ============================================
SHOW TABLES;
-- Deberías ver: equipos, equipo_miembros, usuarios

-- ============================================
-- ARCHIVO 18/30: AGREGAR TABLAS DE TAREAS Y ENTREGAS
-- ============================================
-- Ejecuta esto en SQLyog para agregar las nuevas tablas
-- ============================================

USE learnify_db;

-- ============================================
-- TABLA 1: tareas
-- Almacena las tareas creadas en cada equipo
-- ============================================
CREATE TABLE IF NOT EXISTS tareas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT,
    equipo_id INT NOT NULL,
    creador_id INT NOT NULL,  -- Quién creó la tarea (maestro o líder)
    fecha_limite DATE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipo_id) REFERENCES equipos(id) ON DELETE CASCADE,
    FOREIGN KEY (creador_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- ============================================
-- TABLA 2: entregas
-- Almacena las entregas de los alumnos
-- ============================================
CREATE TABLE IF NOT EXISTS entregas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tarea_id INT NOT NULL,
    alumno_id INT NOT NULL,
    comentario TEXT,
    archivo VARCHAR(255),  -- Ruta del archivo subido
    calificacion INT,      -- NULL si no calificada
    fecha_entrega TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tarea_id) REFERENCES tareas(id) ON DELETE CASCADE,
    FOREIGN KEY (alumno_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_entrega (tarea_id, alumno_id)  -- Un alumno solo una entrega por tarea
);

-- ============================================
-- VERIFICAR TABLAS CREADAS
-- ============================================
SHOW TABLES;
-- Deberías ver: equipos, equipo_miembros, entregas, tareas, usuarios


-- ============================================
-- FASE 4: AGREGAR TABLA DE CHAT Y ARCHIVOS
-- ============================================

USE learnify_db;

-- ============================================
-- TABLA: mensajes_chat
-- Guarda los mensajes de cada equipo
-- ============================================
CREATE TABLE IF NOT EXISTS mensajes_chat (
    id INT PRIMARY KEY AUTO_INCREMENT,
    equipo_id INT NOT NULL,
    usuario_id INT NOT NULL,
    mensaje TEXT NOT NULL,
    fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipo_id) REFERENCES equipos(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- ============================================
-- MODIFICAR TABLA entregas: agregar archivo
-- ============================================
-- Si la columna archivo no existe, la agregamos
ALTER TABLE entregas ADD COLUMN IF NOT EXISTS archivo VARCHAR(255) NULL;
ALTER TABLE entregas ADD COLUMN IF NOT EXISTS nombre_archivo VARCHAR(255) NULL;

-- ============================================
-- VERIFICAR
-- ============================================
SHOW TABLES;
SHOW COLUMNS FROM entregas;

-- ============================================
-- MONGODB: CREAR BASE DE DATOS Y COLECCIONES
// ============================================
// CREAR COLECCIONES PARA DUALES Y ESTADÍAS
// ============================================

// Colección: duales
db.createCollection("duales");

// Colección: estadias
db.createCollection("estadias");

// ============================================
// ÍNDICES PARA BÚSQUEDAS
// ============================================
db.duales.createIndex({ usuario_id: 1 });
db.duales.createIndex({ estado: 1 });
db.estadias.createIndex({ usuario_id: 1 });
db.estadias.createIndex({ estado: 1 });

// ============================================
// DOCUMENTO DE EJEMPLO PARA DUAL
// ============================================
// {
//   "_id": ObjectId,
//   "usuario_id": ObjectId,
//   "titulo": "Desarrollo Frontend",
//   "empresa": "Tech Solutions",
//   "descripcion": "Desarrollo de interfaces web",
//   "fecha_inicio": ISODate("2026-01-15"),
//   "fecha_fin": ISODate("2026-07-15"),
//   "horas": 480,
//   "tutor": "Ing. María González",
//   "estado": "activo",
//   "fecha_creacion": ISODate()
// }

// ============================================
// DOCUMENTO DE EJEMPLO PARA ESTADÍA
// ============================================
// {
//   "_id": ObjectId,
//   "usuario_id": ObjectId,
//   "titulo": "Desarrollo de Software",
//   "empresa": "SoftTech México",
//   "descripcion": "Desarrollo de aplicaciones web",
//   "fecha_inicio": ISODate("2026-01-10"),
//   "fecha_fin": ISODate("2026-06-10"),
//   "horas": 600,
//   "ubicacion": "Ciudad de México",
//   "tutor": "Ing. Carlos Ramírez",
//   "estado": "en-curso",
//   "fecha_creacion": ISODate()
// }