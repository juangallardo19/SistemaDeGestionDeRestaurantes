from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect


class RolRequeridoMixin(LoginRequiredMixin):
    """
    Mixin para CBV que verifica que el usuario autenticado tenga
    uno de los roles indicados en allowed_roles.
    Los usuarios is_staff siempre tienen acceso.
    """
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not request.user.is_staff and self.allowed_roles:
            if request.user.role not in self.allowed_roles:
                messages.error(request, 'No tienes permiso para acceder a esta sección.')
                return redirect('accounts:login')

        return super().dispatch(request, *args, **kwargs)


class AdminRequeridoMixin(RolRequeridoMixin):
    allowed_roles = ['admin']


class MeseroOAdminMixin(RolRequeridoMixin):
    allowed_roles = ['admin', 'mesero']
