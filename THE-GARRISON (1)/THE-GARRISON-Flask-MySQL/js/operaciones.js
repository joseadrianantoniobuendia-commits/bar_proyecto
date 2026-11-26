const ModuloOperaciones = (() => {
  const API = '/api';
  let obtenerEmpleado = () => null;
  let alActualizarDatos = async () => {};

  const escapar = (valor) => String(valor ?? '').replace(/[&<>"']/g, (caracter) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[caracter]);

  const moneda = (valor) => new Intl.NumberFormat('es-MX', {
    style: 'currency', currency: 'MXN'
  }).format(Number(valor || 0));

  async function pedir(url, opciones = {}) {
    const respuesta = await fetch(`${API}${url}`, {
      headers: { 'Content-Type': 'application/json', ...(opciones.headers || {}) },
      ...opciones
    });
    const datos = await respuesta.json();
    if (!respuesta.ok) throw new Error(datos.error || 'No se pudo completar la operación.');
    return datos;
  }

  function mensaje(id, texto, error = false) {
    const elemento = document.getElementById(id);
    if (!elemento) return;
    elemento.textContent = texto;
    elemento.classList.toggle('error', error);
  }

  function empleadoActual() {
    const empleado = obtenerEmpleado();
    if (!empleado?.id_empleado) throw new Error('Vuelve a iniciar sesión para continuar.');
    return Number(empleado.id_empleado);
  }

  async function cargarCaja() {
    const panel = document.getElementById('caja-panel');
    const lista = document.getElementById('caja-pendientes');
    if (!panel || !lista) return;
    try {
      const datos = await pedir('/caja/resumen');
      if (datos.caja) {
        const cifras = Object.entries(datos.totales || {}).map(([metodo, total]) => `
          <div class="caja-cifra"><span>${escapar(metodo)}</span><strong>${moneda(total)}</strong></div>
        `).join('');
        panel.innerHTML = `
          <div class="caja-panel">
            <h3>Caja abierta · #${Number(datos.caja.id_caja)}</h3>
            <p>Apertura: ${escapar(datos.caja.fecha_apertura)} · ${escapar(datos.caja.empleado_apertura)}</p>
            <div class="caja-cifras">
              <div class="caja-cifra"><span>Fondo inicial</span><strong>${moneda(datos.caja.fondo_inicial)}</strong></div>
              ${cifras}
              <div class="caja-cifra"><span>Efectivo esperado</span><strong>${moneda(datos.caja.efectivo_esperado)}</strong></div>
            </div>
            <form id="form-cerrar-caja" class="operacion-form">
              <label>Efectivo contado al cierre<input id="caja-efectivo-contado" type="number" min="0" step="0.01" required></label>
              <button type="submit" class="btn-brass-full">Cerrar caja</button>
            </form>
          </div>`;
        document.getElementById('form-cerrar-caja').addEventListener('submit', cerrarCaja);
      } else {
        panel.innerHTML = `
          <div class="caja-panel">
            <h3>No hay una caja abierta</h3>
            <p>Registra el fondo con el que inicia el turno para comenzar a cobrar.</p>
            <form id="form-abrir-caja" class="operacion-form">
              <label>Fondo inicial en efectivo<input id="caja-fondo-inicial" type="number" min="0" step="0.01" value="0.00" required></label>
              <button type="submit" class="btn-brass-full">Abrir caja</button>
            </form>
          </div>`;
        document.getElementById('form-abrir-caja').addEventListener('submit', abrirCaja);
      }

      if (!datos.pendientes?.length) {
        lista.innerHTML = '<p class="operacion-ayuda">No hay pedidos entregados pendientes de cobro.</p>';
      } else {
        lista.innerHTML = datos.pendientes.map((pedido) => `
          <article class="caja-pedido">
            <h3>Pedido #${Number(pedido.id_pedido)} · Mesa ${Number(pedido.numero_mesa)}</h3>
            <p>Cliente: ${escapar(pedido.cliente || 'Público general')}</p>
            <strong>${moneda(pedido.total)}</strong>
            <label for="metodo-pago-${Number(pedido.id_pedido)}">Forma de pago</label>
            <select id="metodo-pago-${Number(pedido.id_pedido)}" ${datos.caja ? '' : 'disabled'}>
              <option>Efectivo</option><option>Tarjeta</option><option>Transferencia</option><option>Otro</option>
            </select>
            <button class="btn-brass" data-cobrar="${Number(pedido.id_pedido)}" ${datos.caja ? '' : 'disabled'}>Registrar cobro</button>
          </article>`).join('');
        lista.querySelectorAll('[data-cobrar]').forEach((boton) => {
          boton.addEventListener('click', () => cobrarPedido(Number(boton.dataset.cobrar)));
        });
      }
      mensaje('caja-mensaje', 'Caja actualizada.');
    } catch (error) {
      panel.innerHTML = '<p class="operacion-ayuda">No se pudo cargar la información de caja.</p>';
      lista.innerHTML = '';
      mensaje('caja-mensaje', error.message, true);
    }
  }

  async function abrirCaja(evento) {
    evento.preventDefault();
    try {
      await pedir('/caja/abrir', {
        method: 'POST',
        body: JSON.stringify({
          id_empleado: empleadoActual(),
          fondo_inicial: document.getElementById('caja-fondo-inicial').value
        })
      });
      mensaje('caja-mensaje', 'Caja abierta. Ya puedes registrar cobros.');
      await cargarCaja();
    } catch (error) {
      mensaje('caja-mensaje', error.message, true);
    }
  }

  async function cerrarCaja(evento) {
    evento.preventDefault();
    if (!confirm('¿Cerrar la caja con el efectivo contado indicado?')) return;
    try {
      const resultado = await pedir('/caja/cerrar', {
        method: 'POST',
        body: JSON.stringify({
          id_empleado: empleadoActual(),
          efectivo_contado: document.getElementById('caja-efectivo-contado').value
        })
      });
      mensaje('caja-mensaje', `Caja cerrada. Efectivo esperado: ${moneda(resultado.esperado)}. Diferencia: ${moneda(resultado.diferencia)}.`);
      await cargarCaja();
    } catch (error) {
      mensaje('caja-mensaje', error.message, true);
    }
  }

  async function cobrarPedido(idPedido) {
    const metodo = document.getElementById(`metodo-pago-${idPedido}`)?.value;
    if (!metodo || !confirm(`¿Registrar el cobro del pedido #${idPedido} con ${metodo.toLowerCase()}?`)) return;
    try {
      const resultado = await pedir('/caja/cobrar', {
        method: 'POST',
        body: JSON.stringify({ id_pedido: idPedido, id_empleado: empleadoActual(), metodo })
      });
      mensaje('caja-mensaje', `Cobro registrado: ${moneda(resultado.total)}.`);
      await alActualizarDatos();
      await cargarCaja();
    } catch (error) {
      mensaje('caja-mensaje', error.message, true);
    }
  }

  async function cargarInventario() {
    const existencias = document.getElementById('inventario-existencias');
    const movimientos = document.getElementById('inventario-movimientos');
    const select = document.getElementById('inventario-ingrediente');
    if (!existencias || !movimientos || !select) return;
    try {
      const datos = await pedir('/inventario');
      const seleccionado = select.value;
      select.innerHTML = datos.ingredientes.map((item) =>
        `<option value="${Number(item.id_ingrediente)}">${escapar(item.nombre)} (${escapar(item.unidad_base)})</option>`
      ).join('');
      if (datos.ingredientes.some((item) => String(item.id_ingrediente) === seleccionado)) select.value = seleccionado;
      existencias.innerHTML = datos.ingredientes.length ? datos.ingredientes.map((item) => `
        <tr><td>${escapar(item.nombre)}</td><td>${Number(item.existencia).toLocaleString('es-MX', { maximumFractionDigits: 2 })}</td><td>${escapar(item.unidad_base)}</td></tr>
      `).join('') : '<tr><td colspan="3">No hay ingredientes registrados.</td></tr>';
      movimientos.innerHTML = datos.movimientos.length ? datos.movimientos.map((item) => `
        <tr><td>${escapar(item.fecha)}</td><td>${escapar(item.ingrediente)}</td><td>${escapar(item.tipo)}</td>
        <td>${Number(item.cantidad).toLocaleString('es-MX', { maximumFractionDigits: 2 })} ${escapar(item.unidad_base)}</td>
        <td>${escapar(item.empleado)}</td><td>${escapar(item.notas || '')}</td></tr>
      `).join('') : '<tr><td colspan="6">Aún no hay movimientos registrados.</td></tr>';
      mensaje('inventario-mensaje', 'Inventario actualizado.');
    } catch (error) {
      existencias.innerHTML = `<tr><td colspan="3">${escapar(error.message)}</td></tr>`;
      movimientos.innerHTML = '';
      mensaje('inventario-mensaje', error.message, true);
    }
  }

  async function guardarMovimiento(evento) {
    evento.preventDefault();
    const boton = evento.currentTarget.querySelector('button[type="submit"]');
    boton.disabled = true;
    try {
      await pedir('/inventario/movimiento', {
        method: 'POST',
        body: JSON.stringify({
          id_ingrediente: document.getElementById('inventario-ingrediente').value,
          tipo: document.getElementById('inventario-tipo').value,
          cantidad: document.getElementById('inventario-cantidad').value,
          costo_unitario: document.getElementById('inventario-costo').value || null,
          notas: document.getElementById('inventario-notas').value,
          id_empleado: empleadoActual()
        })
      });
      mensaje('inventario-mensaje', 'Movimiento guardado en MySQL.');
      document.getElementById('inventario-cantidad').value = '';
      document.getElementById('inventario-costo').value = '';
      document.getElementById('inventario-notas').value = '';
      await cargarInventario();
    } catch (error) {
      mensaje('inventario-mensaje', error.message, true);
    } finally {
      boton.disabled = false;
    }
  }

  function hoyLocal() {
    const ahora = new Date();
    const fechaLocal = new Date(ahora.getTime() - ahora.getTimezoneOffset() * 60000);
    return fechaLocal.toISOString().slice(0, 10);
  }

  async function generarReporte(evento) {
    evento.preventDefault();
    const desde = document.getElementById('reporte-desde').value;
    const hasta = document.getElementById('reporte-hasta').value;
    try {
      const datos = await pedir(`/reportes/ventas?desde=${encodeURIComponent(desde)}&hasta=${encodeURIComponent(hasta)}`);
      const tarjetas = [
        ['Ventas cobradas', moneda(datos.total)], ['Número de pagos', datos.pagos],
        ...Object.entries(datos.por_metodo).map(([metodo, total]) => [metodo, moneda(total)])
      ];
      document.getElementById('reporte-resumen').innerHTML = tarjetas.map(([titulo, valor]) => `
        <div class="caja-cifra"><span>${escapar(titulo)}</span><strong>${escapar(valor)}</strong></div>
      `).join('');
      const filas = document.getElementById('reporte-filas');
      filas.innerHTML = datos.filas.length ? datos.filas.map((fila) => `
        <tr><td>${escapar(fila.fecha)}</td><td>#${Number(fila.id_pedido)}</td><td>${Number(fila.numero_mesa)}</td>
        <td>${escapar(fila.cliente || 'Público general')}</td><td>${escapar(fila.empleado)}</td>
        <td>${escapar(fila.metodo)}</td><td>${moneda(fila.monto)}</td></tr>
      `).join('') : '<tr><td colspan="7">No hay cobros en ese rango de fechas.</td></tr>';
      mensaje('reportes-mensaje', `Reporte del ${datos.desde} al ${datos.hasta}.`);
    } catch (error) {
      document.getElementById('reporte-resumen').innerHTML = '';
      document.getElementById('reporte-filas').innerHTML = '<tr><td colspan="7">No se pudo generar el reporte.</td></tr>';
      mensaje('reportes-mensaje', error.message, true);
    }
  }

  function iniciar(opciones = {}) {
    obtenerEmpleado = opciones.obtenerEmpleado || obtenerEmpleado;
    alActualizarDatos = opciones.alActualizarDatos || alActualizarDatos;
    document.getElementById('btn-actualizar-caja')?.addEventListener('click', cargarCaja);
    document.getElementById('btn-actualizar-inventario')?.addEventListener('click', cargarInventario);
    document.getElementById('form-movimiento-inventario')?.addEventListener('submit', guardarMovimiento);
    document.getElementById('form-reporte-ventas')?.addEventListener('submit', generarReporte);
    const hoy = hoyLocal();
    document.getElementById('reporte-desde').value = hoy;
    document.getElementById('reporte-hasta').value = hoy;
  }

  function cargarVista(vista) {
    if (vista === 'caja') return cargarCaja();
    if (vista === 'inventario') return cargarInventario();
  }

  return { iniciar, cargarVista };
})();
