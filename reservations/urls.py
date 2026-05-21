from django.urls import path

from . import views

app_name = 'reservations'

urlpatterns = [
    # Cliente — 'list' requerido por base.html (link Reservas para clientes)
    path('', views.mis_reservas, name='list'),
    path('hacer/', views.hacer_reserva, name='hacer_reserva'),
    path('<int:pk>/cancelar/', views.cancelar_reserva, name='cancelar_reserva'),
    # Mesero / Admin
    path('todas/', views.lista_reservas, name='lista_reservas'),
    path('mesas-estado/', views.mesas_overview, name='mesas_overview'),
    path('mesas-estado/<int:pk>/', views.mesa_detalle, name='mesa_detalle'),
    path('<int:pk>/confirmar/', views.confirmar_reserva, name='confirmar_reserva'),
    path('<int:pk>/completar/', views.completar_reserva, name='completar_reserva'),
    # CRUD Mesas (admin)
    path('mesas/', views.crud_mesas, name='crud_mesas'),
    path('mesas/<int:pk>/editar/', views.editar_mesa, name='editar_mesa'),
    path('mesas/<int:pk>/toggle/', views.toggle_mesa, name='toggle_mesa'),
    # API JSON
    path('disponibilidad/', views.disponibilidad_mesas, name='disponibilidad_mesas'),
]
