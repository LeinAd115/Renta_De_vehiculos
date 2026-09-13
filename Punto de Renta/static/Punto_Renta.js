

const RUTAS = {
    'renta_activa':  '/renta_activa',
    'guardados':     '/guardados',
    'configuracion': '/configuracion',
    'corte':         '/corte',
    'reportes':      '/reportes',
    'red_neuronal':  '/red_neuronal',
};

// Navegar al módulo
function abrirModulo(modulo) {
    const ruta = RUTAS[modulo];
    if (ruta) {
        window.location.href = ruta;
    } else {
        console.warn('Módulo no registrado:', modulo);
    }
}

// ── Asignar eventos a los botones del grid ──
document.addEventListener('DOMContentLoaded', () => {

    // Cada .mod-card tiene un data-modulo="nombre"
    // Los botones "Abrir" dentro de cada tarjeta
    document.querySelectorAll('.mod-card').forEach(card => {
        const modulo = card.dataset.modulo;

        // Clic en la tarjeta completa
        card.addEventListener('click', () => abrirModulo(modulo));

        // Clic en el botón "Abrir" (evita doble disparo)
        const btn = card.querySelector('.mod-btn');
        if (btn) {
            btn.addEventListener('click', e => {
                e.stopPropagation();
                abrirModulo(modulo);
            });
        }
    });


    const userSpan = document.querySelector('.user-info span');
    if (userSpan) userSpan.style.fontWeight = 'bold';
});
