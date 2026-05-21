from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    # Carrito
    path('carrito/', views.ver_carrito, name='cart'),
    path('carrito/agregar/<int:plato_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/remover/<int:plato_id>/', views.remover_del_carrito, name='remover_del_carrito'),
    path('carrito/actualizar/<int:plato_id>/', views.actualizar_carrito, name='actualizar_carrito'),
    path('carrito/json/', views.carrito_json, name='carrito_json'),
    path('carrito/confirmar/', views.crear_pedido, name='crear_pedido'),
    # Pedidos — 'list' es el nombre requerido por base.html y accounts/views.py (redirect mesero)
    path('activos/', views.lista_pedidos_activos, name='list'),
    path('mis-pedidos/', views.mis_pedidos, name='mis_pedidos'),
    path('historial/', views.historial_pedidos, name='historial_pedidos'),
    path('<int:pk>/', views.detalle_pedido, name='detalle_pedido'),
    path('<int:pk>/estado/', views.cambiar_estado_pedido, name='cambiar_estado_pedido'),
    path('reporte/ventas/', views.reporte_ventas_diarias, name='reporte_ventas'),
]
