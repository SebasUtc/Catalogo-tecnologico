from django.urls import path
from . import views

app_name = 'reservas'

urlpatterns = [
    # Flujo del Cliente
    path('solicitar/<slug:slug>/', views.solicitar_reserva_view, name='solicitar'),
    path('resumen/<str:codigo>/', views.resumen_reserva_view, name='resumen'),
    path('subir-comprobante/<str:codigo>/', views.subir_comprobante_view, name='subir_comprobante'),
    path('consultar/', views.consultar_reserva_view, name='consultar'),

    # Flujo del Gestor Financiero (HU 4)
    path('panel-financiero/', views.panel_financiero_view, name='panel_financiero'),
    path('panel-financiero/aprobar/<str:codigo>/', views.aprobar_reserva_view, name='aprobar'),
    path('panel-financiero/rechazar/<str:codigo>/', views.rechazar_reserva_view, name='rechazar'),
]
