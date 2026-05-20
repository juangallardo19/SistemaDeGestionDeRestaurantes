from django.conf import settings
from django.db import models


class MovimientoInventario(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
    ]

    ingrediente = models.ForeignKey(
        'menu.Ingrediente',
        on_delete=models.PROTECT,
        related_name='movimientos',
        verbose_name='Ingrediente',
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name='Tipo')
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Cantidad')
    fecha = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='movimientos_inventario',
        verbose_name='Responsable',
    )
    motivo = models.CharField(max_length=255, blank=True, verbose_name='Motivo')
    stock_resultante = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Stock resultante')

    class Meta:
        verbose_name = 'Movimiento de inventario'
        verbose_name_plural = 'Movimientos de inventario'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.get_tipo_display()} — {self.ingrediente.nombre} ({self.cantidad}) — {self.fecha.strftime("%d/%m/%Y")}'
