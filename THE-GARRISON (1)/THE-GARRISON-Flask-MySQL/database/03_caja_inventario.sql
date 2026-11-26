-- Ejecutar una sola vez después de 01_seguridad_pin.sql y 02_operacion.sql.
-- Añade caja, existencias iniciales vacías y control de consumos por pedido.
USE cantinadb;

CREATE TABLE IF NOT EXISTS existencias_ingrediente (
    id_ingrediente INT NOT NULL,
    existencia DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id_ingrediente),
    CONSTRAINT fk_existencias_ingrediente FOREIGN KEY (id_ingrediente)
        REFERENCES ingredientes (id_ingrediente) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_existencia_no_negativa CHECK (existencia >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO existencias_ingrediente (id_ingrediente, existencia)
SELECT id_ingrediente, 0.00 FROM ingredientes
ON DUPLICATE KEY UPDATE existencia = existencias_ingrediente.existencia;

CREATE TABLE IF NOT EXISTS cajas (
    id_caja INT NOT NULL AUTO_INCREMENT,
    id_empleado_apertura INT NOT NULL,
    id_empleado_cierre INT NULL,
    fondo_inicial DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    efectivo_contado DECIMAL(10,2) NULL,
    efectivo_esperado DECIMAL(10,2) NULL,
    diferencia DECIMAL(10,2) NULL,
    estado ENUM('Abierta','Cerrada') NOT NULL DEFAULT 'Abierta',
    caja_abierta TINYINT GENERATED ALWAYS AS (CASE WHEN estado = 'Abierta' THEN 1 ELSE NULL END) STORED,
    fecha_apertura DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_cierre DATETIME NULL,
    PRIMARY KEY (id_caja),
    UNIQUE KEY uk_caja_unica_abierta (caja_abierta),
    KEY idx_cajas_fecha_apertura (fecha_apertura),
    CONSTRAINT fk_cajas_apertura FOREIGN KEY (id_empleado_apertura)
        REFERENCES empleados (id_empleado) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_cajas_cierre FOREIGN KEY (id_empleado_cierre)
        REFERENCES empleados (id_empleado) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_caja_fondo_no_negativo CHECK (fondo_inicial >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS caja_pagos (
    id_pago INT NOT NULL,
    id_caja INT NOT NULL,
    PRIMARY KEY (id_pago),
    KEY idx_caja_pagos_caja (id_caja),
    CONSTRAINT fk_caja_pagos_pago FOREIGN KEY (id_pago)
        REFERENCES pagos (id_pago) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_caja_pagos_caja FOREIGN KEY (id_caja)
        REFERENCES cajas (id_caja) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS consumos_pedido (
    id_pedido INT NOT NULL,
    id_ingrediente INT NOT NULL,
    cantidad DECIMAL(12,2) NOT NULL,
    revertido TINYINT(1) NOT NULL DEFAULT 0,
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_pedido, id_ingrediente),
    CONSTRAINT fk_consumos_pedido FOREIGN KEY (id_pedido)
        REFERENCES pedidos (id_pedido) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_consumos_ingrediente FOREIGN KEY (id_ingrediente)
        REFERENCES ingredientes (id_ingrediente) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_consumos_cantidad CHECK (cantidad > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
