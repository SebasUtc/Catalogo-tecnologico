from django.contrib import admin
from django.utils.html import format_html
from .models import CuentaBancaria, Reserva


@admin.register(CuentaBancaria)
class CuentaBancariaAdmin(admin.ModelAdmin):
    list_display = ("banco", "tipo_cuenta", "numero_cuenta", "titular", "documento_titular", "activo", "orden")
    list_filter = ("activo", "banco")
    list_editable = ("activo", "orden")
    search_fields = ("banco", "numero_cuenta", "titular", "documento_titular")


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "estado",
        "nombre_cliente",
        "telefono_cliente",
        "producto",
        "cantidad",
        "precio_total_formateado",
        "anticipo_formateado",
        "saldo_formateado",
        "fecha_creacion",
        "fecha_limite_pago",
    )
    list_filter = ("estado", "fecha_creacion", "producto__categoria", "producto__marca")
    search_fields = ("codigo", "nombre_cliente", "email_cliente", "telefono_cliente", "documento_identidad", "producto__nombre", "producto__sku")
    readonly_fields = ("codigo", "fecha_creacion", "fecha_actualizacion")
    list_editable = ("estado",)

    fieldsets = (
        ("Identificación de Reserva", {
            "fields": ("codigo", "estado", "fecha_creacion", "fecha_limite_pago")
        }),
        ("Datos del Cliente", {
            "fields": ("nombre_cliente", "documento_identidad", "email_cliente", "telefono_cliente", "notas")
        }),
        ("Detalle del Producto y Cupo", {
            "fields": ("producto", "cantidad", "precio_unitario")
        }),
        ("Desglose Financiero de Reserva", {
            "fields": ("precio_total", "monto_anticipo", "saldo_en_tienda")
        }),
    )

    def badge_estado(self, obj):
        colores = {
            Reserva.ESTADO_PENDIENTE_PAGO: "#f59e0b",       # Ámbar
            Reserva.ESTADO_COMPROBANTE_SUBIDO: "#3b82f6",   # Azul
            Reserva.ESTADO_CONFIRMADA: "#10b981",           # Verde
            Reserva.ESTADO_ENTREGADA: "#6366f1",            # Indigo
            Reserva.ESTADO_CANCELADA: "#ef4444",            # Rojo
        }
        color = colores.get(obj.estado, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 0.8rem;">{}</span>',
            color,
            obj.get_estado_display()
        )
    badge_estado.short_description = "Estado"

    def precio_total_formateado(self, obj):
        return f"${obj.precio_total:,.2f}"
    precio_total_formateado.short_description = "Total"

    def anticipo_formateado(self, obj):
        return f"${obj.monto_anticipo:,.2f}"
    anticipo_formateado.short_description = "Anticipo Req."

    def saldo_formateado(self, obj):
        return f"${obj.saldo_en_tienda:,.2f}"
    saldo_formateado.short_description = "Saldo Tienda"
