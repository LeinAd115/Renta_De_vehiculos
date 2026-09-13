document.getElementById('btnIngresar').addEventListener('click', async () => {
    const usuario = document.querySelector('input[name="Usuario"]').value.trim();
    const contrasena = document.querySelector('input[name="Contraseña"]').value.trim();

    const errorPrevio = document.getElementById('mensajeError');
    if (errorPrevio) errorPrevio.remove();

    const respuesta = await fetch('/validar_login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ usuario, contrasena })
    });

    const datos = await respuesta.json();

    if (datos.success) {
        window.location.href = '/punto_renta';
    } else {
        const mensaje = document.createElement('p');
        mensaje.id = 'mensajeError';
        mensaje.textContent = datos.mensaje;
        mensaje.style.cssText = `
            color: #e74c3c;
            background: #fdecea;
            border: 1px solid #e74c3c;
            border-radius: 6px;
            padding: 8px 12px;
            margin-top: 10px;
            font-size: 0.85rem;
            text-align: center;
        `;
        document.querySelector('.ingreso').appendChild(mensaje);
    }
});

document.getElementById('btnRC').addEventListener('click', () => {
    const popup = document.createElement('div');
    popup.id = 'popupRC';
    popup.style.cssText = `
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background: rgba(0,0,0,0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 999;
    `;
    popup.innerHTML = `
        <div style="background:white; padding:30px; border-radius:12px; width:300px; display:flex; flex-direction:column; gap:10px;">
            <h3 style="text-align:center; color:#2c3e50;">Recuperar Contraseña</h3>
            <label style="font-weight:bold;">Nombre:</label>
            <input type="text" id="rcNombre" style="padding:8px; border-radius:6px; border:1px solid #ccc;">
            <label style="font-weight:bold;">Rol:</label>
            <select id="rcRol" style="padding:8px; border-radius:6px; border:1px solid #ccc;">
                
                <option value="auxiliar">Auxiliar</option>
                <option value="caja">Caja</option>
            </select>
            <button id="btnEnviarRC" style="background:#4ca1af; color:white; padding:10px; border:none; border-radius:6px; cursor:pointer;">Enviar correo</button>
            <button id="btnCerrarRC" style="background:#bdc3c7; padding:10px; border:none; border-radius:6px; cursor:pointer;">Cancelar</button>
            <p id="mensajeRC" style="text-align:center; font-size:0.85rem;"></p>
        </div>
    `;
    document.body.appendChild(popup);

    document.getElementById('btnCerrarRC').addEventListener('click', () => popup.remove());

    document.getElementById('btnEnviarRC').addEventListener('click', async () => {
        const nombre = document.getElementById('rcNombre').value.trim();
        const rol = document.getElementById('rcRol').value;
        const mensajeRC = document.getElementById('mensajeRC');

        const respuesta = await fetch('/recuperar_contrasena', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, rol })
        });

        const datos = await respuesta.json();

        if (datos.success) {
            mensajeRC.style.color = 'green';
            mensajeRC.textContent =  datos.mensaje;
            setTimeout(() => popup.remove(), 3000);
        } else {
            mensajeRC.style.color = 'red';
            mensajeRC.textContent =  datos.mensaje;
        }
    });
});