const ModuloBarra = {
  render(pedidos, onCambiarEstado) {
    ['Pendiente', 'Preparando', 'Entregado'].forEach(estado => {
      const col = document.getElementById(`col-${estado.toLowerCase()}`);
      col.innerHTML = '';
      pedidos.filter(p => p.estado === estado).forEach(p => {
        const card = document.createElement('div');
        card.className = 'order-ticket-card';
        const sig = estado === 'Pendiente' ? 'Preparando' : estado === 'Preparando' ? 'Entregado' : null;
        card.innerHTML = `
          <strong>Mesa #${p.numero_mesa}</strong>
          <div style="margin:0.4rem 0; font-size:0.88rem;">
            ${p.items.map(i => `<div>• ${i.cantidad}x ${i.nombre} ${i.extras?.length ? `(+ ${i.extras.map(e => e.nombre).join(', ')})` : ''}</div>`).join('')}
          </div>
          ${sig ? `<button class="btn-brass" style="width:100%; margin-top:0.4rem;">Pasar a ${sig}</button>` : '<small>✔ Completado</small>'}
        `;
        if (sig) card.querySelector('button').onclick = () => onCambiarEstado(p.id_pedido, sig);
        col.appendChild(card);
      });
    });
  }
};