CREATE DATABASE IF NOT EXISTS `cantinadb` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `cantinadb`;

SET FOREIGN_KEY_CHECKS = 0;

-- ------------------------------------------------------
-- Table structure for table `categorias`
-- ------------------------------------------------------
DROP TABLE IF EXISTS `categorias`;
CREATE TABLE `categorias` (
  `id_categoria` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `descripcion` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id_categoria`),
  UNIQUE KEY `uk_categoria_nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `categorias` VALUES 
(1,'Cervezas','Cervezas comerciales'),
(2,'Tequilas','Bebidas destiladas de agave'),
(3,'Rones','Destilados de caña de azúcar'),
(4,'Vodkas','Bebidas destiladas de cereal'),
(5,'Ginebras','Destilados botánicos'),
(6,'Cocteles','Bebidas preparadas y mezcladas'),
(7,'Mixes sin alcohol','Bebidas sin contenido alcohólico'),
(8,'Licores','Bebidas alcohólicas saborizadas');

-- ------------------------------------------------------
-- Table structure for table `bebidas`
-- ------------------------------------------------------
DROP TABLE IF EXISTS `bebidas`;
CREATE TABLE `bebidas` (
  `id_bebida` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `descripcion` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `id_categoria` int NOT NULL,
  `estado` enum('Disponible','No disponible') COLLATE utf8mb4_unicode_ci DEFAULT 'Disponible',
  `imagen_url` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_bebida`),
  UNIQUE KEY `uk_bebida_nombre` (`nombre`),
  KEY `id_categoria` (`id_categoria`),
  CONSTRAINT `bebidas_ibfk_1` FOREIGN KEY (`id_categoria`) REFERENCES `categorias` (`id_categoria`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `bebidas` VALUES 
(1,'Corona','Cerveza lager mexicana',1,'Disponible',NULL,'2026-11-10 00:00:00'),
(2,'Victoria','Cerveza tipo vienna',1,'Disponible',NULL,'2026-11-10 00:00:00'),
(3,'Modelo Especial','Cerveza lager',1,'Disponible',NULL,'2026-11-10 00:00:00'),
(4,'Jose Cuervo Tradicional','Tequila reposado',2,'Disponible',NULL,'2026-11-10 00:00:00'),
(5,'Don Julio Blanco','Tequila blanco',2,'Disponible',NULL,'2026-11-10 00:00:00'),
(6,'Bacardi Carta Blanca','Ron blanco',3,'Disponible',NULL,'2026-11-10 00:00:00'),
(7,'Havana Club 3 Años','Ron blanco cubano',3,'Disponible',NULL,'2026-11-10 00:00:00'),
(8,'Smirnoff No. 21','Vodka clásico',4,'Disponible',NULL,'2026-11-10 00:00:00'),
(9,'Tanqueray London Dry','Ginebra seca',5,'Disponible',NULL,'2026-11-10 00:00:00'),
(10,'Margarita','Cóctel de tequila y cítricos',6,'Disponible',NULL,'2026-11-10 00:00:00'),
(11,'Mojito','Cóctel cubano de ron y hierbabuena',6,'Disponible',NULL,'2026-11-10 00:00:00'),
(12,'Daiquiri','Cóctel de ron y lima',6,'Disponible',NULL,'2026-11-10 00:00:00'),
(13,'Cuba Libre','Ron mezclado con cola y lima',6,'Disponible',NULL,'2026-11-10 00:00:00'),
(14,'Piña Colada','Cóctel tropical de ron y piña',6,'Disponible',NULL,'2026-11-10 00:00:00'),
(15,'Negroni','Cóctel italiano de ginebra',6,'Disponible',NULL,'2026-11-10 00:00:00'),
(16,'Limonada natural','Bebida de limón sin alcohol',7,'Disponible',NULL,'2026-11-10 00:00:00'),
(17,'Naranjada','Bebida de naranja sin alcohol',7,'Disponible',NULL,'2026-11-10 00:00:00'),
(18,'Shirley Temple','Cóctel sin alcohol de granadina',7,'Disponible',NULL,'2026-11-10 00:00:00'),
(19,'Triple Sec','Licor de naranja',8,'Disponible',NULL,'2026-11-10 00:00:00'),
(20,'Campari','Licor aperitivo amargo',8,'Disponible',NULL,'2026-11-10 00:00:00');

-- ------------------------------------------------------
-- Table structure for table `clientes`
-- ------------------------------------------------------
DROP TABLE IF EXISTS `clientes`;
CREATE TABLE `clientes` (
  `id_cliente` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `telefono` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `correo` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_cliente`),
  UNIQUE KEY `uk_cliente_telefono` (`telefono`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `clientes` VALUES 
(1,'Juan Pérez','5512345678','juan@gmail.com','2026-11-10 00:00:00'),
(2,'María López','5523456789','maria@gmail.com','2026-11-10 00:00:00'),
(3,'Carlos Ramírez','5534567890','carlos@gmail.com','2026-11-10 00:00:00'),
(4,'Ana Torres','5545678901','ana@gmail.com','2026-11-10 00:00:00');

-- ------------------------------------------------------
-- Table structure for table `empleados`
-- ------------------------------------------------------
DROP TABLE IF EXISTS `empleados`;
CREATE TABLE `empleados` (
  `id_empleado` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `usuario` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL,
  `pin` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `rol` enum('Mesero','Bartender','Cajero','Gerente') COLLATE utf8mb4_unicode_ci DEFAULT 'Mesero',
  PRIMARY KEY (`id_empleado`),
  UNIQUE KEY `uk_empleado_usuario` (`usuario`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `empleados` (`id_empleado`, `nombre`, `usuario`, `pin`, `rol`) VALUES 
(1,'Roberto Gómez','roberto','1234','Mesero'),
(2,'Lucía Méndez','lucia','1234','Bartender');

-- ------------------------------------------------------
-- Table structure for table `mesas`
-- ------------------------------------------------------
DROP TABLE IF EXISTS `mesas`;
CREATE TABLE `mesas` (
  `id_mesa` int NOT NULL AUTO_INCREMENT,
  `numero_mesa` int NOT NULL,
  `capacidad` int DEFAULT 4,
  `estado` enum('Disponible','Ocupada','Reservada') COLLATE utf8mb4_unicode_ci DEFAULT 'Disponible',
  PRIMARY KEY (`id_mesa`),
  UNIQUE KEY `uk_numero_mesa` (`numero_mesa`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `mesas` VALUES 
(1,1,4,'Ocupada'),
(2,2,2,'Disponible'),
(3,3,6,'Disponible'),
(4,4,4,'Reservada');

-- ------------------------------------------------------
-- Table structure for table `medidas`
-- ------------------------------------------------------
DROP TABLE IF EXISTS `medidas`;
CREATE TABLE `medidas` (
  `id_medida` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `mililitros` int NOT NULL,
  PRIMARY KEY (`id_medida`),
  CONSTRAINT `medidas_chk_1` CHECK ((`mililitros` > 0))
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `medidas` VALUES 
(1,'Caballito',45),
(2,'Medida doble',90),
(3,'Copa pequeña',150),
(4,'Copa mediana',250),
(5,'Copa grande',350),
(6,'Tarro',500),
(7,'Litro',1000);

-- ------------------------------------------------------
-- Table structure for table `vasos`
-- ------------------------------------------------------
DROP TABLE IF EXISTS `vasos`;
CREATE TABLE `vasos` (
  `id_vaso` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `capacidad_ml` int NOT NULL,
  PRIMARY KEY (`id_vaso`),
  CONSTRAINT `vasos_chk_1` CHECK ((`capacidad_ml` > 0))
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `vasos` VALUES 
(1,'Caballito tequilero',60),
(2,'Old Fashioned',300),
(3,'Highball',350),
(4,'Copa Margarita',250),
(5,'Copa Martini',180),
(6,'Copa Huracán',450),
(7,'Copa balón',600),
(8,'Tarro cervecero',500),
(9,'Copa Flauta',200);

-- ------------------------------------------------------
-- Table structure for table `presentaciones`
-- ------------------------------------------------------
DROP TABLE IF EXISTS `presentaciones`;
CREATE TABLE `presentaciones` (
  `id_presentacion` int NOT NULL AUTO_INCREMENT,
  `id_bebida` int NOT NULL,
  `id_medida` int NOT NULL,
  `id_vaso` int NOT NULL,
  `precio` decimal(10,2) NOT NULL,
  PRIMARY KEY (`id_presentacion`),
  UNIQUE KEY `uk_bebida_medida_vaso` (`id_bebida`, `id_medida`, `id_vaso`),
  KEY `id_medida` (`id_medida`),
  KEY `id_vaso` (`id_vaso`),
  CONSTRAINT `presentaciones_ibfk_1` FOREIGN KEY (`id_bebida`) REFERENCES `bebidas` (`id_bebida`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `presentaciones_ibfk_2` FOREIGN KEY (`id_medida`) REFERENCES `medidas` (`id_medida`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `presentaciones_ibfk_3` FOREIGN KEY (`id_vaso`) REFERENCES `vasos` (`id_vaso`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `presentaciones_chk_1` CHECK ((`precio` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `presentaciones` VALUES 
(1,1,4,8,40.00),
(2,1,6,8,55.00),
(3,2,4,8,38.00),
(4,3,4,8,42.00),
(5,4,1,1,45.00),
(6,4,2,2,80.00),
(7,5,1,1,55.00),
(8,6,1,1,35.00),
(9,6,2,2,65.00),
(10,7,1,1,40.00),
(11,8,1,1,40.00),
(12,9,1,1,50.00),
(13,10,3,4,110.00),
(14,11,5,3,95.00),
(15,12,3,5,90.00),
(16,13,5,3,85.00),
(17,14,5,6,115.00),
(18,15,3,2,105.00),
(19,16,4,3,30.00),
(20,17,4,3,35.00),
(21,18,3,5,45.00);

-- ------------------------------------------------------
-- Table structure for table `pedidos`
-- ------------------------------------------------------
DROP TABLE IF EXISTS `pedidos`;
CREATE TABLE `pedidos` (
  `id_pedido` int NOT NULL AUTO_INCREMENT,
  `id_cliente` int DEFAULT NULL,
  `id_empleado` int NOT NULL,
  `id_mesa` int NOT NULL,
  `fecha` datetime DEFAULT CURRENT_TIMESTAMP,
  `estado` enum('Pendiente','Preparando','Entregado','Cancelado') COLLATE utf8mb4_unicode_ci DEFAULT 'Pendiente',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_pedido`),
  KEY `id_cliente` (`id_cliente`),
  KEY `id_empleado` (`id_empleado`),
  KEY `id_mesa` (`id_mesa`),
  CONSTRAINT `pedidos_ibfk_1` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id_cliente`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `pedidos_ibfk_2` FOREIGN KEY (`id_empleado`) REFERENCES `empleados` (`id_empleado`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `pedidos_ibfk_3` FOREIGN KEY (`id_mesa`) REFERENCES `mesas` (`id_mesa`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `pedidos` VALUES 
(1,1,1,1,'2026-11-09 14:52:46','Entregado','2026-11-09 14:52:46'),
(2,2,1,1,'2026-11-09 14:52:46','Entregado','2026-11-09 14:52:46'),
(3,3,1,2,'2026-11-09 14:52:46','Preparando','2026-11-09 14:52:46'),
(4,4,1,3,'2026-11-09 14:52:46','Pendiente','2026-11-09 14:52:46');

-- ------------------------------------------------------
-- Table structure for table `detalle_pedido`
-- ------------------------------------------------------
DROP TABLE IF EXISTS `detalle_pedido`;
CREATE TABLE `detalle_pedido` (
  `id_detalle` int NOT NULL AUTO_INCREMENT,
  `id_pedido` int NOT NULL,
  `id_presentacion` int NOT NULL,
  `cantidad` int NOT NULL,
  `precio_unitario` decimal(10,2) NOT NULL,
  PRIMARY KEY (`id_detalle`),
  UNIQUE KEY `uk_pedido_presentacion` (`id_pedido`, `id_presentacion`),
  KEY `id_pedido` (`id_pedido`),
  KEY `id_presentacion` (`id_presentacion`),
  CONSTRAINT `detalle_pedido_ibfk_1` FOREIGN KEY (`id_pedido`) REFERENCES `pedidos` (`id_pedido`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `detalle_pedido_ibfk_2` FOREIGN KEY (`id_presentacion`) REFERENCES `presentaciones` (`id_presentacion`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `detalle_pedido_chk_1` CHECK ((`cantidad` > 0)),
  CONSTRAINT `detalle_pedido_chk_2` CHECK ((`precio_unitario` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `detalle_pedido` VALUES 
(1,1,13,2,110.00),
(2,1,14,1,95.00),
(3,2,1,2,40.00),
(4,3,17,1,115.00),
(5,4,19,2,30.00);

-- ------------------------------------------------------
-- Table structure for table `extras`
-- ------------------------------------------------------
DROP TABLE IF EXISTS `extras`;
CREATE TABLE `extras` (
  `id_extra` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `precio` decimal(10,2) NOT NULL DEFAULT '0.00',
  PRIMARY KEY (`id_extra`),
  UNIQUE KEY `nombre` (`nombre`),
  CONSTRAINT `extras_chk_1` CHECK ((`precio` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `extras` VALUES 
(1,'Escarchado de sal',5.00),
(2,'Escarchado de azúcar',5.00),
(3,'Chamoy',5.00),
(4,'Tarugo de tamarindo',10.00),
(5,'Hielo',0.00),
(6,'Limón extra',3.00),
(7,'Naranja extra',3.00),
(8,'Cerezas',8.00),
(9,'Hierbabuena',5.00),
(10,'Chile en polvo',5.00),
(11,'Rodaja de piña',8.00);

-- ------------------------------------------------------
-- Table structure for table `detalle_pedido_extras`
-- ------------------------------------------------------
DROP TABLE IF EXISTS `detalle_pedido_extras`;
CREATE TABLE `detalle_pedido_extras` (
  `id_detalle` int NOT NULL,
  `id_extra` int NOT NULL,
  `precio_extra` decimal(10,2) NOT NULL DEFAULT '0.00',
  PRIMARY KEY (`id_detalle`,`id_extra`),
  KEY `id_extra` (`id_extra`),
  CONSTRAINT `detalle_pedido_extras_ibfk_1` FOREIGN KEY (`id_detalle`) REFERENCES `detalle_pedido` (`id_detalle`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `detalle_pedido_extras_ibfk_2` FOREIGN KEY (`id_extra`) REFERENCES `extras` (`id_extra`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `detalle_pedido_extras_chk_1` CHECK ((`precio_extra` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `detalle_pedido_extras` VALUES 
(1,1,5.00),
(1,6,3.00),
(2,9,5.00),
(3,5,0.00),
(4,8,8.00);

-- ------------------------------------------------------
-- Table structure for table `presentacion_extras`
-- ------------------------------------------------------
DROP TABLE IF EXISTS `presentacion_extras`;
CREATE TABLE `presentacion_extras` (
  `id_presentacion` int NOT NULL,
  `id_extra` int NOT NULL,
  PRIMARY KEY (`id_presentacion`,`id_extra`),
  KEY `id_extra` (`id_extra`),
  CONSTRAINT `presentacion_extras_ibfk_1` FOREIGN KEY (`id_presentacion`) REFERENCES `presentaciones` (`id_presentacion`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `presentacion_extras_ibfk_2` FOREIGN KEY (`id_extra`) REFERENCES `extras` (`id_extra`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `presentacion_extras` (`id_presentacion`, `id_extra`) VALUES
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

-- ------------------------------------------------------
-- Table structure for table `ingredientes`
-- ------------------------------------------------------
DROP TABLE IF EXISTS `ingredientes`;
CREATE TABLE `ingredientes` (
  `id_ingrediente` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `unidad_base` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id_ingrediente`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `ingredientes` VALUES 
(1,'Tequila blanco','ml'),
(2,'Triple Sec','ml'),
(3,'Jugo de lima','ml'),
(4,'Ron blanco','ml'),
(5,'Hierbabuena','hojas'),
(6,'Azúcar','g'),
(7,'Agua mineral','ml'),
(8,'Refresco de cola','ml'),
(9,'Crema de coco','ml'),
(10,'Jugo de piña','ml'),
(11,'Ginebra','ml'),
(12,'Campari','ml'),
(13,'Vermut rojo dulce','ml'),
(14,'Agua natural','ml'),
(15,'Granadina','ml'),
(16,'Jugo de limón','ml'),
(17,'Jugo de naranja','ml'),
(18,'Prosecco','ml'),
(19,'Ginger ale','ml'),
(20,'Cereza','pieza'),
(21,'Hielo','g'),
(22,'Jarabe natural','ml'),
(23,'Agua tónica','ml');

-- ------------------------------------------------------
-- Table structure for table `recetas`
-- ------------------------------------------------------
DROP TABLE IF EXISTS `recetas`;
CREATE TABLE `recetas` (
  `id_receta` int NOT NULL AUTO_INCREMENT,
  `id_bebida` int NOT NULL,
  `metodo` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `preparacion` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `decoracion` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id_receta`),
  UNIQUE KEY `id_bebida` (`id_bebida`),
  CONSTRAINT `recetas_ibfk_1` FOREIGN KEY (`id_bebida`) REFERENCES `bebidas` (`id_bebida`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `recetas` VALUES 
(1,10,'Agitado','Agitar tequila, Triple Sec y jugo de lima con hielo. Colar en copa fría.','Escarchado de sal y rodaja de lima'),
(2,11,'Directo','Mezclar suavemente hierbabuena, azúcar y lima. Agregar ron, hielo y agua mineral.','Hierbabuena y rodaja de lima'),
(3,12,'Agitado','Agitar ron, jugo de lima y azúcar con hielo. Colar en copa fría.','Rodaja de lima opcional'),
(4,13,'Directo','Agregar ron y jugo de lima en vaso con hielo. Completar con refresco de cola.','Gajo de lima'),
(5,14,'Licuado','Licuar ron, crema de coco y jugo de piña con hielo.','Rodaja de piña y cereza'),
(6,15,'Directo','Combinar ginebra, Campari y vermut rojo. Mezclar con hielo.','Rodaja de naranja'),
(7,16,'Directo','Mezclar jugo de limón, jarabe natural, agua y hielo.','Rodaja de limón'),
(8,18,'Directo','Servir ginger ale con hielo y agregar granadina.','Cereza');

-- ------------------------------------------------------
-- Table structure for table `receta_ingredientes`
-- ------------------------------------------------------
DROP TABLE IF EXISTS `receta_ingredientes`;
CREATE TABLE `receta_ingredientes` (
  `id_receta` int NOT NULL,
  `id_ingrediente` int NOT NULL,
  `cantidad` decimal(10,2) NOT NULL,
  `unidad` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id_receta`,`id_ingrediente`),
  KEY `id_ingrediente` (`id_ingrediente`),
  CONSTRAINT `receta_ingredientes_ibfk_1` FOREIGN KEY (`id_receta`) REFERENCES `recetas` (`id_receta`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `receta_ingredientes_ibfk_2` FOREIGN KEY (`id_ingrediente`) REFERENCES `ingredientes` (`id_ingrediente`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `receta_ingredientes_chk_1` CHECK ((`cantidad` > 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `receta_ingredientes` VALUES 
(1,1,50.00,'ml'),(1,2,20.00,'ml'),(1,3,15.00,'ml'),
(2,3,20.00,'ml'),(2,4,45.00,'ml'),(2,5,6.00,'hojas'),(2,6,5.00,'g'),(2,7,60.00,'ml'),(2,21,100.00,'g'),
(3,3,20.00,'ml'),(3,4,60.00,'ml'),(3,6,10.00,'g'),(3,21,100.00,'g'),
(4,3,10.00,'ml'),(4,4,50.00,'ml'),(4,8,120.00,'ml'),(4,21,100.00,'g'),
(5,4,50.00,'ml'),(5,9,30.00,'ml'),(5,10,50.00,'ml'),(5,21,120.00,'g'),
(6,11,30.00,'ml'),(6,12,30.00,'ml'),(6,13,30.00,'ml'),(6,21,100.00,'g'),
(7,14,180.00,'ml'),(7,16,30.00,'ml'),(7,21,100.00,'g'),(7,22,20.00,'ml'),
(8,15,20.00,'ml'),(8,19,150.00,'ml'),(8,20,1.00,'pieza'),(8,21,100.00,'g');

SET FOREIGN_KEY_CHECKS = 1;

-- ------------------------------------------------------
-- Transacción de prueba en tiempo real
-- ------------------------------------------------------
START TRANSACTION;

INSERT IGNORE INTO clientes (nombre, telefono, correo) 
VALUES ('Sofía Castro', '5598765432', 'sofia@gmail.com');

SET @id_cliente_sofia = (SELECT id_cliente FROM clientes WHERE telefono = '5598765432' LIMIT 1);

INSERT INTO pedidos (id_cliente, id_empleado, id_mesa, estado) 
VALUES (@id_cliente_sofia, 1, 2, 'Pendiente');

SET @id_pedido_nuevo = LAST_INSERT_ID();

INSERT INTO detalle_pedido (id_pedido, id_presentacion, cantidad, precio_unitario) 
VALUES (@id_pedido_nuevo, 1, 3, 40.00);

SET @id_detalle_nuevo = LAST_INSERT_ID();

INSERT INTO detalle_pedido_extras (id_detalle, id_extra, precio_extra) 
VALUES (@id_detalle_nuevo, 6, 3.00);

UPDATE mesas SET estado = 'Ocupada' WHERE id_mesa = 2;

COMMIT;

-- Consulta de verificación del pedido creado
SELECT 
    p.id_pedido,
    m.numero_mesa,
    c.nombre AS cliente,
    e.nombre AS mesero,
    b.nombre AS bebida,
    med.nombre AS medida,
    dp.cantidad,
    dp.precio_unitario,
    (dp.cantidad * dp.precio_unitario) AS subtotal
FROM pedidos p
INNER JOIN mesas m ON p.id_mesa = m.id_mesa
LEFT JOIN clientes c ON p.id_cliente = c.id_cliente
INNER JOIN empleados e ON p.id_empleado = e.id_empleado
INNER JOIN detalle_pedido dp ON p.id_pedido = dp.id_pedido
INNER JOIN presentaciones pres ON dp.id_presentacion = pres.id_presentacion
INNER JOIN bebidas b ON pres.id_bebida = b.id_bebida
INNER JOIN medidas med ON pres.id_medida = med.id_medida
WHERE p.id_pedido = @id_pedido_nuevo;
