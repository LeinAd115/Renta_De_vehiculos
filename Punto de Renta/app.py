from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from database import DatabaseConnection
from auth_service import AuthService
from punto_renta_service import PuntoRentaService
from renta_activa_service import RentaActivaService
from configuracion_service import ConfiguracionService
import functools

app = Flask(__name__)
app.secret_key = "clave_secreta_para_sesiones_flask"

db = DatabaseConnection(host="localhost", user="root", password="danixGd2", database="amistoso", port=3306)
auth_srv = AuthService(db)
renta_srv = PuntoRentaService(db)
activa_srv = RentaActivaService(db)
config_srv = ConfiguracionService(db)

def login_required(modulo_solicitado):
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(*args, **kwargs):
            if 'usuario' not in session:
                flash("Debes iniciar sesión para acceder.", "warning")
                return redirect(url_for('vista_login'))
            
            rol = session.get('rol')
            if rol == 'ADMINISTRADOR':
                return view_func(*args, **kwargs)
            elif rol == 'AUXILIAR' and modulo_solicitado in ['RENTA_ACTIVA', 'GUARDADOS']:
                return view_func(*args, **kwargs)
            else:
                flash("Acceso denegado a este módulo para tu rol.", "danger")
                return redirect(url_for('vista_renta_activa'))
        return wrapper
    return decorator

@app.route('/', methods=['GET', 'POST'])
def vista_login():
    if request.method == 'POST':
        user = request.form.get('usuario')
        pwd = request.form.get('contrasena')
        ip = request.remote_addr

        datos_usuario = auth_srv.login(user, pwd, ip)
        if datos_usuario:
            session['usuario_id'] = datos_usuario['id']
            session['usuario'] = datos_usuario['usuario']
            session['rol'] = datos_usuario['rol']
            
            if datos_usuario['rol'] == 'ADMINISTRADOR':
                return redirect(url_for('vista_punto_renta'))
            return redirect(url_for('vista_renta_activa'))
        else:
            flash("Credenciales incorrectas.", "danger")

    return render_template('login.html')

@app.route('/restablecer', methods=['POST'])
def restablecer():
    user = request.form.get('usuario')
    try:
        auth_srv.restablecer_contrasena(user)
        flash("Se ha enviado una nueva contraseña a tu correo registrado.", "info")
    except Exception as e:
        flash(str(e), "danger")
    return redirect(url_for('vista_login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('vista_login'))

@app.route('/punto-renta', methods=['GET', 'POST'])
@login_required('PUNTO_RENTA')
def vista_punto_renta():
    if request.method == 'POST':
        datos = request.get_json()
        articulos = datos.get('articulos', [])
        monto_pagado = float(datos.get('monto_pagado', 0.0))

        sesion_dict = {'id': session['usuario_id'], 'rol': session['rol']}
        try:
            res = renta_srv.procesar_renta(sesion_dict, articulos, monto_pagado)
            return jsonify({'success': True, 'data': res})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400

    return render_template('punto_renta.html')

@app.route('/renta-activa')
@login_required('RENTA_ACTIVA')
def vista_renta_activa():
    sesion_dict = {'id': session['usuario_id'], 'rol': session['rol']}
    articulos_rentados = activa_srv.listar_rentas_activas(sesion_dict)
    return render_template('renta_activa.html', rentas=articulos_rentados)

@app.route('/renta-activa/pausar/<int:detalle_id>', methods=['POST'])
@login_required('RENTA_ACTIVA')
def pausar(detalle_id):
    sesion_dict = {'id': session['usuario_id'], 'rol': session['rol']}
    activa_srv.pausar(sesion_dict, detalle_id)
    return redirect(url_for('vista_renta_activa'))

@app.route('/renta-activa/reanudar/<int:detalle_id>', methods=['POST'])
@login_required('RENTA_ACTIVA')
def reanudar(detalle_id):
    sesion_dict = {'id': session['usuario_id'], 'rol': session['rol']}
    activa_srv.reanudar(sesion_dict, detalle_id)
    return redirect(url_for('vista_renta_activa'))

@app.route('/renta-activa/entregar/<int:detalle_id>', methods=['POST'])
@login_required('RENTA_ACTIVA')
def entregar(detalle_id):
    sesion_dict = {'id': session['usuario_id'], 'rol': session['rol']}
    resultado = activa_srv.entregar(sesion_dict, detalle_id)
    if resultado and resultado.get('cobro_extra', 0) > 0:
        flash(f"Tiempo excedido: {resultado['minutos_retraso']} min. Cobro extra: ${resultado['cobro_extra']}", "warning")
    if resultado and resultado.get('estado_articulo') == 'GUARDADO':
        flash("El artículo no cuenta con batería suficiente. Debe ser guardado.", "info")
    return redirect(url_for('vista_renta_activa'))

@app.route('/guardados')
@login_required('GUARDADOS')
def vista_guardados():
    sesion_dict = {'id': session['usuario_id'], 'rol': session['rol']}
    articulos_guardados = activa_srv.listar_guardados(sesion_dict)
    return render_template('guardados.html', guardados=articulos_guardados)

@app.route('/configuraciones', methods=['GET', 'POST'])
@login_required('CONFIGURACION')
def vista_configuraciones():
    sesion_dict = {'id': session['usuario_id'], 'rol': session['rol']}
    
    if request.method == 'POST':
        accion = request.form.get('accion')
        try:
            if accion == 'crear_categoria':
                config_srv.crear_categoria(sesion_dict, request.form['nombre'], float(request.form['costo_minuto']))
                flash("Categoría creada con éxito.", "success")
                
            elif accion == 'registrar_articulo':
                aplica_bat = 'aplica_bateria' in request.form
                bat_min = int(request.form['bateria_minutos']) if aplica_bat and request.form['bateria_minutos'] else None
                config_srv.registrar_articulo(sesion_dict, request.form['numero_articulo'], int(request.form['categoria_id']), aplica_bat, bat_min)
                flash("Artículo registrado exitosamente.", "success")

            elif accion == 'editar_articulo':
                art_id = int(request.form['articulo_id'])
                cat_id = int(request.form['categoria_id'])
                aplica_bat = 'aplica_bateria' in request.form
                bat_min = int(request.form['bateria_minutos']) if aplica_bat and request.form['bateria_minutos'] else None
                estado = request.form['estado']
                config_srv.editar_articulo(sesion_dict, art_id, cat_id, aplica_bat, bat_min, estado)
                flash("Artículo actualizado correctamente.", "success")

            elif accion == 'cambiar_estado':
                art_id = int(request.form['articulo_id'])
                nuevo_estado = request.form['nuevo_estado']
                config_srv.cambiar_estado_articulo(sesion_dict, art_id, nuevo_estado)
                flash(f"Estado del artículo cambiado a {nuevo_estado}.", "info")

        except Exception as e:
            flash(str(e), "danger")
            
        return redirect(url_for('vista_configuraciones'))
            
    lista_articulos = config_srv.listar_articulos_completos(sesion_dict)
    lista_categorias = config_srv.listar_categorias(sesion_dict)
    
    return render_template('configuraciones.html', articulos=lista_articulos, categorias=lista_categorias)

if __name__ == '__main__':
    app.run(debug=True, port=5000)