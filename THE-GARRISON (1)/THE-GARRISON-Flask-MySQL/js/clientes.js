const ModuloClientes = {
  render(clientes, onAsignar) {
    const cont = document.getElementById('clientes-lista');
    cont.innerHTML = '';
    clientes.forEach(c => {
      const card = document.createElement('div');
      card.className = 'cliente-card';
      card.innerHTML = `
        <strong style="color:var(--brass-light)">${c.nombre}</strong>
        <span>📞 ${c.telefono}</span>
        <small style="color:var(--text-muted)">${c.correo || 'Sin correo'}</small>
        <button class="btn-brass">Asignar a Comanda</button>
      `;
      card.querySelector('button').onclick = () => onAsignar(c);
      cont.appendChild(card);
    });
  }
};