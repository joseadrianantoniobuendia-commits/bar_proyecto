from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from flask import Flask, abort, jsonify, request, send_from_directory
from mysql.connector import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db_connection


PROJECT_ROOT = Path(__file__).resolve().parents[1]
app = Flask(__name__)


@app.get("/")
def inicio():
    return send_from_directory(PROJECT_ROOT, "index.html")


@app.get("/<path:archivo>")
def archivos_estaticos(archivo):
    # Solo publicar la interfaz. Los archivos Python, SQL y configuración quedan fuera.
    permitidos = {"app.js", "styles.css", "theme.css"}
    if archivo not in permitidos and not archivo.startswith(("js/", "imagenes/")):
        abort(404)
    return send_from_directory(PROJECT_ROOT, archivo)


def _cursor_db():
    return get_db_connection()


def _leer_json():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        raise ValueError("El cuerpo de la solicitud no es válido.")
    return datos


def _entero_positivo(valor, etiqueta):
    if isinstance(valor, bool):
        raise ValueError(f"{etiqueta} no es válido.")
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{etiqueta} no es válido.")
    if numero < 1 or str(numero) != str(valor).strip():
        raise ValueError(f"{etiqueta} no es válido.")
    return numero


def _dinero(valor, etiqueta, permitir_cero=False):
    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{etiqueta} no es válido.")
    if not numero.is_finite() or numero < 0 or (numero == 0 and not permitir_cero):
        raise ValueError(f"{etiqueta} debe ser un monto válido.")
    return numero.quantize(Decimal("0.01"))


def _total_pedido(cursor, id_pedido):
    cursor.execute(
        """
        SELECT
            COALESCE((SELECT SUM(dp.cantidad * dp.precio_unitario)
                      FROM detalle_pedido dp WHERE dp.id_pedido = %s), 0)
            + COALESCE((SELECT SUM(dp.cantidad * dpe.precio_extra)
                        FROM detalle_pedido dp
                        JOIN detalle_pedido_extras dpe ON dpe.id_detalle = dp.id_detalle
                        WHERE dp.id_pedido = %s), 0) AS total
        """,
        (id_pedido, id_pedido),
    )
    total = cursor.fetchone()["total"]
    return Decimal(str(total or 0)).quantize(Decimal("0.01"))


def _liberar_mesa_si_corresponde(cursor, id_mesa):
    cursor.execute(
        """
        UPDATE mesas m SET estado = 'Disponible'
        WHERE m.id_mesa = %s
          AND NOT EXISTS (
              SELECT 1 FROM pedidos p
              WHERE p.id_mesa = m.id_mesa
                AND p.estado IN ('Pendiente', 'Preparando', 'Entregado')
                AND NOT EXISTS (
                    SELECT 1 FROM pagos pg
                    WHERE pg.id_pedido = p.id_pedido AND pg.estado = 'Registrado'
                )
          )
        """,
        (id_mesa,),
    )


def _cerrar(conn, cursor=None):
    if cursor is not None:
        cursor.close()
    if conn is not None and conn.is_connected():
        conn.close()


@app.get("/api/datos_iniciales")
def datos_iniciales():
    conn = cursor = None
    try:
        conn = _cursor_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id_mesa, numero_mesa, capacidad, estado FROM mesas ORDER BY numero_mesa")
        mesas = cursor.fetchall()
        for mesa in mesas:
            for campo in ("id_mesa", "numero_mesa", "capacidad"):
                mesa[campo] = int(mesa[campo])

        cursor.execute(
            """
            SELECT pr.id_presentacion,
                   CONCAT(b.nombre, ' (', m.nombre, ' ', m.mililitros, 'ml - ', v.nombre, ')') AS nombre,
                   c.nombre AS categoria, pr.precio, b.estado
            FROM presentaciones pr
            JOIN bebidas b ON b.id_bebida = pr.id_bebida
            JOIN categorias c ON c.id_categoria = b.id_categoria
            JOIN medidas m ON m.id_medida = pr.id_medida
            JOIN vasos v ON v.id_vaso = pr.id_vaso
            WHERE b.estado = 'Disponible'
            ORDER BY c.nombre, b.nombre
            """
        )
        bebidas = cursor.fetchall()
        for bebida in bebidas:
            bebida["id_presentacion"] = int(bebida["id_presentacion"])
            bebida["precio"] = float(bebida["precio"])

        cursor.execute("SELECT id_extra, nombre, precio FROM extras ORDER BY nombre")
        extras = cursor.fetchall()
        for extra in extras:
            extra["id_extra"] = int(extra["id_extra"])
            extra["precio"] = float(extra["precio"])

        cursor.execute("SELECT id_presentacion, id_extra FROM presentacion_extras")
        extras_por_presentacion = {}
        for relacion in cursor.fetchall():
            extras_por_presentacion.setdefault(int(relacion["id_presentacion"]), []).append(
                int(relacion["id_extra"])
            )
        for bebida in bebidas:
            bebida["extras_permitidos"] = extras_por_presentacion.get(bebida["id_presentacion"], [])

        cursor.execute("SELECT id_cliente, nombre, telefono, correo FROM clientes ORDER BY nombre")
        clientes = cursor.fetchall()
        for cliente in clientes:
            cliente["id_cliente"] = int(cliente["id_cliente"])

        cursor.execute(
            """
            SELECT r.id_receta, b.nombre AS bebida, r.metodo, r.preparacion, r.decoracion,
                   i.nombre AS ing_nombre, ri.cantidad, ri.unidad
            FROM recetas r
            JOIN bebidas b ON b.id_bebida = r.id_bebida
            LEFT JOIN receta_ingredientes ri ON ri.id_receta = r.id_receta
            LEFT JOIN ingredientes i ON i.id_ingrediente = ri.id_ingrediente
            ORDER BY b.nombre, i.nombre
            """
        )
        recetas_map = {}
        for fila in cursor.fetchall():
            id_receta = int(fila["id_receta"])
            if id_receta not in recetas_map:
                recetas_map[id_receta] = {
                    "id_receta": id_receta,
                    "bebida": fila["bebida"],
                    "metodo": fila["metodo"],
                    "preparacion": fila["preparacion"],
                    "decoracion": fila["decoracion"],
                    "ingredientes": [],
                }
            if fila["ing_nombre"]:
                recetas_map[id_receta]["ingredientes"].append(
                    {
                        "nombre": fila["ing_nombre"],
                        "cantidad": float(fila["cantidad"]),
                        "unidad": fila["unidad"],
                    }
                )

        cursor.execute(
            """
            SELECT p.id_pedido, m.numero_mesa, p.estado, dp.id_detalle, dp.cantidad,
                   CONCAT(b.nombre, ' (', med.nombre, ')') AS bebida_nombre,
                   ex.nombre AS extra_nombre, dpe.precio_extra
            FROM pedidos p
            JOIN mesas m ON m.id_mesa = p.id_mesa
            LEFT JOIN detalle_pedido dp ON dp.id_pedido = p.id_pedido
            LEFT JOIN presentaciones pr ON pr.id_presentacion = dp.id_presentacion
            LEFT JOIN bebidas b ON b.id_bebida = pr.id_bebida
            LEFT JOIN medidas med ON med.id_medida = pr.id_medida
            LEFT JOIN detalle_pedido_extras dpe ON dpe.id_detalle = dp.id_detalle
            LEFT JOIN extras ex ON ex.id_extra = dpe.id_extra
            WHERE p.estado IN ('Pendiente', 'Preparando', 'Entregado')
              AND NOT EXISTS (
                  SELECT 1 FROM pagos pg
                  WHERE pg.id_pedido = p.id_pedido AND pg.estado = 'Registrado'
              )
            ORDER BY p.id_pedido DESC, dp.id_detalle ASC
            """
        )
        pedidos_map = {}
        detalles_map = {}
        for fila in cursor.fetchall():
            id_pedido = int(fila["id_pedido"])
            if id_pedido not in pedidos_map:
                pedidos_map[id_pedido] = {
                    "id_pedido": id_pedido,
                    "numero_mesa": int(fila["numero_mesa"]),
                    "estado": fila["estado"],
                    "items": [],
                }
            if fila["id_detalle"]:
                id_detalle = int(fila["id_detalle"])
                if id_detalle not in detalles_map:
                    detalle = {
                        "cantidad": int(fila["cantidad"]),
                        "nombre": fila["bebida_nombre"],
                        "extras": [],
                    }
                    detalles_map[id_detalle] = detalle
                    pedidos_map[id_pedido]["items"].append(detalle)
                if fila["extra_nombre"]:
                    detalles_map[id_detalle]["extras"].append(
                        {"nombre": fila["extra_nombre"], "precio": float(fila["precio_extra"])}
                    )

        return jsonify(
            {
                "mesas": mesas,
                "bebidas": bebidas,
                "extras": extras,
                "clientes": clientes,
                "recetas": list(recetas_map.values()),
                "pedidos": list(pedidos_map.values()),
            }
        )
    except Exception as error:
        app.logger.exception("No se pudieron cargar los datos iniciales: %s", error)
        return jsonify(error="No se pudieron cargar los datos iniciales. Revisa MySQL y la configuración local."), 500
    finally:
        _cerrar(conn, cursor)


@app.post("/api/login")
def login():
    try:
        datos = _leer_json()
    except ValueError as error:
        return jsonify(ok=False, error=str(error)), 400

    usuario = str(datos.get("usuario", "")).strip().lower()
    pin = str(datos.get("pin", "")).strip()
    if not usuario or not pin:
        return jsonify(ok=False, error="Usuario y PIN requeridos."), 400

    conn = cursor = None
    try:
        conn = _cursor_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_empleado, nombre, rol, pin, pin_hash FROM empleados WHERE LOWER(usuario) = %s LIMIT 1",
            (usuario,),
        )
        empleado = cursor.fetchone()
        if not empleado:
            return jsonify(ok=False, error="Credenciales incorrectas."), 401

        pin_hash = empleado.get("pin_hash")
        if pin_hash:
            if not check_password_hash(pin_hash, pin):
                return jsonify(ok=False, error="Credenciales incorrectas."), 401
        else:
            pin_legado = empleado.get("pin")
            if pin_legado is None or str(pin_legado) != pin:
                return jsonify(ok=False, error="Credenciales incorrectas."), 401
            nuevo_hash = generate_password_hash(pin)
            cursor.execute(
                "UPDATE empleados SET pin_hash = %s, pin = NULL WHERE id_empleado = %s",
                (nuevo_hash, int(empleado["id_empleado"])),
            )
            conn.commit()

        respuesta = {
            "id_empleado": int(empleado["id_empleado"]),
            "nombre": empleado["nombre"],
            "rol": empleado["rol"],
        }
        return jsonify(ok=True, empleado=respuesta)
    except Exception as error:
        if conn and conn.is_connected():
            conn.rollback()
        app.logger.exception("Error de inicio de sesión: %s", error)
        return jsonify(ok=False, error="No se pudo completar el inicio de sesión."), 500
    finally:
        _cerrar(conn, cursor)


@app.post("/api/crear_cliente")
def crear_cliente():
    try:
        datos = _leer_json()
    except ValueError as error:
        return jsonify(ok=False, error=str(error)), 400

    nombre = str(datos.get("nombre", "")).strip()
    telefono = str(datos.get("telefono", "")).strip()
    correo = str(datos.get("correo", "")).strip() or None
    if not nombre or not telefono:
        return jsonify(ok=False, error="Nombre y teléfono son obligatorios."), 400
    if len(nombre) > 100 or len(telefono) > 20 or (correo and len(correo) > 100):
        return jsonify(ok=False, error="Algún dato excede el tamaño permitido."), 400

    conn = cursor = None
    try:
        conn = _cursor_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_cliente, nombre, telefono, correo FROM clientes WHERE telefono = %s LIMIT 1",
            (telefono,),
        )
        cliente = cursor.fetchone()
        if cliente:
            cliente["id_cliente"] = int(cliente["id_cliente"])
            return jsonify(ok=True, id_cliente=cliente["id_cliente"], cliente=cliente)

        cursor.execute(
            "INSERT INTO clientes (nombre, telefono, correo) VALUES (%s, %s, %s)",
            (nombre, telefono, correo),
        )
        id_cliente = int(cursor.lastrowid)
        conn.commit()
        cliente = {"id_cliente": id_cliente, "nombre": nombre, "telefono": telefono, "correo": correo}
        return jsonify(ok=True, id_cliente=id_cliente, cliente=cliente)
    except IntegrityError:
        if conn and conn.is_connected():
            conn.rollback()
        return jsonify(ok=False, error="Ya existe un cliente con ese teléfono."), 409
    except Exception as error:
        if conn and conn.is_connected():
            conn.rollback()
        app.logger.exception("Error al registrar cliente: %s", error)
        return jsonify(ok=False, error="No se pudo registrar el cliente."), 500
    finally:
        _cerrar(conn, cursor)


@app.post("/api/actualizar_estado_pedido")
def actualizar_estado_pedido():
    try:
        datos = _leer_json()
        id_pedido = _entero_positivo(datos.get("id_pedido"), "El pedido")
        id_empleado = _entero_positivo(datos.get("id_empleado"), "El empleado")
        estado = str(datos.get("estado", "")).strip()
    except ValueError as error:
        return jsonify(ok=False, error=str(error)), 400
    estados_validos = {"Pendiente", "Preparando", "Entregado", "Cancelado"}
    if estado not in estados_validos:
        return jsonify(ok=False, error="El estado indicado no es válido."), 400

    conn = cursor = None
    try:
        conn = _cursor_db()
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_mesa, estado FROM pedidos WHERE id_pedido = %s FOR UPDATE",
            (id_pedido,),
        )
        pedido = cursor.fetchone()
        if not pedido:
            conn.rollback()
            return jsonify(ok=False, error="No se encontró el pedido."), 404

        estado_actual = pedido["estado"]
        if estado_actual == estado:
            conn.commit()
            return jsonify(ok=True, id_pedido=id_pedido, estado=estado)
        if estado_actual == "Cancelado":
            raise ValueError("Un pedido cancelado no se puede reabrir.")
        if estado == "Pendiente":
            raise ValueError("No se puede regresar un pedido a Pendiente.")
        if estado == "Preparando" and estado_actual != "Pendiente":
            raise ValueError("Solo se puede preparar un pedido pendiente.")
        if estado == "Entregado" and estado_actual not in {"Pendiente", "Preparando"}:
            raise ValueError("El pedido no está listo para entregarse.")

        if estado == "Cancelado":
            cursor.execute(
                "SELECT 1 FROM pagos WHERE id_pedido = %s AND estado = 'Registrado' LIMIT 1",
                (id_pedido,),
            )
            if cursor.fetchone():
                raise ValueError("No se puede cancelar un pedido que ya fue cobrado.")
            cursor.execute(
                """SELECT id_ingrediente, cantidad FROM consumos_pedido
                   WHERE id_pedido = %s AND revertido = 0 FOR UPDATE""",
                (id_pedido,),
            )
            for consumo in cursor.fetchall():
                cursor.execute(
                    "UPDATE existencias_ingrediente SET existencia = existencia + %s WHERE id_ingrediente = %s",
                    (consumo["cantidad"], consumo["id_ingrediente"]),
                )
                cursor.execute(
                    """INSERT INTO movimientos_inventario
                       (id_ingrediente, id_empleado, tipo, cantidad, referencia, notas)
                       VALUES (%s, %s, 'AjustePositivo', %s, %s, %s)""",
                    (consumo["id_ingrediente"], id_empleado, consumo["cantidad"],
                     f"Pedido #{id_pedido}", "Reversión por cancelación del pedido"),
                )
            cursor.execute(
                "UPDATE consumos_pedido SET revertido = 1 WHERE id_pedido = %s",
                (id_pedido,),
            )

        if estado == "Entregado" and estado_actual != "Entregado":
            cursor.execute(
                """
                SELECT ri.id_ingrediente, SUM(ri.cantidad * dp.cantidad) AS requerido,
                       i.nombre, i.unidad_base
                FROM detalle_pedido dp
                JOIN presentaciones pr ON pr.id_presentacion = dp.id_presentacion
                JOIN recetas r ON r.id_bebida = pr.id_bebida
                JOIN receta_ingredientes ri ON ri.id_receta = r.id_receta
                JOIN ingredientes i ON i.id_ingrediente = ri.id_ingrediente
                WHERE dp.id_pedido = %s AND ri.unidad = i.unidad_base
                GROUP BY ri.id_ingrediente, i.nombre, i.unidad_base
                """,
                (id_pedido,),
            )
            consumos = cursor.fetchall()
            for consumo in consumos:
                requerido = Decimal(str(consumo["requerido"])).quantize(Decimal("0.01"))
                cursor.execute(
                    "SELECT existencia FROM existencias_ingrediente WHERE id_ingrediente = %s FOR UPDATE",
                    (consumo["id_ingrediente"],),
                )
                fila_stock = cursor.fetchone()
                existencia = Decimal(str(fila_stock["existencia"] if fila_stock else 0))
                if existencia < requerido:
                    raise ValueError(
                        f"Inventario insuficiente de {consumo['nombre']}: "
                        f"hay {existencia} {consumo['unidad_base']} y se requieren {requerido}. "
                        "Registra una entrada en Inventario antes de entregar el pedido."
                    )
                cursor.execute(
                    "UPDATE existencias_ingrediente SET existencia = existencia - %s WHERE id_ingrediente = %s",
                    (requerido, consumo["id_ingrediente"]),
                )
                cursor.execute(
                    """INSERT INTO movimientos_inventario
                       (id_ingrediente, id_empleado, tipo, cantidad, referencia, notas)
                       VALUES (%s, %s, 'Consumo', %s, %s, %s)""",
                    (consumo["id_ingrediente"], id_empleado, requerido,
                     f"Pedido #{id_pedido}", "Consumo registrado al entregar la bebida"),
                )
                cursor.execute(
                    """INSERT INTO consumos_pedido (id_pedido, id_ingrediente, cantidad)
                       VALUES (%s, %s, %s)""",
                    (id_pedido, consumo["id_ingrediente"], requerido),
                )

        cursor.execute("UPDATE pedidos SET estado = %s WHERE id_pedido = %s", (estado, id_pedido))
        if estado == "Cancelado":
            _liberar_mesa_si_corresponde(cursor, pedido["id_mesa"])
        conn.commit()
        return jsonify(ok=True, id_pedido=id_pedido, estado=estado)
    except ValueError as error:
        if conn and conn.is_connected():
            conn.rollback()
        return jsonify(ok=False, error=str(error)), 409
    except Exception as error:
        if conn and conn.is_connected():
            conn.rollback()
        app.logger.exception("Error al actualizar pedido: %s", error)
        return jsonify(ok=False, error="No se pudo actualizar el pedido."), 500
    finally:
        _cerrar(conn, cursor)


@app.post("/api/crear_pedido")
def crear_pedido():
    try:
        datos = _leer_json()
        id_mesa = _entero_positivo(datos.get("id_mesa"), "La mesa")
        id_empleado = _entero_positivo(datos.get("id_empleado"), "El empleado")
        raw_id_cliente = datos.get("id_cliente")
        id_cliente = None if raw_id_cliente in (None, "") else _entero_positivo(raw_id_cliente, "El cliente")
        items = datos.get("items")
        if not isinstance(items, list) or not items or len(items) > 80:
            raise ValueError("El pedido debe contener entre 1 y 80 artículos.")
    except ValueError as error:
        return jsonify(error=str(error)), 400

    conn = cursor = None
    try:
        conn = _cursor_db()
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id_mesa FROM mesas WHERE id_mesa = %s FOR UPDATE", (id_mesa,))
        if cursor.fetchone() is None:
            raise ValueError("La mesa seleccionada no existe.")

        cursor.execute(
            "INSERT INTO pedidos (id_cliente, id_empleado, id_mesa, estado) VALUES (%s, %s, %s, 'Pendiente')",
            (id_cliente, id_empleado, id_mesa),
        )
        id_pedido = int(cursor.lastrowid)

        for item in items:
            if not isinstance(item, dict):
                raise ValueError("Hay un artículo inválido en el pedido.")
            id_presentacion = _entero_positivo(item.get("id_presentacion"), "La presentación")
            cantidad = _entero_positivo(item.get("cantidad"), "La cantidad")
            if cantidad > 1000:
                raise ValueError("La cantidad máxima por artículo es 1000.")

            cursor.execute(
                """
                SELECT pr.precio, b.estado
                FROM presentaciones pr JOIN bebidas b ON b.id_bebida = pr.id_bebida
                WHERE pr.id_presentacion = %s FOR UPDATE
                """,
                (id_presentacion,),
            )
            presentacion = cursor.fetchone()
            if not presentacion or presentacion["estado"] != "Disponible":
                raise ValueError("Una bebida ya no está disponible.")

            cursor.execute(
                "INSERT INTO detalle_pedido (id_pedido, id_presentacion, cantidad, precio_unitario) VALUES (%s, %s, %s, %s)",
                (id_pedido, id_presentacion, cantidad, presentacion["precio"]),
            )
            id_detalle = int(cursor.lastrowid)

            extras = item.get("extras", [])
            if not isinstance(extras, list):
                raise ValueError("Los extras de un artículo no son válidos.")
            extras_vistos = set()
            for extra in extras:
                if not isinstance(extra, dict):
                    raise ValueError("Hay un extra inválido.")
                id_extra = _entero_positivo(extra.get("id_extra"), "El extra")
                if id_extra in extras_vistos:
                    raise ValueError("No se puede repetir el mismo extra.")
                extras_vistos.add(id_extra)

                cursor.execute(
                    """
                    SELECT e.precio FROM extras e
                    JOIN presentacion_extras pe ON pe.id_extra = e.id_extra
                    WHERE pe.id_presentacion = %s AND pe.id_extra = %s
                    """,
                    (id_presentacion, id_extra),
                )
                fila_extra = cursor.fetchone()
                if fila_extra is None:
                    raise ValueError("Ese extra no está disponible para la bebida seleccionada.")
                cursor.execute(
                    "INSERT INTO detalle_pedido_extras (id_detalle, id_extra, precio_extra) VALUES (%s, %s, %s)",
                    (id_detalle, id_extra, fila_extra["precio"]),
                )

        cursor.execute("UPDATE mesas SET estado = 'Ocupada' WHERE id_mesa = %s", (id_mesa,))
        conn.commit()
        return jsonify(ok=True, id_pedido=id_pedido)
    except ValueError as error:
        if conn and conn.is_connected():
            conn.rollback()
        return jsonify(error=str(error)), 400
    except Exception as error:
        if conn and conn.is_connected():
            conn.rollback()
        app.logger.exception("Error al crear pedido: %s", error)
        return jsonify(error="No se pudo guardar el pedido. Revisa la conexión con MySQL."), 500
    finally:
        _cerrar(conn, cursor)


@app.get("/api/inventario")
def inventario():
    conn = cursor = None
    try:
        conn = _cursor_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT i.id_ingrediente, i.nombre, i.unidad_base,
                      COALESCE(e.existencia, 0) AS existencia
               FROM ingredientes i
               LEFT JOIN existencias_ingrediente e ON e.id_ingrediente = i.id_ingrediente
               ORDER BY i.nombre"""
        )
        ingredientes = cursor.fetchall()
        for fila in ingredientes:
            fila["id_ingrediente"] = int(fila["id_ingrediente"])
            fila["existencia"] = float(fila["existencia"] or 0)

        cursor.execute(
            """SELECT mi.id_movimiento, i.nombre AS ingrediente, i.unidad_base,
                      mi.tipo, mi.cantidad, mi.costo_unitario, mi.referencia, mi.notas,
                      mi.fecha, e.nombre AS empleado
               FROM movimientos_inventario mi
               JOIN ingredientes i ON i.id_ingrediente = mi.id_ingrediente
               JOIN empleados e ON e.id_empleado = mi.id_empleado
               ORDER BY mi.id_movimiento DESC LIMIT 40"""
        )
        movimientos = cursor.fetchall()
        for fila in movimientos:
            fila["id_movimiento"] = int(fila["id_movimiento"])
            fila["cantidad"] = float(fila["cantidad"])
            fila["costo_unitario"] = float(fila["costo_unitario"]) if fila["costo_unitario"] is not None else None
            fila["fecha"] = fila["fecha"].strftime("%Y-%m-%d %H:%M")
        return jsonify(ingredientes=ingredientes, movimientos=movimientos)
    except Exception as error:
        app.logger.exception("Error al consultar inventario: %s", error)
        return jsonify(error="No se pudo cargar el inventario."), 500
    finally:
        _cerrar(conn, cursor)


@app.post("/api/inventario/movimiento")
def registrar_movimiento_inventario():
    try:
        datos = _leer_json()
        id_ingrediente = _entero_positivo(datos.get("id_ingrediente"), "El ingrediente")
        id_empleado = _entero_positivo(datos.get("id_empleado"), "El empleado")
        cantidad = _dinero(datos.get("cantidad"), "La cantidad")
        tipo = str(datos.get("tipo", "")).strip()
        notas = str(datos.get("notas", "")).strip() or None
        if tipo not in {"Entrada", "AjustePositivo", "AjusteNegativo", "Merma"}:
            raise ValueError("El tipo de movimiento no es válido.")
        if notas and len(notas) > 255:
            raise ValueError("Las notas no pueden superar 255 caracteres.")
        raw_costo = datos.get("costo_unitario")
        costo = None if raw_costo in (None, "") else _dinero(raw_costo, "El costo unitario", permitir_cero=True)
    except ValueError as error:
        return jsonify(ok=False, error=str(error)), 400

    conn = cursor = None
    try:
        conn = _cursor_db()
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT nombre FROM ingredientes WHERE id_ingrediente = %s", (id_ingrediente,))
        ingrediente = cursor.fetchone()
        if not ingrediente:
            conn.rollback()
            return jsonify(ok=False, error="No se encontró el ingrediente."), 404
        cursor.execute(
            "SELECT existencia FROM existencias_ingrediente WHERE id_ingrediente = %s FOR UPDATE",
            (id_ingrediente,),
        )
        fila_existencia = cursor.fetchone()
        if not fila_existencia:
            cursor.execute(
                "INSERT INTO existencias_ingrediente (id_ingrediente, existencia) VALUES (%s, 0.00)",
                (id_ingrediente,),
            )
            actual = Decimal("0.00")
        else:
            actual = Decimal(str(fila_existencia["existencia"]))

        suma = tipo in {"Entrada", "AjustePositivo"}
        nuevo = actual + cantidad if suma else actual - cantidad
        if nuevo < 0:
            raise ValueError("El movimiento dejaría el inventario en negativo.")
        cursor.execute(
            "UPDATE existencias_ingrediente SET existencia = %s WHERE id_ingrediente = %s",
            (nuevo, id_ingrediente),
        )
        cursor.execute(
            """INSERT INTO movimientos_inventario
               (id_ingrediente, id_empleado, tipo, cantidad, costo_unitario, notas)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (id_ingrediente, id_empleado, tipo, cantidad, costo, notas),
        )
        conn.commit()
        return jsonify(ok=True, existencia=float(nuevo))
    except ValueError as error:
        if conn and conn.is_connected():
            conn.rollback()
        return jsonify(ok=False, error=str(error)), 409
    except Exception as error:
        if conn and conn.is_connected():
            conn.rollback()
        app.logger.exception("Error al registrar movimiento de inventario: %s", error)
        return jsonify(ok=False, error="No se pudo registrar el movimiento."), 500
    finally:
        _cerrar(conn, cursor)


@app.get("/api/caja/resumen")
def resumen_caja():
    conn = cursor = None
    try:
        conn = _cursor_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT c.id_caja, c.fondo_inicial, c.fecha_apertura,
                      ea.nombre AS empleado_apertura
               FROM cajas c JOIN empleados ea ON ea.id_empleado = c.id_empleado_apertura
               WHERE c.estado = 'Abierta' LIMIT 1"""
        )
        caja = cursor.fetchone()
        totales = {"Efectivo": 0.0, "Tarjeta": 0.0, "Transferencia": 0.0, "Otro": 0.0}
        if caja:
            caja["id_caja"] = int(caja["id_caja"])
            caja["fondo_inicial"] = float(caja["fondo_inicial"])
            caja["fecha_apertura"] = caja["fecha_apertura"].strftime("%Y-%m-%d %H:%M")
            cursor.execute(
                """SELECT pg.metodo, COALESCE(SUM(pg.monto), 0) AS total
                   FROM caja_pagos cp JOIN pagos pg ON pg.id_pago = cp.id_pago
                   WHERE cp.id_caja = %s AND pg.estado = 'Registrado'
                   GROUP BY pg.metodo""",
                (caja["id_caja"],),
            )
            for fila in cursor.fetchall():
                totales[fila["metodo"]] = float(fila["total"])
        caja["efectivo_esperado"] = round(caja["fondo_inicial"] + totales["Efectivo"], 2) if caja else 0.0

        cursor.execute(
            """SELECT p.id_pedido, m.numero_mesa, c.nombre AS cliente,
                      COALESCE((SELECT SUM(dp.cantidad * dp.precio_unitario)
                                FROM detalle_pedido dp WHERE dp.id_pedido = p.id_pedido), 0)
                      + COALESCE((SELECT SUM(dp.cantidad * dpe.precio_extra)
                                  FROM detalle_pedido dp
                                  JOIN detalle_pedido_extras dpe ON dpe.id_detalle = dp.id_detalle
                                  WHERE dp.id_pedido = p.id_pedido), 0) AS total
               FROM pedidos p
               JOIN mesas m ON m.id_mesa = p.id_mesa
               LEFT JOIN clientes c ON c.id_cliente = p.id_cliente
               WHERE p.estado = 'Entregado'
                 AND NOT EXISTS (
                     SELECT 1 FROM pagos pg
                     WHERE pg.id_pedido = p.id_pedido AND pg.estado = 'Registrado'
                 )
               ORDER BY p.fecha, p.id_pedido"""
        )
        pendientes = cursor.fetchall()
        for fila in pendientes:
            fila["id_pedido"] = int(fila["id_pedido"])
            fila["numero_mesa"] = int(fila["numero_mesa"])
            fila["total"] = float(fila["total"] or 0)
        return jsonify(caja=caja, totales=totales, pendientes=pendientes)
    except Exception as error:
        app.logger.exception("Error al consultar la caja: %s", error)
        return jsonify(error="No se pudo cargar la caja."), 500
    finally:
        _cerrar(conn, cursor)


@app.post("/api/caja/abrir")
def abrir_caja():
    try:
        datos = _leer_json()
        id_empleado = _entero_positivo(datos.get("id_empleado"), "El empleado")
        fondo = _dinero(datos.get("fondo_inicial"), "El fondo inicial", permitir_cero=True)
    except ValueError as error:
        return jsonify(ok=False, error=str(error)), 400

    conn = cursor = None
    try:
        conn = _cursor_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO cajas (id_empleado_apertura, fondo_inicial) VALUES (%s, %s)",
            (id_empleado, fondo),
        )
        id_caja = int(cursor.lastrowid)
        conn.commit()
        return jsonify(ok=True, id_caja=id_caja)
    except IntegrityError:
        if conn and conn.is_connected():
            conn.rollback()
        return jsonify(ok=False, error="Ya hay una caja abierta. Ciérrala antes de abrir otra."), 409
    except Exception as error:
        if conn and conn.is_connected():
            conn.rollback()
        app.logger.exception("Error al abrir caja: %s", error)
        return jsonify(ok=False, error="No se pudo abrir la caja."), 500
    finally:
        _cerrar(conn, cursor)


@app.post("/api/caja/cerrar")
def cerrar_caja():
    try:
        datos = _leer_json()
        id_empleado = _entero_positivo(datos.get("id_empleado"), "El empleado")
        contado = _dinero(datos.get("efectivo_contado"), "El efectivo contado", permitir_cero=True)
    except ValueError as error:
        return jsonify(ok=False, error=str(error)), 400

    conn = cursor = None
    try:
        conn = _cursor_db()
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_caja, fondo_inicial FROM cajas WHERE estado = 'Abierta' FOR UPDATE"
        )
        caja = cursor.fetchone()
        if not caja:
            conn.rollback()
            return jsonify(ok=False, error="No hay una caja abierta."), 409
        cursor.execute(
            """SELECT COALESCE(SUM(pg.monto), 0) AS total
               FROM caja_pagos cp JOIN pagos pg ON pg.id_pago = cp.id_pago
               WHERE cp.id_caja = %s AND pg.metodo = 'Efectivo' AND pg.estado = 'Registrado'""",
            (caja["id_caja"],),
        )
        ventas_efectivo = Decimal(str(cursor.fetchone()["total"] or 0))
        esperado = (Decimal(str(caja["fondo_inicial"])) + ventas_efectivo).quantize(Decimal("0.01"))
        diferencia = (contado - esperado).quantize(Decimal("0.01"))
        cursor.execute(
            """UPDATE cajas SET id_empleado_cierre = %s, efectivo_contado = %s,
                      efectivo_esperado = %s, diferencia = %s, estado = 'Cerrada',
                      fecha_cierre = CURRENT_TIMESTAMP
               WHERE id_caja = %s""",
            (id_empleado, contado, esperado, diferencia, caja["id_caja"]),
        )
        conn.commit()
        return jsonify(ok=True, esperado=float(esperado), diferencia=float(diferencia))
    except Exception as error:
        if conn and conn.is_connected():
            conn.rollback()
        app.logger.exception("Error al cerrar caja: %s", error)
        return jsonify(ok=False, error="No se pudo cerrar la caja."), 500
    finally:
        _cerrar(conn, cursor)


@app.post("/api/caja/cobrar")
def cobrar_pedido():
    try:
        datos = _leer_json()
        id_pedido = _entero_positivo(datos.get("id_pedido"), "El pedido")
        id_empleado = _entero_positivo(datos.get("id_empleado"), "El empleado")
        metodo = str(datos.get("metodo", "")).strip()
        if metodo not in {"Efectivo", "Tarjeta", "Transferencia", "Otro"}:
            raise ValueError("El método de pago no es válido.")
    except ValueError as error:
        return jsonify(ok=False, error=str(error)), 400

    conn = cursor = None
    try:
        conn = _cursor_db()
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_mesa, estado FROM pedidos WHERE id_pedido = %s FOR UPDATE",
            (id_pedido,),
        )
        pedido = cursor.fetchone()
        if not pedido:
            raise ValueError("No se encontró el pedido.")
        if pedido["estado"] != "Entregado":
            raise ValueError("Solo se puede cobrar un pedido que ya fue entregado.")
        cursor.execute(
            "SELECT id_pago FROM pagos WHERE id_pedido = %s AND estado = 'Registrado' LIMIT 1",
            (id_pedido,),
        )
        if cursor.fetchone():
            raise ValueError("Este pedido ya fue cobrado.")
        cursor.execute("SELECT id_caja FROM cajas WHERE estado = 'Abierta' FOR UPDATE")
        caja = cursor.fetchone()
        if not caja:
            raise ValueError("Abre la caja antes de cobrar pedidos.")

        total = _total_pedido(cursor, id_pedido)
        if total <= 0:
            raise ValueError("El pedido no tiene un total cobrable.")
        cursor.execute(
            "INSERT INTO pagos (id_pedido, id_empleado, metodo, monto) VALUES (%s, %s, %s, %s)",
            (id_pedido, id_empleado, metodo, total),
        )
        id_pago = int(cursor.lastrowid)
        cursor.execute(
            "INSERT INTO caja_pagos (id_pago, id_caja) VALUES (%s, %s)",
            (id_pago, caja["id_caja"]),
        )
        _liberar_mesa_si_corresponde(cursor, pedido["id_mesa"])
        conn.commit()
        return jsonify(ok=True, id_pago=id_pago, total=float(total))
    except ValueError as error:
        if conn and conn.is_connected():
            conn.rollback()
        return jsonify(ok=False, error=str(error)), 409
    except Exception as error:
        if conn and conn.is_connected():
            conn.rollback()
        app.logger.exception("Error al cobrar pedido: %s", error)
        return jsonify(ok=False, error="No se pudo registrar el pago."), 500
    finally:
        _cerrar(conn, cursor)


@app.get("/api/reportes/ventas")
def reporte_ventas():
    try:
        inicio = date.fromisoformat(request.args.get("desde", ""))
        fin = date.fromisoformat(request.args.get("hasta", ""))
        if fin < inicio:
            raise ValueError("La fecha final debe ser igual o posterior a la inicial.")
        if fin - inicio > timedelta(days=366):
            raise ValueError("El rango del reporte no puede superar un año.")
    except ValueError as error:
        return jsonify(error=str(error) or "Indica fechas válidas para el reporte."), 400

    conn = cursor = None
    try:
        conn = _cursor_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT pg.id_pago, pg.id_pedido, pg.metodo, pg.monto, pg.fecha,
                      m.numero_mesa, c.nombre AS cliente, e.nombre AS empleado
               FROM pagos pg
               JOIN pedidos p ON p.id_pedido = pg.id_pedido
               JOIN mesas m ON m.id_mesa = p.id_mesa
               JOIN empleados e ON e.id_empleado = pg.id_empleado
               LEFT JOIN clientes c ON c.id_cliente = p.id_cliente
               WHERE pg.estado = 'Registrado'
                 AND pg.fecha >= %s AND pg.fecha < %s
               ORDER BY pg.fecha DESC, pg.id_pago DESC""",
            (inicio, fin + timedelta(days=1)),
        )
        filas = cursor.fetchall()
        totales = {"Efectivo": Decimal("0.00"), "Tarjeta": Decimal("0.00"),
                   "Transferencia": Decimal("0.00"), "Otro": Decimal("0.00")}
        total = Decimal("0.00")
        for fila in filas:
            monto = Decimal(str(fila["monto"])).quantize(Decimal("0.01"))
            total += monto
            totales[fila["metodo"]] = totales.get(fila["metodo"], Decimal("0.00")) + monto
            fila["monto"] = float(monto)
            fila["fecha"] = fila["fecha"].strftime("%Y-%m-%d %H:%M")
            fila["id_pago"] = int(fila["id_pago"])
            fila["id_pedido"] = int(fila["id_pedido"])
            fila["numero_mesa"] = int(fila["numero_mesa"])
        return jsonify(
            desde=inicio.isoformat(), hasta=fin.isoformat(),
            total=float(total), pagos=len(filas),
            por_metodo={metodo: float(monto) for metodo, monto in totales.items()},
            filas=filas,
        )
    except Exception as error:
        app.logger.exception("Error al generar reporte de ventas: %s", error)
        return jsonify(error="No se pudo generar el reporte de ventas."), 500
    finally:
        _cerrar(conn, cursor)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
