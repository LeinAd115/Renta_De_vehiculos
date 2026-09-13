

import mysql.connector
import bcrypt

# ── Configuración de conexión ─────────────────────────────────────────────────
DB_CONFIG = {
    'host':     'localhost',
    'user':     'root',
    'password': 'Alex12.a',
    'database': 'amistoso',
}

def hashear(contrasena: str) -> str:
    return bcrypt.hashpw(contrasena.encode(), bcrypt.gensalt()).decode()

def migrar():
    db     = mysql.connector.connect(**DB_CONFIG)
    cursor = db.cursor(dictionary=True)

    # Leer todos los empleados
    cursor.execute('SELECT n_empleado  , usuario, contrasena FROM Empleados')
    empleados = cursor.fetchall()

    migrados  = 0
    omitidos  = 0
    errores   = 0

    print(f"\n{'─'*50}")
    print(f"  Empleados encontrados: {len(empleados)}")
    print(f"{'─'*50}")

    for emp in empleados:
        contrasena_actual = emp['contrasena']

        # Si ya es un hash bcrypt (empieza con $2b$ o $2a$), se omite
        if contrasena_actual.startswith('$2b$') or contrasena_actual.startswith('$2a$'):
            print(f"  [OMITIDO]  {emp['usuario']} — ya tiene hash bcrypt")
            omitidos += 1
            continue

        try:
            nuevo_hash = hashear(contrasena_actual)
            cursor.execute(
                'UPDATE Empleados SET contrasena = %s WHERE n_empleado   = %s',
                (nuevo_hash, emp['n_empleado'])
            )
            db.commit()
            print(f"  [OK]       {emp['usuario']} — migrado correctamente")
            migrados += 1

        except Exception as e:
            print(f"  [ERROR]    {emp['usuario']} — {e}")
            errores += 1

    cursor.close()
    db.close()

    print(f"\n{'─'*50}")
    print(f"  Migrados : {migrados}")
    print(f"  Omitidos : {omitidos}  ")
    print(f"  Errores  : {errores}")
    print(f"{'─'*50}")
    print("\n  Migración completada. Puedes borrar este archivo.\n")

if __name__ == '__main__':
    confirmacion = input("¿Confirmar la migración de contraseñas a bcrypt? (s/n): ").strip().lower()
    if confirmacion == 's':
        migrar()
    else:
        print("Migración cancelada.")
