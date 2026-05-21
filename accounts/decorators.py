from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def rol_requerido(roles):
    """
    Decorador para FBV. roles puede ser string o lista de strings.
    Los usuarios is_staff siempre tienen acceso.
    """
    if isinstance(roles, str):
        roles = [roles]

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Debes iniciar sesión para acceder a esta página.')
                return redirect('accounts:login')

            if request.user.is_staff or request.user.role in roles:
                return view_func(request, *args, **kwargs)

            messages.error(request, 'No tienes permiso para acceder a esta sección.')
            return redirect('accounts:login')

        return wrapper
    return decorator


def solo_admin(view_func):
    return rol_requerido(['admin'])(view_func)


def solo_mesero_o_admin(view_func):
    return rol_requerido(['admin', 'mesero'])(view_func)


# Alias usados en las vistas de las apps
admin_required   = solo_admin
mesero_required  = solo_mesero_o_admin
