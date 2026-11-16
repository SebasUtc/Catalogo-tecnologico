from django.contrib import admin
from django.utils.html import format_html
from .models import Categoria, Marca, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug", "activo", "total_productos")
    list_filter = ("acti",)
    search_fields = ("nombre", "descripcion")
    prepopulated_fields = {"slug": ("nombre",)}

    def total_productos(self, obj):
        return obj.productos.count()
    total_productos.short_description = "Total Productos"


@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug", "activo", "total_productos")
    list_filter = ("activo",)
    search_fields = ("nombre",)
    prepopulated_fields = {"slug": ("nombre",)}

    def total_productos(self, obj):
        return obj.productos.count()
    total_productos.short_description = "Total Productos"


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "vista_previa",
        "sku",
        "nombre",
        "categoria",
        "marca",
        "precio_formateado",
        "anticipo_formateado",
        "saldo_formateado",
        "stock_disponible",
        "destacado",
        "activo",
    )
    list_filter = ("categoria", "marca", "destacado", "activo")
    search_fields = ("sku", "nombre", "descripcion_corta", "ficha_tecnica")
    prepopulated_fields = {"slug": ("nombre", "sku")}
    list_editable = ("destacado", "activo", "stock_disponible")
    readonly_fields = ("anticipo_calculado_display", "saldo_tienda_display", "fecha_creacion", "fecha_actualizacion")
    fieldsets = (
        ("Identificación del Producto", {
            "fields": ("sku", "nombre", "slug", "categoria", "marca", "activo", "destacado")
        }),
        ("Precios y Condiciones de Reserva", {
            "fields": (
                "precio",
                "porcentaje_anticipo",
                "monto_anticipo",
                "anticipo_calculado_display",
                "saldo_tienda_display",
                "stock_disponible"
            ),
            "description": "Configura el precio total y el anticipo requerido que el cliente debe consignar para apartar el artículo."
        }),
        ("Detalles y Ficha Técnica", {
            "fields": ("descripcion_corta", "ficha_tecnica")
        }),
        ("Multimedia", {
            "fields": ("imagen", "imagen_url")
        }),
        ("Auditoría", {
            "fields": ("fecha_creacion", "fecha_actualizacion"),
            "classes": ("collapse",)
        }),
    )

    def vista_previa(self, obj):
        url = obj.url_foto
        if url:
            return format_html('<img src="{}" style="width: 48px; height: 48px; object-fit: cover; border-radius: 6px;" />', url)
        return format_html('<span style="color: #999;">Sin foto</span>')
    vista_previa.short_description = "Foto"

    def precio_formateado(self, obj):
        return f"${obj.precio:,.2f}"
    precio_formateado.short_description = "Precio Total"
    precio_formateado.admin_order_field = "precio"

    def anticipo_formateado(self, obj):
        return f"${obj.anticipo_requerido:,.2f}"
    anticipo_formateado.short_description = "Anticipo Req."

    def saldo_formateado(self, obj):
        return f"${obj.saldo_en_tienda:,.2f}"
    saldo_formateado.short_description = "Saldo en Tienda"

    def anticipo_calculado_display(self, obj):
        return f"${obj.anticipo_requerido:,.2f} (calculado según política configurada)"
    anticipo_calculado_display.short_description = "Anticipo Efectivo para Reserva"

    def saldo_tienda_display(self, obj):
        return f"${obj.saldo_en_tienda:,.2f} (monto a cancelar físicamente en tienda)"
    saldo_tienda_display.short_description = "Saldo Pendiente en Tienda"
