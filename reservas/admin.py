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
        "comprobante_link",
        "nombre_cliente",
        "telefono_cliente",
        "producto",
        "cantidad",
        "precio_total_formateado",
        "anticipo_formateado",
        "saldo_formateado",
        "fecha_creacion",
        "fecha_subida_comprobante",
    )
    list_filter = ("estado", "fecha_creacion", "fecha_subida_comprobante", "producto__categoria", "producto__marca")
    search_fields = (
        "codigo",
        "nombre_cliente",
        "email_cliente",
        "telefono_cliente",
        "documento_identidad",
        "numero_transaccion",
        "producto__nombre",
        "producto__sku"
    )
    readonly_fields = ("codigo", "fecha_creacion", "fecha_actualizacion", "vista_comprobante")
    list_editable = ("estado",)

    fieldsets = (
        ("Identificación de Reserva", {
            "fields": ("codigo", "estado", "fecha_creacion", "fecha_limite_pago")
        }),
        ("Comprobante de Pago de Anticipo (HU 3)", {
            "fields": (
                "comprobante",
                "vista_comprobante",
                "numero_transaccion",
                "banco_origen",
                "fecha_subida_comprobante"
            ),
            "description": "Comprobante adjuntado por el cliente en formato JPG, PNG o PDF."
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

    def comprobante_link(self, obj):
        if obj.comprobante:
            if obj.es_pdf_comprobante:
                return format_html(
                    '<a href="{}" target="_blank" style="color: #dc2626; font-weight: bold;">📄 Ver PDF</a>',
                    obj.comprobante.url
                )
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="width: 32px; height: 32px; object-fit: cover; border-radius: 4px; vertical-align: middle; margin-right: 4px;" /> Ver Foto</a>',
                obj.comprobante.url,
                obj.comprobante.url
            )
        return format_html('<span style="color: #94a3b8;">Sin adjunto</span>')
    comprobante_link.short_description = "Comprobante"

    def vista_comprobante(self, obj):
        if obj.comprobante:
            if obj.es_pdf_comprobante:
                return format_html(
                    '<a href="{}" target="_blank" class="button" style="padding: 6px 12px; background: #dc2626; color: white; border-radius: 4px; text-decoration: none;">📄 Abrir Documento PDF del Comprobante</a>',
                    obj.comprobante.url
                )
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-width: 300px; max-height: 250px; border-radius: 8px; border: 1px solid #ccc; display: block; margin-top: 5px;" /></a>',
                obj.comprobante.url,
                obj.comprobante.url
            )
        return "No se ha adjuntado ningún comprobante todavía."
    vista_comprobante.short_description = "Vista Previa del Comprobante"

    def precio_total_formateado(self, obj):
        return f"${obj.precio_total:,.2f}"
    precio_total_formateado.short_description = "Total"

    def anticipo_formateado(self, obj):
        return f"${obj.monto_anticipo:,.2f}"
    anticipo_formateado.short_description = "Anticipo Req."

    def saldo_formateado(self, obj):
        return f"${obj.saldo_en_tienda:,.2f}"
    saldo_formateado.short_description = "Saldo Tienda"
