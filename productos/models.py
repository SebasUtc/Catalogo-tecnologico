from decimal import Decimal
from django.db import models
from django.utils.text import slugify


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    icono = models.CharField(
        max_length=50,
        blank=True,
        default="bi-laptop",
        verbose_name="Ícono (Bootstrap Icons / Identificador)",
        help_text="Clase del ícono, ej: bi-laptop, bi-phone, bi-controller"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["nombre"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Marca(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Activa")

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        ordering = ["nombre"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    sku = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name="Código SKU",
        help_text="Identificador único del producto en inventario"
    )
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Producto")
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos",
        verbose_name="Categoría"
    )
    marca = models.ForeignKey(
        Marca,
        on_delete=models.PROTECT,
        related_name="productos",
        verbose_name="Marca"
    )
    descripcion_corta = models.CharField(
        max_length=250,
        blank=True,
        verbose_name="Descripción Breve",
        help_text="Resumen llamativo para la tarjeta del producto"
    )
    ficha_tecnica = models.TextField(
        verbose_name="Ficha Técnica / Especificaciones",
        help_text="Especificaciones en formato 'Característica: Detalle' (una por línea)"
    )
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio Total ($)",
        help_text="Precio total de venta del producto"
    )
    porcentaje_anticipo = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('20.00'),
        verbose_name="Porcentaje de Anticipo (%)",
        help_text="Porcentaje sugerido para apartar o reservar (ej. 20%)"
    )
    monto_anticipo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Monto Fijo de Anticipo ($)",
        help_text="Opcional. Si se define, sobrescribe el cálculo porcentual"
    )
    imagen = models.ImageField(
        upload_to="productos/",
        blank=True,
        null=True,
        verbose_name="Foto del Producto"
    )
    imagen_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="URL de Imagen Externa",
        help_text="Enlace a imagen externa en caso de no subir archivo local"
    )
    stock_disponible = models.PositiveIntegerField(
        default=5,
        verbose_name="Stock Disponible para Reserva"
    )
    destacado = models.BooleanField(
        default=False,
        verbose_name="Destacado en Portada"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Visible en Catálogo"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["-destacado", "-fecha_creacion"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.nombre}-{self.sku}")
            self.slug = base_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.sku}] {self.nombre} - ${self.precio:,.2f}"

    @property
    def anticipo_requerido(self):
        """Calcula el anticipo necesario para reservar el producto."""
        if self.monto_anticipo is not None and self.monto_anticipo > 0:
            return self.monto_anticipo
        if self.precio and self.porcentaje_anticipo:
            return (self.precio * (self.porcentaje_anticipo / Decimal('100'))).quantize(Decimal('0.01'))
        return Decimal('0.00')

    @property
    def saldo_en_tienda(self):
        """Monto restante que el cliente terminará de liquidar en la tienda física."""
        if self.precio:
            return max(Decimal('0.00'), self.precio - self.anticipo_requerido)
        return Decimal('0.00')

    @property
    def url_foto(self):
        """
        Retorna la URL de la foto local del producto (almacenada en media/productos/ o static/img/productos/).
        Garantiza que las imágenes se sirvan de forma 100% local sin llamadas a internet.
        """
        if self.imagen:
            try:
                return self.imagen.url
            except Exception:
                pass
        # Fallback local en static por SKU
        import os
        from django.conf import settings
        static_img = os.path.join(settings.BASE_DIR, 'static', 'img', 'productos', f"{self.sku}.jpg")
        if os.path.exists(static_img):
            return f"{settings.STATIC_URL}img/productos/{self.sku}.jpg"
        if self.imagen_url:
            return self.imagen_url
        return None

    def ficha_tecnica_lista(self):
        """
        Retorna la ficha técnica como lista de diccionarios {clave, valor}
        para mostrar en tablas o listas estructuradas.
        """
        resultado = []
        if not self.ficha_tecnica:
            return resultado

        for linea in self.ficha_tecnica.strip().splitlines():
            linea_limpia = linea.strip().lstrip("-*•").strip()
            if not linea_limpia:
                continue
            if ":" in linea_limpia:
                partes = linea_limpia.split(":", 1)
                resultado.append({
                    "clave": partes[0].strip(),
                    "valor": partes[1].strip()
                })
            else:
                resultado.append({
                    "clave": "Característica",
                    "valor": linea_limpia
                })
        return resultado
