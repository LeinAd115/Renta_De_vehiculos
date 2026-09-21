import bcrypt
import secrets
import string
from database import DatabaseConnection

class AuthService:
    def __init__(self, db: DatabaseConnection):
        self.db = db

    def login(self, nombre_usuario: str, contrasena: str, ip: str = None) -> dict:
        with self.db.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.callproc('sp_autenticar_usuario', (nombre_usuario, ip))
                user_record = None
                for result in cursor.stored_results():
                    user_record = result.fetchone()

                es_valido = False
                user_data = None

                if user_record and bcrypt.checkpw(contrasena.encode('utf-8'), user_record['contrasena_hash'].encode('utf-8')):
                    es_valido = True
                    user_data = {
                        'id': user_record['id'],
                        'usuario': user_record['nombre_usuario'],
                        'rol': user_record['rol'],
                        'correo': user_record['correo']
                    }

                cursor.callproc('sp_registrar_auditoria_login', (nombre_usuario, es_valido, ip))
                conn.commit()

                return user_data
            finally:
                cursor.close()

    def restablecer_contrasena(self, nombre_usuario: str) -> dict:
        nueva_clave = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
        nueva_hash = bcrypt.hashpw(nueva_clave.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        with self.db.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.callproc('sp_restablecer_contrasena', (nombre_usuario, nueva_hash))
                correo_destino = None
                for result in cursor.stored_results():
                    row = result.fetchone()
                    if row:
                        correo_destino = row['correo']

                conn.commit()

                if not correo_destino:
                    raise ValueError("Usuario inexistente o inactivo.")

                self._simular_envio_correo(correo_destino, nueva_clave)
                return {"correo": correo_destino, "nueva_clave": nueva_clave}
            finally:
                cursor.close()

    def _simular_envio_correo(self, correo: str, clave: str):
        print(f"[Notificación SMTP] Se ha enviado la nueva contraseña a '{correo}': {clave}")