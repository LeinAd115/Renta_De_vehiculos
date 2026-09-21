from database import DatabaseConnection
from auth_guard import AuthGuard

class RentaActivaService:
    def __init__(self, db: DatabaseConnection):
        self.db = db

    def listar_rentas_activas(self, usuario_sesion: dict) -> list:
        AuthGuard.verificar_acceso(usuario_sesion, 'RENTA_ACTIVA')
        with self.db.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("""
                    SELECT 
                        rd.id AS detalle_id,
                        a.numero_articulo,
                        rd.estado AS estado_renta,
                        rd.hora_inicio,
                        rd.hora_entrega_programada,
                        TIMESTAMPDIFF(MINUTE, NOW(), rd.hora_entrega_programada) AS minutos_restantes,
                        a.aplica_bateria,
                        a.minutos_bateria_restante,
                        CASE 
                            WHEN a.aplica_bateria = FALSE THEN 'No Aplica'
                            WHEN a.minutos_bateria_restante >= 40 THEN 'Disponible 40+ min'
                            WHEN a.minutos_bateria_restante >= 30 THEN 'Disponible 30 min'
                            WHEN a.minutos_bateria_restante >= 20 THEN 'Disponible 20 min'
                            ELSE 'Guardar (Sin batería suficiente)'
                        END AS estado_bateria_diagnostico
                    FROM renta_detalles rd
                    JOIN articulos a ON rd.articulo_id = a.id
                    WHERE rd.estado IN ('ACTIVA', 'PAUSADA')
                """)
                return cursor.fetchall()
            finally:
                cursor.close()

    def pausar(self, usuario_sesion: dict, detalle_id: int):
        AuthGuard.verificar_acceso(usuario_sesion, 'RENTA_ACTIVA')
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.callproc('sp_pausar_renta_articulo', (detalle_id,))
                conn.commit()
            finally:
                cursor.close()

    def reanudar(self, usuario_sesion: dict, detalle_id: int):
        AuthGuard.verificar_acceso(usuario_sesion, 'RENTA_ACTIVA')
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.callproc('sp_reanudar_renta_articulo', (detalle_id,))
                conn.commit()
            finally:
                cursor.close()

    def entregar(self, usuario_sesion: dict, detalle_id: int) -> dict:
        AuthGuard.verificar_acceso(usuario_sesion, 'RENTA_ACTIVA')
        with self.db.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.callproc('sp_entregar_articulo', (detalle_id,))
                resultado = None
                for r in cursor.stored_results():
                    resultado = r.fetchone()
                conn.commit()
                return resultado
            finally:
                cursor.close()

    def extender_tiempo(self, usuario_sesion: dict, detalle_id: int, minutos_extra: int, monto_pagado: float) -> dict:
        AuthGuard.verificar_acceso(usuario_sesion, 'PUNTO_RENTA')
        with self.db.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.callproc('sp_extender_tiempo_articulo', (detalle_id, minutos_extra, monto_pagado))
                resultado = None
                for r in cursor.stored_results():
                    resultado = r.fetchone()
                conn.commit()
                return resultado
            finally:
                cursor.close()

    def listar_guardados(self, usuario_sesion: dict) -> list:
        AuthGuard.verificar_acceso(usuario_sesion, 'GUARDADOS')
        with self.db.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("""
                    SELECT numero_articulo, minutos_bateria_restante, estado 
                    FROM articulos 
                    WHERE estado = 'GUARDADO'
                """)
                return cursor.fetchall()
            finally:
                cursor.close()