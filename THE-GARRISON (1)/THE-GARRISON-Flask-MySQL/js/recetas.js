const ModuloRecetas = {
  render(recetas) {
    const cont = document.getElementById('recetas-grid');
    cont.innerHTML = recetas.map(r => `
      <article class="receta-card">
        <h3>${r.bebida}</h3>
        <p style="color:var(--brass-gold); font-size:0.85rem; margin-bottom:0.6rem;">Método: ${r.metodo}</p>
        <ul style="margin-left:1.1rem; margin-bottom:0.7rem; font-size:0.9rem;">
          ${r.ingredientes.map(i => `<li>${i.cantidad} ${i.unidad} — ${i.nombre}</li>`).join('')}
        </ul>
        <p style="font-size:0.88rem; margin-bottom:0.5rem;"><strong>Preparación:</strong> ${r.preparacion}</p>
        <small style="color:var(--text-muted)"><strong>Decoración:</strong> ${r.decoracion}</small>
      </article>
    `).join('');
  }
};