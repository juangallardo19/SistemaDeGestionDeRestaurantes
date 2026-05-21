from django.urls import path

from . import views

app_name = 'inventory'

urlpatterns = [
    # 'list' requerido por base.html (link Inventario en dropdown Administración)
    path('', views.lista_inventario, name='list'),
    path('movimiento/', views.registrar_movimiento, name='registrar_movimiento'),
    path('historial/', views.historial_movimientos, name='historial'),
    path('ingrediente/<int:pk>/', views.detalle_ingrediente, name='detalle_ingrediente'),
    path('stock-categoria/', views.stock_por_categoria, name='stock_categoria'),
]
