from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    imagen = models.ImageField(upload_to='categorias/', blank=True, null=True, verbose_name='Imagen')
    activo = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Ingrediente(models.Model):
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    unidad_medida = models.CharField(max_length=30, verbose_name='Unidad de medida')
    stock_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Stock actual')
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Stock mínimo')
    activo = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        verbose_name = 'Ingrediente'
        verbose_name_plural = 'Ingredientes'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.unidad_medida})'

    @property
    def stock_bajo(self):
        return self.stock_actual <= self.stock_minimo


class Plato(models.Model):
    nombre = models.CharField(max_length=150, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio')
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='platos',
        verbose_name='Categoría',
    )
    imagen = models.ImageField(upload_to='platos/', blank=True, null=True, verbose_name='Imagen')
    disponible = models.BooleanField(default=True, verbose_name='Disponible')
    tiempo_preparacion = models.IntegerField(default=15, verbose_name='Tiempo de preparación (min)')
    ingredientes = models.ManyToManyField(
        Ingrediente,
        through='PlatoIngrediente',
        related_name='platos',
        verbose_name='Ingredientes',
    )

    class Meta:
        verbose_name = 'Plato'
        verbose_name_plural = 'Platos'
        ordering = ['categoria', 'nombre']

    def __str__(self):
        return f'{self.nombre} — ${self.precio}'


class PlatoIngrediente(models.Model):
    plato = models.ForeignKey(
        Plato,
        on_delete=models.CASCADE,
        related_name='plato_ingredientes',
        verbose_name='Plato',
    )
    ingrediente = models.ForeignKey(
        Ingrediente,
        on_delete=models.PROTECT,
        related_name='plato_ingredientes',
        verbose_name='Ingrediente',
    )
    cantidad_necesaria = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Cantidad necesaria')

    class Meta:
        verbose_name = 'Ingrediente del plato'
        verbose_name_plural = 'Ingredientes del plato'
        unique_together = ('plato', 'ingrediente')

    def __str__(self):
        return f'{self.plato.nombre} — {self.ingrediente.nombre}: {self.cantidad_necesaria}'
