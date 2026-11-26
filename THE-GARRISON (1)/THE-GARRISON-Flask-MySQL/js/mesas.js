const ModuloMesas = {
  render(mesas, mesaSeleccionada, onSelect) {
    const cont = document.getElementById('mesas-floor-plan');
    cont.innerHTML = '';
    mesas.forEach(m => {
      const div = document.createElement('div');
      const forma = m.capacidad <= 4 ? 'round' : '';
      const activa = mesaSeleccionada?.id_mesa === m.id_mesa ? 'selected' : '';
      div.className = `mesa-node ${forma} ${m.estado} ${activa}`;
      div.innerHTML = `
        <div class="mesa-num">${m.numero_mesa}</div>
        <div>MESA ${m.numero_mesa} - ${m.estado.toUpperCase()}</div>
        <small style="color:var(--text-muted)">Capacidad: ${m.capacidad} pers.</small>
      `;
      div.onclick = () => onSelect(m);
      cont.appendChild(div);
    });
  }
};