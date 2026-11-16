from django.urls import path
from . import views

app_name = 'reservas'

urlpatterns = [
    path('solicitar/<slug:slug>/', views.solicitar_reserva_view, name='solicitar'),
    path('resumen/<str:codigo>/', views.resumen_reserva_view, name='resumen'),
    path('subir-comprobante/<str:codigo>/', views.subir_comprobante_view, name='subir_comprobante'),
    path('consultar/', views.consultar_reserva_view, name='consultar'),
]
