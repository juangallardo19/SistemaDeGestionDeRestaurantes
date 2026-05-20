from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def role_required(role):
    """
    Verifica que el usuario tenga el rol indicado.
    role puede ser un string o una lista de strings.
    Los usuarios is_staff siempre tienen acceso.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Debes iniciar sesión para acceder a esta página.')
                return redirect('accounts:login')

            if isinstance(role, (list, tuple)):
                allowed = request.user.role in role or request.user.is_staff
            else:
                allowed = request.user.role == role or request.user.is_staff

            if not allowed:
                messages.error(request, 'No tienes permiso para acceder a esta sección.')
                return redirect('accounts:login')

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_func):
    return role_required('admin')(view_func)


def mesero_required(view_func):
    return role_required(['admin', 'mesero'])(view_func)
