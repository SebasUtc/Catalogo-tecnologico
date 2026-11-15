from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    path('', views.catalogo_view, name='catalogo'),
    path('producto/<slug:slug>/', views.detalle_producto_view, name='detalle'),
]
