-- Ejecutar una sola vez. Conserva la información existente.
-- Permite guardar el mismo producto dos veces en un pedido si lleva extras distintos.
ALTER TABLE detalle_pedido DROP INDEX uk_pedido_presentacion;

INSERT IGNORE INTO presentacion_extras (id_presentacion, id_extra) VALUES
(1,5),(1,6),(2,5),(2,6),(3,5),(3,6),
(5,1),(5,3),(5,4),(5,6),(5,10),
(6,1),(6,3),(6,4),(6,6),(6,10),
(7,1),(7,6),(8,5),(9,5),(10,5),(11,5),(12,5),(12,6),
(13,1),(13,2),(13,3),(13,6),(13,8),
(14,5),(14,6),(14,9),
(15,2),(15,5),(15,6),(15,8),
(16,5),(16,6),(16,7),(16,8),
(17,5),(17,8),(17,11),
(18,5),(18,7),
(19,5),(19,6),(20,5),(20,7),(21,5),(21,8);

CREATE TABLE IF NOT EXISTS pagos (
    id_pago INT NOT NULL AUTO_INCREMENT,
    id_pedido INT NOT NULL,
    id_empleado INT NOT NULL,
    metodo ENUM('Efectivo','Tarjeta','Transferencia','Otro') NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    referencia VARCHAR(100) NULL,
    estado ENUM('Registrado','Reembolsado') NOT NULL DEFAULT 'Registrado',
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_pago),
    KEY idx_pagos_pedido_fecha (id_pedido, fecha),
    CONSTRAINT fk_pagos_pedido FOREIGN KEY (id_pedido)
        REFERENCES pedidos (id_pedido) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_pagos_empleado FOREIGN KEY (id_empleado)
        REFERENCES empleados (id_empleado) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_pagos_monto CHECK (monto > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS movimientos_inventario (
    id_movimiento INT NOT NULL AUTO_INCREMENT,
    id_ingrediente INT NOT NULL,
    id_empleado INT NOT NULL,
    tipo ENUM('Entrada','Consumo','AjustePositivo','AjusteNegativo','Merma') NOT NULL,
    cantidad DECIMAL(10,2) NOT NULL,
    costo_unitario DECIMAL(10,2) NULL,
    referencia VARCHAR(100) NULL,
    notas VARCHAR(255) NULL,
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_movimiento),
    KEY idx_movimientos_ingrediente_fecha (id_ingrediente, fecha),
    KEY idx_movimientos_empleado (id_empleado),
    CONSTRAINT fk_movimientos_ingrediente FOREIGN KEY (id_ingrediente)
        REFERENCES ingredientes (id_ingrediente) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_movimientos_empleado FOREIGN KEY (id_empleado)
        REFERENCES empleados (id_empleado) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_movimientos_cantidad CHECK (cantidad > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- cantidad es positiva; el tipo define si el movimiento suma o resta existencias.
-- La aplicación todavía debe registrar estos movimientos al cobrar/preparar pedidos.
