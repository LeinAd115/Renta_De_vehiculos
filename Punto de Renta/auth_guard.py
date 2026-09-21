class AuthGuard:
    @staticmethod
    def verificar_acceso(usuario_sesion: dict, modulo: str) -> bool:
        if not usuario_sesion or 'rol' not in usuario_sesion:
            raise PermissionError("Sesión no válida o no iniciada.")

        rol = usuario_sesion['rol']

        if rol == 'ADMINISTRADOR':
            return True

        if rol == 'AUXILIAR' and modulo in ['RENTA_ACTIVA', 'GUARDADOS']:
            return True

        raise PermissionError(f"Acceso denegado: El rol '{rol}' no tiene permisos para el módulo '{modulo}'.")