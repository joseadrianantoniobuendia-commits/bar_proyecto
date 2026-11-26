# THE GARRISON · Flask + MySQL

Sistema de cantina para Visual Studio Code. Flask sirve la interfaz y la API desde el mismo proceso. El proyecto no necesita XAMPP, Apache, PHP, Live Server ni extensiones de VS Code.

## Qué incluye

- Plano de mesas, comandas, clientes, cola de barra y recetario conectados a MySQL.
- Caja: apertura por turno, cobro de pedidos entregados y cierre con diferencia de efectivo.
- Inventario de ingredientes: entradas, ajustes, mermas e historial de movimientos.
- Al entregar una bebida con receta, descuenta los ingredientes de la existencia y guarda el movimiento. Si no hay suficiente, no marca el pedido como entregado.
- Reporte de ventas cobradas por fechas y forma de pago.
- Contraseñas PIN guardadas con hash.

## Requisitos

- Visual Studio Code.
- Python 3.10 o posterior.
- MySQL Server local y su cliente de consola.

## Preparar una base de datos nueva

Inicia el servicio MySQL. En la terminal integrada de VS Code, desde la carpeta del proyecto, abre MySQL:

```powershell
mysql --user=root --password
```

Si PowerShell dice que `mysql` no se reconoce y usas la instalación predeterminada de MySQL 8.4, abre el cliente con la ruta completa:

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" --user=root --password
```

En el prompt `mysql>`, ejecuta estos archivos en orden:

```sql
SOURCE database/cantinadb_demo_reset.sql;
SOURCE database/01_seguridad_pin.sql;
SOURCE database/02_operacion.sql;
SOURCE database/03_caja_inventario.sql;
```

`cantinadb_demo_reset.sql` borra y reconstruye las tablas de `cantinadb`. Úsalo solo para una instalación de prueba nueva. `01`, `02` y `03` se ejecutan una sola vez, en ese orden.

Después crea un usuario de aplicación con una contraseña propia. Sustituye el texto de ejemplo y no compartas esa clave:

```sql
CREATE USER 'garrison_app'@'localhost' IDENTIFIED BY 'PON_AQUI_UNA_CLAVE_LARGA';
GRANT SELECT, INSERT, UPDATE, DELETE ON cantinadb.* TO 'garrison_app'@'localhost';
EXIT;
```

Si el usuario ya existe, cambia su clave con `ALTER USER` en vez de repetir `CREATE USER`.

## Actualizar la base que ya tenías

Si ya aplicaste las migraciones `01_seguridad_pin.sql` y `02_operacion.sql`, ejecuta **solo una vez** `database/03_caja_inventario.sql`. No vuelvas a ejecutar `cantinadb_demo_reset.sql`, porque elimina los registros existentes.

## Configurar la conexión

En PowerShell, desde la carpeta del proyecto:

```powershell
Copy-Item backend/config_local.example.py backend/config_local.py
```

Abre `backend/config_local.py` y escribe tu contraseña local de MySQL. Ese archivo está ignorado por Git y no se incluye en el ZIP.

## Instalar y abrir

Desde VS Code, selecciona **Terminal > Run Task** (o `Ctrl+Shift+P` y busca **Tasks: Run Task**):

1. Ejecuta **THE GARRISON: instalar dependencias** una vez.
2. Ejecuta **THE GARRISON: iniciar aplicación**.
3. Abre `http://127.0.0.1:5000/`.

También puedes iniciar Flask desde PowerShell:

```powershell
cd backend
python app.py
```

Mantén esa terminal abierta mientras uses el sistema.

## Primer uso de caja e inventario

Inicia sesión con una cuenta de demostración existente. Abre **Inventario** y registra las existencias reales o de prueba de los ingredientes. La migración crea esas existencias en cero para no inventar cantidades.

Abre **Caja** e indica el fondo inicial. Cuando un pedido llegue a **Entregado**, puedes cobrarlo desde Caja. El cobro se suma al reporte y el efectivo se toma en cuenta para el cierre.

Los pedidos preparados con recetas descuentan ingredientes al pasar a **Entregado**. Los ingredientes cuya unidad de receta no coincide con su unidad base se omiten para evitar conversiones incorrectas. Los extras no ligados a recetas tampoco descuentan inventario.

## Seguridad y límites

No incluyas `backend/config_local.py`, `.venv` ni contraseñas en la entrega. Cambia o elimina las cuentas de demostración antes de usar datos reales. La autenticación es didáctica y no gestiona sesiones protegidas en el servidor; no publiques esta versión en internet sin completar esos controles.
