import random
import string
from datetime import timedelta
from decimal import Decimal
from django.db import models
from django.utils import timezone
from productos.models import Producto


def generar_codigo_unico():
    """Genera un código amigable y único para la reserva, ej. RES-2026-A8K29"""
    anio = timezone.now().year
    caracteres = string.ascii_uppercase + string.digits
    sufijo = ''.join(random.choices(caracteres, k=5))
    return f"RES-{anio}-{sufijo}"


class CuentaBancaria(models.Model):
    """
    Cuentas bancarias de la tienda tecnológica donde los clientes
    deben consignar o transferir el anticipo para apartar su cupo.
    """
    banco = models.CharField(
        max_length=100,
        verbose_name="Entidad Bancaria / Plataforma",
        help_text="Ej: Banco Pichincha, Bancolombia, BBVA, BCP, Nequi, etc."
    )
    tipo_cuenta = models.CharField(
        max_length=50,
        verbose_name="Tipo de Cuenta",
        help_text="Ej: Cuenta Corriente, Cuenta de Ahorros, Billetera Digital"
    )
    numero_cuenta = models.CharField(
        max_length=60,
        verbose_name="Número de Cuenta / Llave"
    )
    titular = models.CharField(
        max_length=150,
        verbose_name="Nombre del Titular"
    )
    documento_titular = models.CharField(
        max_length=50,
        verbose_name="Documento / RUC / Cédula del Titular"
    )
    correo_notificacion = models.EmailField(
        blank=True,
        verbose_name="Correo para Notificación de Transferencias"
    )
    instrucciones = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Instrucciones breves",
        help_text="Ej: Colocar el código de reserva en el concepto de la transferencia"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Visible para clientes"
    )
    orden = models.PositiveIntegerField(
        default=1,
        verbose_name="Orden de visualización"
    )

    class Meta:
        verbose_name = "Cuenta Bancaria de la Tienda"
        verbose_name_plural = "Cuentas Bancarias de la Tienda"
        ordering = ["orden", "banco"]

    def __str__(self):
        return f"{self.banco} ({self.tipo_cuenta}) - {self.numero_cuenta}"


class Reserva(models.Model):
    """
    Modelo de Reserva para apartar cupo en el lote.
    Estado inicial: 'Pendiente de Pago' hasta que el cliente transfiera el anticipo.
    """
    ESTADO_PENDIENTE_PAGO = 'PENDIENTE_PAGO'
    ESTADO_COMPROBANTE_SUBIDO = 'COMPROBANTE_SUBIDO'
    ESTADO_CONFIRMADA = 'CONFIRMADA'
    ESTADO_ENTREGADA = 'ENTREGADA'
    ESTADO_CANCELADA = 'CANCELADA'

    ESTADOS_CHOICES = [
        (ESTADO_PENDIENTE_PAGO, 'Pendiente de Pago'),
        (ESTADO_COMPROBANTE_SUBIDO, 'Comprobante Subido / Por Verificar'),
        (ESTADO_CONFIRMADA, 'Confirmada (Cupo Apartado)'),
        (ESTADO_ENTREGADA, 'Entregada y Liquidada en Tienda'),
        (ESTADO_CANCELADA, 'Cancelada'),
    ]

    codigo = models.CharField(
        max_length=25,
        unique=True,
        db_index=True,
        editable=False,
        verbose_name="Código de Reserva"
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="reservas",
        verbose_name="Producto Reservado"
    )
    cantidad = models.PositiveIntegerField(
        default=1,
        verbose_name="Cantidad apartada"
    )

    # Valores congelados al momento de solicitar la reserva
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio Unitario ($)"
    )
    precio_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio Total ($)"
    )
    monto_anticipo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Monto de Anticipo Requerido ($)"
    )
    saldo_en_tienda = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Saldo a Liquidar en Tienda ($)"
    )

    # Datos del Cliente para apartar el cupo
    nombre_cliente = models.CharField(
        max_length=150,
        verbose_name="Nombre Completo del Cliente"
    )
    email_cliente = models.EmailField(
        verbose_name="Correo Electrónico"
    )
    telefono_cliente = models.CharField(
        max_length=35,
        verbose_name="Teléfono / WhatsApp"
    )
    documento_identidad = models.CharField(
        max_length=35,
        verbose_name="Documento de Identidad (C.I. / DNI / Pasaporte)"
    )
    notas = models.TextField(
        blank=True,
        verbose_name="Notas u Observaciones"
    )

    # Estado y Auditoría
    estado = models.CharField(
        max_length=30,
        choices=ESTADOS_CHOICES,
        default=ESTADO_PENDIENTE_PAGO,
        verbose_name="Estado de la Reserva"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Solicitud"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Modificación"
    )
    fecha_limite_pago = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha Límite para Anticipo",
        help_text="Plazo máximo para transferir el anticipo antes de liberar el cupo"
    )

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ["-fecha_creacion"]

    def save(self, *args, **kwargs):
        # Generar código único si no existe
        if not self.codigo:
            nuevo_codigo = generar_codigo_unico()
            while Reserva.objects.filter(codigo=nuevo_codigo).exists():
                nuevo_codigo = generar_codigo_unico()
            self.codigo = nuevo_codigo

        # Asignar fecha límite por defecto (24 horas después de la solicitud)
        if not self.fecha_limite_pago:
            self.fecha_limite_pago = timezone.now() + timedelta(hours=24)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.nombre_cliente} ({self.producto.nombre}) [{self.get_estado_display()}]"
