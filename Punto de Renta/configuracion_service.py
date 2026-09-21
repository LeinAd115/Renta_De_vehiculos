import bcrypt
from database import DatabaseConnection
from auth_guard import AuthGuard

class ConfiguracionService:
    def __init__(self, db: DatabaseConnection):
        self.db = db

    def listar_categorias(self, usuario_sesion: dict) -> list:
        AuthGuard.verificar_acceso(usuario_sesion, 'CONFIGURACION')
        with self.db.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("SELECT id, nombre, costo_por_minuto FROM categorias ORDER BY nombre ASC")
                return cursor.fetchall()
            finally:
                cursor.close()

    def listar_articulos_completos(self, usuario_sesion: dict) -> list:
        AuthGuard.verificar_acceso(usuario_sesion, 'CONFIGURACION')
        with self.db.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("""
                    SELECT 
                        a.id,
                        a.numero_articulo,
                        a.categoria_id,
                        c.nombre AS categoria_nombre,
                        c.costo_por_minuto,
                        a.aplica_bateria,
                        a.minutos_bateria_restante,
                        a.estado
                    FROM articulos a
                    JOIN categorias c ON a.categoria_id = c.id
                    ORDER BY a.id DESC
                """)
                return cursor.fetchall()
            finally:
                cursor.close()

    def crear_categoria(self, usuario_sesion: dict, nombre: str, costo_por_minuto: float):
        AuthGuard.verificar_acceso(usuario_sesion, 'CONFIGURACION')
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO categorias (nombre, costo_por_minuto) VALUES (%s, %s)", (nombre, costo_por_minuto))
                conn.commit()
            finally:
                cursor.close()

    def registrar_articulo(self, usuario_sesion: dict, numero_articulo: str, categoria_id: int, aplica_bateria: bool, bateria_minutos: int = None):
        AuthGuard.verificar_acceso(usuario_sesion, 'CONFIGURACION')
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO articulos (numero_articulo, categoria_id, aplica_bateria, minutos_bateria_restante)
                    VALUES (%s, %s, %s, %s)
                """, (numero_articulo, categoria_id, aplica_bateria, bateria_minutos))
                conn.commit()
            finally:
                cursor.close()

    def editar_articulo(self, usuario_sesion: dict, articulo_id: int, categoria_id: int, aplica_bateria: bool, bateria_minutos: int, estado: str):
        AuthGuard.verificar_acceso(usuario_sesion, 'CONFIGURACION')
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE articulos 
                    SET categoria_id = %s,
                        aplica_bateria = %s,
                        minutos_bateria_restante = %s,
                        estado = %s
                    WHERE id = %s
                """, (categoria_id, aplica_bateria, bateria_minutos, estado, articulo_id))
                conn.commit()
            finally:
                cursor.close()

    def cambiar_estado_articulo(self, usuario_sesion: dict, articulo_id: int, nuevo_estado: str):
        AuthGuard.verificar_acceso(usuario_sesion, 'CONFIGURACION')
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE articulos SET estado = %s WHERE id = %s", (nuevo_estado, articulo_id))
                conn.commit()
            finally:
                cursor.close()