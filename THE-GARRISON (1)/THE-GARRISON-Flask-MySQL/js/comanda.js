const ModuloComanda = {
  abrirExtras(bebida, extras, onConfirmar) {
    const modal = document.getElementById('modal-extras');
    const titulo = document.getElementById('modal-bebida-titulo');
    const lista = document.getElementById('lista-extras-checks');
    const elegidos = [];

    titulo.textContent = `${bebida.nombre} ($${bebida.precio.toFixed(2)})`;
    lista.innerHTML = '';

    extras.forEach(ext => {
      const label = document.createElement('label');
      label.className = 'extra-row';
      label.innerHTML = `
        <span><input type="checkbox" /> ${ext.nombre}</span>
        <strong>+$${ext.precio.toFixed(2)}</strong>
      `;
      label.querySelector('input').onchange = (e) => {
        if (e.target.checked) elegidos.push(ext);
        else elegidos.splice(elegidos.indexOf(ext), 1);
      };
      lista.appendChild(label);
    });

    modal.style.display = 'flex';
    document.getElementById('cerrar-modal-extras').onclick = () => modal.style.display = 'none';
    document.getElementById('confirmar-extras').onclick = () => {
      onConfirmar(elegidos);
      modal.style.display = 'none';
    };
  }
};