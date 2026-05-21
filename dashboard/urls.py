from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_principal, name='principal'),
    # ── API JSON para gráficos ────────────────────────────────────────────────
    path('api/platos-vendidos/', views.json_platos_mas_vendidos, name='api_platos'),
    path('api/ingresos-mes/', views.json_ingresos_por_mes, name='api_ingresos'),
    path('api/pedidos-estado/', views.json_pedidos_por_estado, name='api_estados'),
    path('api/reservas-mes/', views.json_reservas_por_mes, name='api_reservas'),
    path('api/ocupacion-mesas/', views.json_ocupacion_mesas, name='api_ocupacion'),
    # ── Exportaciones ─────────────────────────────────────────────────────────
    path('exportar/pedidos/pdf/', views.exportar_pedidos_pdf, name='export_pedidos_pdf'),
    path('exportar/pedidos/excel/', views.exportar_pedidos_excel, name='export_pedidos_excel'),
    path('exportar/inventario/pdf/', views.exportar_inventario_pdf, name='export_inventario_pdf'),
    path('exportar/inventario/excel/', views.exportar_inventario_excel, name='export_inventario_excel'),
]
