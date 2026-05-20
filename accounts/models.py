from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('cliente', 'Cliente'),
        ('mesero', 'Mesero'),
        ('admin', 'Administrador'),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='cliente',
        verbose_name='Rol',
    )
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Teléfono')
    profile_picture = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True,
        verbose_name='Foto de perfil',
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    @property
    def is_admin(self):
        return self.role == 'admin' or self.is_staff

    @property
    def is_mesero(self):
        return self.role == 'mesero'

    @property
    def is_cliente(self):
        return self.role == 'cliente'
