from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.shortcuts import redirect, render

from .forms import CustomUserChangeForm, CustomUserCreationForm, LoginForm


def register_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'cliente'
            user.save()

            group, _ = Group.objects.get_or_create(name=user.get_role_display())
            user.groups.add(group)

            messages.success(
                request,
                f'¡Cuenta creada exitosamente! Bienvenido, {user.first_name or user.username}.'
            )
            return redirect('accounts:login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(
                request,
                f'Bienvenido, {user.get_full_name() or user.username}.'
            )
            return _redirect_by_role(user)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos. Intenta de nuevo.')
    else:
        form = LoginForm(request)

    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('accounts:profile')
    else:
        form = CustomUserChangeForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})


def _redirect_by_role(user):
    if user.is_admin:
        return redirect('dashboard:index')
    if user.is_mesero:
        return redirect('orders:list')
    return redirect('menu:list')
