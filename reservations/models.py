from django.conf import settings
from django.db import models


class Mesa(models.Model):
    UBICACION_CHOICES = [
        ('interior', 'Interior'),
        ('exterior', 'Exterior'),
        ('terraza', 'Terraza'),
    ]

    numero = models.IntegerField(unique=True, verbose_name='Número de mesa')
    capacidad = models.PositiveIntegerField(verbose_name='Capacidad')
    ubicacion = models.CharField(
        max_length=20,
        choices=UBICACION_CHOICES,
        default='interior',
        verbose_name='Ubicación',
    )
    activa = models.BooleanField(default=True, verbose_name='Activa')

    class Meta:
        verbose_name = 'Mesa'
        verbose_name_plural = 'Mesas'
        ordering = ['numero']

    def __str__(self):
        return f'Mesa {self.numero} — {self.get_ubicacion_display()} (cap. {self.capacidad})'


class Reserva(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
    ]

    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='reservas',
        verbose_name='Cliente',
    )
    mesa = models.ForeignKey(Mesa, on_delete=models.PROTECT, related_name='reservas', verbose_name='Mesa')
    fecha = models.DateField(verbose_name='Fecha')
    hora_inicio = models.TimeField(verbose_name='Hora de inicio')
    hora_fin = models.TimeField(verbose_name='Hora de fin')
    numero_personas = models.PositiveIntegerField(verbose_name='Número de personas')
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name='Estado',
    )
    notas = models.TextField(blank=True, verbose_name='Notas')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')

    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering = ['fecha', 'hora_inicio']

    def __str__(self):
        return f'Reserva — {self.cliente.username} | Mesa {self.mesa.numero} | {self.fecha} {self.hora_inicio}'
