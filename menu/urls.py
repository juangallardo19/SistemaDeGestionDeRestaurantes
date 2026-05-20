from django.urls import path

from . import views

app_name = 'menu'

urlpatterns = [
    # Platos
    path('', views.lista_platos, name='list'),
    path('buscar/', views.buscar_platos, name='buscar_platos'),
    path('plato/nuevo/', views.crear_plato, name='crear_plato'),
    path('plato/<int:pk>/', views.detalle_plato, name='detalle_plato'),
    path('plato/<int:pk>/editar/', views.editar_plato, name='editar_plato'),
    path('plato/<int:pk>/eliminar/', views.eliminar_plato, name='eliminar_plato'),
    # Categorías
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/nueva/', views.crear_categoria, name='crear_categoria'),
    path('categorias/<int:pk>/editar/', views.editar_categoria, name='editar_categoria'),
    path('categorias/<int:pk>/eliminar/', views.eliminar_categoria, name='eliminar_categoria'),
    # Ingredientes
    path('ingredientes/', views.lista_ingredientes, name='lista_ingredientes'),
    path('ingredientes/nuevo/', views.crear_ingrediente, name='crear_ingrediente'),
    path('ingredientes/<int:pk>/editar/', views.editar_ingrediente, name='editar_ingrediente'),
    path('ingredientes/<int:pk>/eliminar/', views.eliminar_ingrediente, name='eliminar_ingrediente'),
]
