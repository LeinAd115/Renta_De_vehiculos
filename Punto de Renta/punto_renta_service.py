from database import DatabaseConnection
from auth_guard import AuthGuard

class PuntoRentaService:
    def __init__(self, db: DatabaseConnection):
        self.db = db

    def procesar_renta(self, usuario_sesion: dict, articulos_a_rentar: list, monto_pagado: float) -> dict:
        AuthGuard.verificar_acceso(usuario_sesion, 'PUNTO_RENTA')

        with self.db.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                total_acumulado = 0.0
                articulos_validados = []

                # Validación de artículos, inventario y batería
                for item in articulos_a_rentar:
                    cursor.execute("""
                        SELECT a.id, a.numero_articulo, a.estado, a.aplica_bateria, 
                               a.minutos_bateria_restante, c.costo_por_minuto
                        FROM articulos a
                        JOIN categorias c ON a.categoria_id = c.id
                        WHERE a.numero_articulo = %s FOR UPDATE
                    """, (item['numero_articulo'],))
                    art = cursor.fetchone()

                    if not art:
                        raise ValueError(f"El artículo '{item['numero_articulo']}' no existe.")
                    if art['estado'] != 'DISPONIBLE':
                        raise ValueError(f"El artículo '{item['numero_articulo']}' no está disponible ({art['estado']}).")
                    if art['aplica_bateria'] and art['minutos_bateria_restante'] < item['minutos']:
                        raise ValueError(f"Artículo '{item['numero_articulo']}' sin batería suficiente.")

                    costo_parcial = float(art['costo_por_minuto']) * int(item['minutos'])
                    total_acumulado += costo_parcial
                    articulos_validados.append({
                        'id': art['id'],
                        'minutos': item['minutos'],
                        'aplica_bateria': art['aplica_bateria']
                    })

                if monto_pagado < total_acumulado:
                    raise ValueError(f"Monto insuficiente. Total: ${total_acumulado:.2f}, Pagado: ${monto_pagado:.2f}")

                cambio = round(monto_pagado - total_acumulado, 2)

                # Registrar transacción principal
                cursor.execute("""
                    INSERT INTO rentas (usuario_id, monto_total, monto_pagado, cambio_devuelto)
                    VALUES (%s, %s, %s, %s)
                """, (usuario_sesion['id'], total_acumulado, monto_pagado, cambio))
                renta_id = cursor.lastrowid

                # Registrar detalles con la fórmula de 3 minutos de gracia
                for art in articulos_validados:
                    cursor.execute("""
                        INSERT INTO renta_detalles (
                            renta_id, articulo_id, tiempo_rentado_minutos, hora_entrega_programada
                        ) VALUES (
                            %s, %s, %s, DATE_ADD(DATE_ADD(NOW(), INTERVAL %s MINUTE), INTERVAL 3 MINUTE)
                        )
                    """, (renta_id, art['id'], art['minutos'], art['minutos']))

                    if art['aplica_bateria']:
                        cursor.execute("""
                            UPDATE articulos 
                            SET estado = 'RENTADO',
                                minutos_bateria_restante = minutos_bateria_restante - %s
                            WHERE id = %s
                        """, (art['minutos'], art['id']))
                    else:
                        cursor.execute("UPDATE articulos SET estado = 'RENTADO' WHERE id = %s", (art['id'],))

                conn.commit()
                return {
                    'renta_id': renta_id,
                    'total': total_acumulado,
                    'cambio': cambio,
                    'articulos_procesados': len(articulos_validados)
                }
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()