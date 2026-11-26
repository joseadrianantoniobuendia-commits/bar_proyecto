document.addEventListener('DOMContentLoaded', () => {
  const API_URL = '/api';

  const loginScreen = document.getElementById('login-screen');
  const posApp = document.getElementById('pos-app');
  const loginForm = document.getElementById('login-form');
  const errorMsg = document.getElementById('login-error');

  // La interfaz trabaja con los datos que entrega MySQL; no mantiene catálogos de demostración.
  let mesasDB = [];
  let bebidasDB = [];
  let extrasDB = [];
  let clientesDB = [];
  let pedidosDB = [];
  let recetasDB = [];

  let mesaActual = null;
  let clienteActual = null;
  let carrito = [];
  let categoriaActiva = 'Todas';

  // Sincronización con MySQL (cantinadb)
  async function sincronizarConMySQL() {
    try {
      const res = await fetch(`${API_URL}/datos_iniciales`);
      if (!res.ok) throw new Error('API no disponible');
      const data = await res.json();

      if (Array.isArray(data.mesas)) mesasDB = data.mesas;
      if (Array.isArray(data.bebidas)) bebidasDB = data.bebidas;
      if (Array.isArray(data.extras)) extrasDB = data.extras;
      if (Array.isArray(data.clientes)) clientesDB = data.clientes;
      if (Array.isArray(data.recetas) && data.recetas.length > 0) recetasDB = data.recetas;
      if (Array.isArray(data.pedidos)) pedidosDB = data.pedidos;
      return true;
    } catch (err) {
      console.warn('No se pudo sincronizar con MySQL:', err.message);
      return false;
    }
  }

  // Login independiente
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const u = document.getElementById('username').value.trim().toLowerCase();
    const p = document.getElementById('password').value.trim();

    let emp = null;
    let apiResponded = false;

    // La API valida el PIN y devuelve los datos del empleado.
    try {
      const res = await fetch(`${API_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ usuario: u, pin: p })
      });
      apiResponded = true;
      const data = await res.json();
      if (res.ok && data.ok && data.empleado) emp = data.empleado;
      else {
        errorMsg.textContent = data.error || 'Credenciales incorrectas.';
        return;
      }
    } catch (_) {
      if (apiResponded) {
        errorMsg.textContent = 'El servidor respondió con un mensaje inválido.';
        return;
      }
    }

    if (!emp) {
      errorMsg.textContent = apiResponded
        ? 'Credenciales incorrectas.'
        : 'No hay conexión con la API. Inicia MySQL y la tarea Flask de VS Code.';
      return;
    }

    errorMsg.textContent = '';
    sessionStorage.setItem('garrison_user', JSON.stringify(emp));
    await entrarAlSistema(emp);
  });

  // Volver al Login independiente
  document.getElementById('btn-logout').addEventListener('click', () => {
    sessionStorage.removeItem('garrison_user');
    posApp.style.display = 'none';
    loginScreen.style.display = 'flex';
    loginForm.reset();
  });

  // Navegación entre apartados separados
  document.querySelectorAll('.nav-pill').forEach(btn => {
    btn.addEventListener('click', () => cambiarVista(btn.dataset.vista));
  });

  function cambiarVista(vista) {
    document.querySelectorAll('.nav-pill').forEach(b => b.classList.toggle('active', b.dataset.vista === vista));
    document.querySelectorAll('.vista-seccion').forEach(s => s.style.display = 'none');
    document.getElementById(`vista-${vista}`).style.display = 'block';

    // Cambiar fondo ambiental según zona
    posApp.className = (vista === 'barra' || vista === 'recetas') ? 'app-shell bg-barra' : 'app-shell bg-salon';
    ModuloOperaciones.cargarVista(vista);
  }

  async function entrarAlSistema(emp) {
    loginScreen.style.display = 'none';
    posApp.style.display = 'block';
    document.getElementById('empleado-activo').textContent = `${emp.nombre} (${emp.rol})`;

    const conectado = await sincronizarConMySQL();
    if (!conectado) {
      sessionStorage.removeItem('garrison_user');
      posApp.style.display = 'none';
      loginScreen.style.display = 'flex';
      errorMsg.textContent = 'No se pudieron cargar los datos. Revisa MySQL y vuelve a intentar.';
      return;
    }
    renderTodo();
    cambiarVista(emp.rol === 'Bartender' ? 'barra' : 'mesas');
  }

  function renderTodo() {
    ModuloMesas.render(mesasDB, mesaActual, (mesa) => {
      mesaActual = mesa;
      document.getElementById('ticket-mesa-info').textContent = `Mesa: #${mesa.numero_mesa}`;
      renderTodo();
      cambiarVista('comanda');
    });

    ModuloClientes.render(clientesDB, (cli) => {
      clienteActual = cli;
      document.getElementById('ticket-cliente-info').textContent = `Cliente: ${cli.nombre}`;
      cambiarVista('comanda');
    });

    ModuloBarra.render(pedidosDB, async (idPedido, nuevoEstado) => {
      try {
        const sesion = JSON.parse(sessionStorage.getItem('garrison_user') || '{}');
        const res = await fetch(`${API_URL}/actualizar_estado_pedido`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id_pedido: idPedido, estado: nuevoEstado, id_empleado: sesion.id_empleado })
        });
        const datos = await res.json();
        if (!res.ok) throw new Error(datos.error || 'El servidor rechazó el cambio.');
        await sincronizarConMySQL();
      } catch (error) {
        alert(error.message || 'No se pudo actualizar el pedido en MySQL.');
        return;
      }

      renderTodo();
    });

    ModuloRecetas.render(recetasDB);
    renderCatalogoBebidas();
    renderTicket();
  }

  function renderCatalogoBebidas() {
    const cats = ['Todas', ...new Set(bebidasDB.map(b => b.categoria))];
    const catBar = document.getElementById('categorias-filter');
    catBar.innerHTML = cats.map(c => `<button class="cat-btn ${c === categoriaActiva ? 'active' : ''}">${c}</button>`).join('');
    catBar.querySelectorAll('button').forEach(btn => {
      btn.onclick = () => { categoriaActiva = btn.textContent; renderCatalogoBebidas(); };
    });

    const grid = document.getElementById('bebidas-catalogo');
    const filtradas = categoriaActiva === 'Todas' ? bebidasDB : bebidasDB.filter(b => b.categoria === categoriaActiva);
    grid.innerHTML = '';

    filtradas.forEach(b => {
      const card = document.createElement('div');
      card.className = 'bebida-item-card';
      card.innerHTML = `
        <div>
          <strong>${b.nombre}</strong>
          <div style="color:var(--brass-light); margin-top:0.3rem;">$${Number(b.precio).toFixed(2)}</div>
        </div>
        <button class="btn-brass">+ Añadir</button>
      `;
      card.querySelector('button').onclick = () => {
        if (!mesaActual) {
          alert('Primero selecciona una mesa en el apartado Mesas.');
          cambiarVista('mesas');
          return;
        }
        const extrasDeEstaBebida = Array.isArray(b.extras_permitidos)
          ? extrasDB.filter(ext => b.extras_permitidos.includes(Number(ext.id_extra)))
          : extrasDB;
        ModuloComanda.abrirExtras(b, extrasDeEstaBebida, (extrasElegidos) => {
          const totalExtras = extrasElegidos.reduce((s, e) => s + Number(e.precio), 0);
          const existente = carrito.find(
            item => item.id_presentacion === b.id_presentacion &&
                    JSON.stringify(item.extras.map(e => e.id_extra).sort()) === JSON.stringify(extrasElegidos.map(e => e.id_extra).sort())
          );

          if (existente) {
            existente.cantidad += 1;
            existente.subtotal += Number(b.precio) + totalExtras;
          } else {
            carrito.push({
              ...b,
              cantidad: 1,
              extras: extrasElegidos,
              subtotal: Number(b.precio) + totalExtras
            });
          }
          renderTicket();
        });
      };
      grid.appendChild(card);
    });
  }

  function renderTicket() {
    const lista = document.getElementById('ticket-lista');
    lista.innerHTML = '';
    let total = 0;

    carrito.forEach(item => {
      total += item.subtotal;
      const li = document.createElement('li');
      li.className = 'ticket-row';
      li.innerHTML = `
        <span>${item.cantidad}x ${item.nombre} ${item.extras.length ? `<br><small style="color:var(--text-muted)">+ ${item.extras.map(e => e.nombre).join(', ')}</small>` : ''}</span>
        <strong>$${item.subtotal.toFixed(2)}</strong>
      `;
      lista.appendChild(li);
    });

    document.getElementById('ticket-total').textContent = `$${total.toFixed(2)}`;
    document.getElementById('btn-enviar-barra').disabled = !(mesaActual && carrito.length > 0);
  }

  // Enviar pedido a MySQL y a la vista Barra
  document.getElementById('btn-enviar-barra').addEventListener('click', async () => {
    const sesion = JSON.parse(sessionStorage.getItem('garrison_user') || '{}');
    const payload = {
      id_cliente: clienteActual ? clienteActual.id_cliente : null,
      id_empleado: sesion.id_empleado || 1,
      id_mesa: mesaActual.id_mesa,
      items: carrito
    };

    try {
      const res = await fetch(`${API_URL}/crear_pedido`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok || !data.id_pedido) throw new Error(data.error || 'No se pudo guardar el pedido.');
      pedidosDB.push({
        id_pedido: data.id_pedido,
        numero_mesa: mesaActual.numero_mesa,
        estado: 'Pendiente',
        items: [...carrito]
      });
    } catch (err) {
      alert(err.message || 'No se pudo conectar con MySQL. El pedido no se guardó.');
      return;
    }

    mesaActual.estado = 'Ocupada';
    carrito = [];
    renderTodo();
    cambiarVista('barra');
  });

  // Registrar cliente en MySQL y asignarlo a la comanda
  document.getElementById('form-nuevo-cliente').addEventListener('submit', async (e) => {
    e.preventDefault();
    const datosCliente = {
      nombre: document.getElementById('cli-nombre').value.trim(),
      telefono: document.getElementById('cli-telefono').value.trim(),
      correo: document.getElementById('cli-correo').value.trim()
    };

    try {
      const res = await fetch(`${API_URL}/crear_cliente`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(datosCliente)
      });
      const data = await res.json();
      if (!res.ok || !data.id_cliente) throw new Error(data.error || 'No se pudo registrar el cliente.');
      const nuevoCliente = data.cliente || { id_cliente: data.id_cliente, ...datosCliente };

      clientesDB.push(nuevoCliente);
      clienteActual = nuevoCliente;
      document.getElementById('ticket-cliente-info').textContent = `Cliente: ${nuevoCliente.nombre}`;
      e.target.reset();
      renderTodo();
      cambiarVista('comanda');
    } catch (err) {
      alert(err.message || 'No se pudo conectar con MySQL. El cliente no se registró.');
    }
  });

  const saved = sessionStorage.getItem('garrison_user');
  ModuloOperaciones.iniciar({
    obtenerEmpleado: () => JSON.parse(sessionStorage.getItem('garrison_user') || 'null'),
    alActualizarDatos: async () => {
      await sincronizarConMySQL();
      renderTodo();
    }
  });
  if (saved) entrarAlSistema(JSON.parse(saved));
});
