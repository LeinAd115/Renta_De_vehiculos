from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_mail import Mail, Message
import mysql.connector
import bcrypt
import random
import string
import re
from datetime import timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = 'amistoso'

# ── Expiración de sesión por inactividad (RNF03) ───────────────────────────────
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# ── Configuración de correo ────────────────────────────────────────────────────
app.config['MAIL_SERVER']         = 'smtp.gmail.com'
app.config['MAIL_PORT']           = 587
app.config['MAIL_USE_TLS']        = True
app.config['MAIL_USE_SSL']        = False
app.config['MAIL_USERNAME']       = 'losamistosos12@gmail.com'
app.config['MAIL_PASSWORD']       = 'rjabjxiabmcscpic'
app.config['MAIL_DEFAULT_SENDER'] = 'losamistosos12@gmail.com'

mail = Mail(app)

# ── Control de acceso por rol (RF02) ──────────────────────────────────────────
PERMISOS_POR_ROL = {
    'caja':     ['renta_activa', 'guardados', 'configuracion', 'corte', 'reportes', 'red_neuronal'],
    'auxiliar': ['renta_activa', 'guardados'],
}

def tiene_permiso(modulo):
    rol = session.get('rol')
    return modulo in PERMISOS_POR_ROL.get(rol, [])

# ── Decorador: requiere sesión activa ─────────────────────────────────────────
def login_requerido(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login'))
        # Renovar sesión en cada request (RNF03)
        session.modified = True
        return f(*args, **kwargs)
    return wrapper

# ── Decorador: requiere permiso de módulo ─────────────────────────────────────
def permiso_requerido(modulo):
    def decorador(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'usuario' not in session:
                return redirect(url_for('login'))
            session.modified = True
            if not tiene_permiso(modulo):
                return redirect(url_for('punto_renta'))
            return f(*args, **kwargs)
        return wrapper
    return decorador

# ── Base de datos ──────────────────────────────────────────────────────────────
def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='alex12.a',
        database='amistoso'
    )

# ── Validación de complejidad de contraseña (RNF02) ───────────────────────────
def validar_complejidad(contrasena):
    """
    Mínimo 8 caracteres, al menos 1 mayúscula y 1 número.
    Retorna (True, '') si es válida, (False, mensaje) si no.
    """
    if len(contrasena) < 8:
        return False, 'La contraseña debe tener al menos 8 caracteres.'
    if not re.search(r'[A-Z]', contrasena):
        return False, 'La contraseña debe tener al menos una mayúscula.'
    if not re.search(r'\d', contrasena):
        return False, 'La contraseña debe tener al menos un número.'
    return True, ''

# ── Registro de accesos (RNF04) ───────────────────────────────────────────────
def registrar_acceso(usuario, resultado, ip):
    """
    Inserta un registro en LogAccesos.
    Tabla esperada:
        CREATE TABLE LogAccesos (
            id        INT AUTO_INCREMENT PRIMARY KEY,
            usuario   VARCHAR(100),
            resultado ENUM('exito', 'fallo'),
            ip        VARCHAR(45),
            fecha     DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO LogAccesos (usuario, resultado, ip) VALUES (%s, %s, %s)',
            (usuario, resultado, ip)
        )
        db.commit()
        cursor.close()
        db.close()
    except Exception:
        pass  # El log nunca debe interrumpir el flujo principal

# ── Hash de contraseña (RNF02) ────────────────────────────────────────────────
def hashear(contrasena: str) -> str:
    return bcrypt.hashpw(contrasena.encode(), bcrypt.gensalt()).decode()

def verificar_hash(contrasena: str, hash_guardado: str) -> bool:
    return bcrypt.checkpw(contrasena.encode(), hash_guardado.encode())

def generar_contrasena_temporal():
    """Genera una contraseña que cumple la política: mayúscula + número + chars."""
    base = random.choices(string.ascii_lowercase, k=4)
    base += random.choices(string.ascii_uppercase, k=2)
    base += random.choices(string.digits, k=2)
    random.shuffle(base)
    return ''.join(base)

# ══════════════════════════════════════════════════════════════════════════════
# RUTAS
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def login():
    return render_template('Login.html')

# ── RF01: Iniciar sesión ───────────────────────────────────────────────────────
@app.route('/validar_login', methods=['POST'])
def validar_login():
    datos      = request.get_json()
    usuario    = datos.get('usuario', '').strip()
    contrasena = datos.get('contrasena', '').strip()
    ip         = request.remote_addr

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute('SELECT * FROM Empleados WHERE usuario = %s', (usuario,))
        empleado = cursor.fetchone()
        cursor.close()
        db.close()

        if empleado and verificar_hash(contrasena, empleado['contrasena']):
            session.permanent = True          # Activa expiración por inactividad (RNF03)
            session['usuario'] = empleado['usuario']
            session['rol']     = empleado['rol']
            registrar_acceso(usuario, 'exito', ip)   # RNF04
            return jsonify({'success': True})
        else:
            registrar_acceso(usuario, 'fallo', ip)   # RNF04
            return jsonify({'success': False, 'mensaje': 'Usuario o contraseña incorrectos'})

    except Exception as e:
        return jsonify({'success': False, 'mensaje': str(e)})

# ── RF03: Recuperar contraseña ────────────────────────────────────────────────
@app.route('/recuperar_contrasena', methods=['POST'])
def recuperar_contrasena():
    datos  = request.get_json()
    nombre = datos.get('nombre', '').strip()
    rol    = datos.get('rol', '').strip()

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM Empleados WHERE Nombre = %s AND rol = %s',
            (nombre, rol)
        )
        empleado = cursor.fetchone()

        if empleado:
            contrasena_temporal = generar_contrasena_temporal()
            hash_temporal       = hashear(contrasena_temporal)   # RNF02: se guarda hasheada

            cursor.execute(
                'UPDATE Empleados SET contrasena = %s WHERE Nombre = %s AND rol = %s',
                (hash_temporal, nombre, rol)
            )
            db.commit()

            msg = Message(
                subject='Recuperación de contraseña - Punto de Renta',
                sender='losamistosos12@gmail.com',
                recipients=[empleado['correo']]
            )
            msg.body = (
                f"Hola {empleado['Nombre']},\n\n"
                f"Tu contraseña temporal es: {contrasena_temporal}\n\n"
                f"Por seguridad, cámbiala en tu próximo inicio de sesión."
            )
            mail.send(msg)

            cursor.close()
            db.close()
            return jsonify({'success': True, 'mensaje': 'Correo enviado exitosamente'})
        else:
            cursor.close()
            db.close()
            return jsonify({'success': False, 'mensaje': 'No se encontró ningún empleado con esos datos'})

    except Exception as e:
        return jsonify({'success': False, 'mensaje': str(e)})

# ── RF04: Cerrar sesión ───────────────────────────────────────────────────────
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── Menú principal ────────────────────────────────────────────────────────────
@app.route('/punto_renta')
@login_requerido
def punto_renta():
    permisos = PERMISOS_POR_ROL.get(session['rol'], [])
    return render_template('puntoRenta.html', rol=session['rol'], permisos=permisos)

# ── Módulos accesibles para todos los roles ───────────────────────────────────
@app.route('/renta_activa')
@login_requerido
def renta_activa():
    return render_template('RentaActiva.html')

@app.route('/guardados')
@login_requerido
def guardados():
    return render_template('Guardados.html')

# ── Módulos restringidos — solo rol 'caja' ────────────────────────────────────
@app.route('/configuracion')
@permiso_requerido('configuracion')
def configuracion():
    return render_template('Configuracion.html')

@app.route('/corte')
@permiso_requerido('corte')
def corte():
    return render_template('Corte.html')

@app.route('/reportes')
@permiso_requerido('reportes')
def reportes():
    return render_template('Reportes.html')

@app.route('/red_neuronal')
@permiso_requerido('red_neuronal')
def red_neuronal():
    return render_template('RedNeuronal.html')

# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True)