-- =============================================================================
-- PROYECTO DOPA (Aplicación de Apoyo para Personas con TDAH)
-- Agente Responsable: 3.1. Agente Arquitecto de Datos (Database & ORM Agent)
-- Fuente de Verdad: PLANEACIÓN Y DISEÑO DE SOFTWARE (1).pdf - Sección 4.3
-- Motor: PostgreSQL 16+
-- =============================================================================

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

-- -----------------------------------------------------------------------------
-- 1. TIPOS ENUM PERSONALIZADOS (Sección 4.3)
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'prioridad_tarea') THEN
        CREATE TYPE prioridad_tarea AS ENUM ('Alta', 'Media', 'Baja');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_recordatorio') THEN
        CREATE TYPE tipo_recordatorio AS ENUM ('Tarea', 'Rutina', 'Compromiso');
    END IF;
END$$;

-- -----------------------------------------------------------------------------
-- 2. DEFINICIÓN DE LAS 10 TABLAS DEL ESQUEMA RELACIONAL (Sección 4.3, págs. 50-56)
-- -----------------------------------------------------------------------------

-- 2.1. Tabla: usuario
CREATE TABLE IF NOT EXISTS usuario (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    correo VARCHAR(150) UNIQUE NOT NULL,
    contrasenahash VARCHAR(255) NOT NULL,
    puntos INT4 NOT NULL DEFAULT 0 CHECK (puntos >= 0),
    nivel INT4 NOT NULL DEFAULT 1 CHECK (nivel >= 1)
);

-- 2.2. Tabla: rutina
CREATE TABLE IF NOT EXISTS rutina (
    id SERIAL PRIMARY KEY,
    id_usuario INT4 NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    nombre VARCHAR(150) NOT NULL,
    recurrencia VARCHAR(100) NOT NULL,
    hora TIME NOT NULL,
    completadahoy BOOL NOT NULL DEFAULT FALSE
);

-- 2.3. Tabla: tarea
CREATE TABLE IF NOT EXISTS tarea (
    id SERIAL PRIMARY KEY,
    id_usuario INT4 NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    id_rutina INT4 NULL REFERENCES rutina(id) ON DELETE SET NULL,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT,
    prioridad prioridad_tarea NOT NULL DEFAULT 'Media',
    fechavencimiento DATE,
    completada BOOL NOT NULL DEFAULT FALSE
);

-- 2.4. Tabla: subtarea (Micro-pasos para reducir la parálisis por análisis - HU-03)
CREATE TABLE IF NOT EXISTS subtarea (
    id SERIAL PRIMARY KEY,
    id_tarea INT4 NOT NULL REFERENCES tarea(id) ON DELETE CASCADE,
    descripcion VARCHAR(255) NOT NULL,
    completada BOOL NOT NULL DEFAULT FALSE
);

-- 2.5. Tabla: sesionpomodoro (Enfoque suave y pausas guiadas - HU-06)
CREATE TABLE IF NOT EXISTS sesionpomodoro (
    id SERIAL PRIMARY KEY,
    id_usuario INT4 NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    id_tarea INT4 NULL REFERENCES tarea(id) ON DELETE SET NULL,
    duracionconcentracion INT4 NOT NULL CHECK (duracionconcentracion > 0),
    duraciondescanso INT4 NOT NULL CHECK (duraciondescanso >= 0),
    sesionescompletadas INT4 NOT NULL DEFAULT 0 CHECK (sesionescompletadas >= 0)
);

-- 2.6. Tabla: recordatorio (Alertas de tareas, rutinas y compromisos - HU-05)
CREATE TABLE IF NOT EXISTS recordatorio (
    id SERIAL PRIMARY KEY,
    id_usuario INT4 NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    id_tarea INT4 NULL REFERENCES tarea(id) ON DELETE CASCADE,
    fechahora TIMESTAMP NOT NULL,
    mensaje VARCHAR(255) NOT NULL,
    tipo tipo_recordatorio NOT NULL DEFAULT 'Tarea',
    completadahoy BOOL NOT NULL DEFAULT FALSE
);

-- 2.7. Tabla: recompensa (Gamificación de dopamina libre de culpa - HU-07)
CREATE TABLE IF NOT EXISTS recompensa (
    id SERIAL PRIMARY KEY,
    id_tarea INT4 NULL REFERENCES tarea(id) ON DELETE SET NULL,
    nombre VARCHAR(150) NOT NULL,
    costopuntos INT4 NOT NULL DEFAULT 10 CHECK (costopuntos >= 0),
    desbloqueada BOOL NOT NULL DEFAULT FALSE
);

-- 2.8. Tabla: registropersonal (Seguimiento de sueño, energía y humor - HU-08)
CREATE TABLE IF NOT EXISTS registropersonal (
    id SERIAL PRIMARY KEY,
    id_usuario INT4 NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    nombre VARCHAR(120) NOT NULL,
    valorobjetivo NUMERIC(10,2) NOT NULL CHECK (valorobjetivo > 0),
    valoractual NUMERIC(10,2) NOT NULL DEFAULT 0,
    progresoporcentaje NUMERIC(5,2) NOT NULL DEFAULT 0
);

-- 2.9. Tabla: metafinanciera (Metas de ahorro y control de gastos - HU-09)
CREATE TABLE IF NOT EXISTS metafinanciera (
    id SERIAL PRIMARY KEY,
    id_usuario INT4 NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    nombre VARCHAR(150) NOT NULL,
    valorobjetivo NUMERIC(12,2) NOT NULL CHECK (valorobjetivo > 0),
    valoractual NUMERIC(12,2) NOT NULL DEFAULT 0,
    progresoporcentaje NUMERIC(5,2) NOT NULL DEFAULT 0
);

-- 2.10. Tabla: panelprincipal (Snapshot diario del Dashboard - HU-10)
CREATE TABLE IF NOT EXISTS panelprincipal (
    id SERIAL PRIMARY KEY,
    id_usuario INT4 NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    fechaactual DATE NOT NULL DEFAULT CURRENT_DATE
);

-- -----------------------------------------------------------------------------
-- 3. ÍNDICES DE OPTIMIZACIÓN (Cumplimiento de RNF-04 <= 2s y RNF-17)
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_usuario_correo ON usuario(correo);

CREATE INDEX IF NOT EXISTS idx_rutina_usuario ON rutina(id_usuario);
CREATE INDEX IF NOT EXISTS idx_rutina_usuario_completada ON rutina(id_usuario, completadahoy);

CREATE INDEX IF NOT EXISTS idx_tarea_usuario ON tarea(id_usuario);
CREATE INDEX IF NOT EXISTS idx_tarea_rutina ON tarea(id_rutina);
CREATE INDEX IF NOT EXISTS idx_tarea_usuario_estado_prioridad ON tarea(id_usuario, completada, prioridad);
CREATE INDEX IF NOT EXISTS idx_tarea_fechavencimiento ON tarea(fechavencimiento);

CREATE INDEX IF NOT EXISTS idx_subtarea_tarea ON subtarea(id_tarea);

CREATE INDEX IF NOT EXISTS idx_sesionpomodoro_usuario ON sesionpomodoro(id_usuario);
CREATE INDEX IF NOT EXISTS idx_sesionpomodoro_tarea ON sesionpomodoro(id_tarea);

CREATE INDEX IF NOT EXISTS idx_recordatorio_usuario_fechahora ON recordatorio(id_usuario, fechahora);
CREATE INDEX IF NOT EXISTS idx_recordatorio_tarea ON recordatorio(id_tarea);

CREATE INDEX IF NOT EXISTS idx_recompensa_tarea ON recompensa(id_tarea);
CREATE INDEX IF NOT EXISTS idx_recompensa_desbloqueada ON recompensa(desbloqueada);

CREATE INDEX IF NOT EXISTS idx_registropersonal_usuario ON registropersonal(id_usuario);
CREATE INDEX IF NOT EXISTS idx_metafinanciera_usuario ON metafinanciera(id_usuario);
CREATE INDEX IF NOT EXISTS idx_panelprincipal_usuario_fecha ON panelprincipal(id_usuario, fechaactual);

-- -----------------------------------------------------------------------------
-- 4. SEEDERS (Datos de Prueba Realistas basados en Parcial 2.pdf - App DOPA)
-- -----------------------------------------------------------------------------
-- Nota: El hash corresponde a la contraseña de prueba "Dopa1234!" en formato bcrypt
INSERT INTO usuario (id, nombre, correo, contrasenahash, puntos, nivel)
VALUES
    (1, 'Fred', 'fred@dopa.app', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 32, 1),
    (2, 'Paula', 'paula@dopa.app', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 55, 2)
ON CONFLICT (correo) DO NOTHING;

SELECT setval('usuario_id_seq', (SELECT COALESCE(MAX(id), 1) FROM usuario));

-- Rutinas inspiradas en Figura 2, Figura 4 y Figura 5 de Parcial 2.pdf
INSERT INTO rutina (id, id_usuario, nombre, recurrencia, hora, completadahoy)
VALUES
    (1, 1, 'Mi rutina de hoy (Mañana suave)', 'Diaria', '08:00:00', FALSE),
    (2, 1, 'Tiempo para ti - Pausa guiada 5 min', 'Diaria', '11:00:00', TRUE),
    (3, 2, 'Rutina de cierre nocturno sin pantallas', 'Lunes a Viernes', '21:30:00', FALSE)
ON CONFLICT (id) DO NOTHING;

SELECT setval('rutina_id_seq', (SELECT COALESCE(MAX(id), 1) FROM rutina));

-- Tareas inspiradas en Figura 2, Figura 3, Figura 7, Figura 8 y Figura 9 de Parcial 2.pdf
INSERT INTO tarea (id, id_usuario, id_rutina, titulo, descripcion, prioridad, fechavencimiento, completada)
VALUES
    (1, 1, 1, 'Hacer la cama', 'Un solo paso pequeño basta para empezar el día con calma.', 'Media', CURRENT_DATE, FALSE),
    (2, 1, 1, 'Poner un vaso de agua cerca', 'Hidratación suave antes de revisar el teléfono.', 'Baja', CURRENT_DATE, TRUE),
    (3, 1, 1, 'Preparar la botella', 'Llenar la botella de agua para el escritorio.', 'Baja', CURRENT_DATE, TRUE),
    (4, 1, NULL, 'Responder a Ana', 'Enviar confirmación breve sobre la reunión de mañana.', 'Alta', CURRENT_DATE, FALSE),
    (5, 1, NULL, 'Guardar la ropa', 'Doblar solo las prendas que están sobre la silla.', 'Media', CURRENT_DATE + INTERVAL '1 day', FALSE),
    (6, 2, 3, 'Preparar mochila del día siguiente', 'Dejar llaves y libreta listas en la entrada.', 'Media', CURRENT_DATE, FALSE)
ON CONFLICT (id) DO NOTHING;

SELECT setval('tarea_id_seq', (SELECT COALESCE(MAX(id), 1) FROM tarea));

-- Subtareas (Micro-pasos) inspiradas en Figura 9 ("Enfoque suave: Hacer la cama")
INSERT INTO subtarea (id, id_tarea, descripcion, completada)
VALUES
    (1, 1, '1. Estirar las sábanas', TRUE),
    (2, 1, '2. Colocar almohadas', FALSE),
    (3, 4, '1. Abrir el chat de Ana', TRUE),
    (4, 4, '2. Escribir respuesta de 2 líneas y enviar', FALSE),
    (5, 5, '1. Separar camisetas de pantalones', FALSE),
    (6, 5, '2. Guardar en el primer cajón', FALSE)
ON CONFLICT (id) DO NOTHING;

SELECT setval('subtarea_id_seq', (SELECT COALESCE(MAX(id), 1) FROM subtarea));

-- Sesiones Pomodoro inspiradas en Figura 4, Figura 9 y Figura 12 (5 min enfoque / 5 min descanso)
INSERT INTO sesionpomodoro (id, id_usuario, id_tarea, duracionconcentracion, duraciondescanso, sesionescompletadas)
VALUES
    (1, 1, 1, 5, 5, 2),
    (2, 1, 4, 15, 5, 1),
    (3, 2, 6, 25, 5, 3)
ON CONFLICT (id) DO NOTHING;

SELECT setval('sesionpomodoro_id_seq', (SELECT COALESCE(MAX(id), 1) FROM sesionpomodoro));

-- Recordatorios inspirados en Figura 2 (Alertas amigables)
INSERT INTO recordatorio (id, id_usuario, id_tarea, fechahora, mensaje, tipo, completadahoy)
VALUES
    (1, 1, 1, CURRENT_TIMESTAMP + INTERVAL '30 minutes', 'Poquito a poquito: termina el paso 2 de Hacer la cama', 'Tarea', FALSE),
    (2, 1, NULL, CURRENT_TIMESTAMP + INTERVAL '2 hours', 'Un break suave: Respiración 4-4 por 1 minuto', 'Rutina', FALSE),
    (3, 1, 4, CURRENT_TIMESTAMP + INTERVAL '4 hours', 'Recuerda responder a Ana sin presiones', 'Compromiso', FALSE)
ON CONFLICT (id) DO NOTHING;

SELECT setval('recordatorio_id_seq', (SELECT COALESCE(MAX(id), 1) FROM recordatorio));

-- Recompensas inspiradas en Figura 6, Figura 10 (+10 dopamina) y Figura 11 ("Mi Dopamina hoy")
INSERT INTO recompensa (id, id_tarea, nombre, costopuntos, desbloqueada)
VALUES
    (1, 2, 'Insignia: Primer paso del día (+10 dopamina)', 10, TRUE),
    (2, 1, 'Pausa libre: Escuchar tu canción favorita sin culpa', 20, TRUE),
    (3, 4, 'Desbloqueo: Episodio de serie o 15 min de hobby', 50, FALSE),
    (4, NULL, 'Racha amable: 3 días avanzando a tu propio ritmo', 100, FALSE)
ON CONFLICT (id) DO NOTHING;

SELECT setval('recompensa_id_seq', (SELECT COALESCE(MAX(id), 1) FROM recompensa));

-- Registros Personales inspirados en Figura 6 ("Sueño 6.8 h", "Energía Alta") y Figura 11 ("Estado emocional: Con foco")
INSERT INTO registropersonal (id, id_usuario, nombre, valorobjetivo, valoractual, progresoporcentaje)
VALUES
    (1, 1, 'Horas de sueño', 8.00, 6.80, 85.00),
    (2, 1, 'Estado emocional: Con foco', 5.00, 4.00, 80.00),
    (3, 1, 'Energía diaria: Alta', 10.00, 8.00, 80.00),
    (4, 2, 'Horas de sueño', 8.00, 7.50, 93.75)
ON CONFLICT (id) DO NOTHING;

SELECT setval('registropersonal_id_seq', (SELECT COALESCE(MAX(id), 1) FROM registropersonal));

-- Metas Financieras (HU-09, RF-20, RF-21)
INSERT INTO metafinanciera (id, id_usuario, nombre, valorobjetivo, valoractual, progresoporcentaje)
VALUES
    (1, 1, 'Fondo de tranquilidad (Colchón de imprevistos)', 500.00, 175.00, 35.00),
    (2, 1, 'Auriculares con cancelación de ruido para enfoque', 120.00, 90.00, 75.00),
    (3, 2, 'Ahorro mensual libre de compras impulsivas', 300.00, 150.00, 50.00)
ON CONFLICT (id) DO NOTHING;

SELECT setval('metafinanciera_id_seq', (SELECT COALESCE(MAX(id), 1) FROM metafinanciera));

-- Panel Principal (HU-10, RF-22)
INSERT INTO panelprincipal (id, id_usuario, fechaactual)
VALUES
    (1, 1, CURRENT_DATE),
    (2, 2, CURRENT_DATE)
ON CONFLICT (id) DO NOTHING;

SELECT setval('panelprincipal_id_seq', (SELECT COALESCE(MAX(id), 1) FROM panelprincipal));
