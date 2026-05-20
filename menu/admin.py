from django.contrib import admin

from .models import Categoria, Ingrediente, Plato, PlatoIngrediente


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)


@admin.register(Ingrediente)
class IngredienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'unidad_medida', 'stock_actual', 'stock_minimo', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)


class PlatoIngredienteInline(admin.TabularInline):
    model = PlatoIngrediente
    extra = 1


@admin.register(Plato)
class PlatoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'disponible', 'tiempo_preparacion')
    list_filter = ('categoria', 'disponible')
    search_fields = ('nombre', 'descripcion')
    inlines = [PlatoIngredienteInline]


@admin.register(PlatoIngrediente)
class PlatoIngredienteAdmin(admin.ModelAdmin):
    list_display = ('plato', 'ingrediente', 'cantidad_necesaria')
    search_fields = ('plato__nombre', 'ingrediente__nombre')
