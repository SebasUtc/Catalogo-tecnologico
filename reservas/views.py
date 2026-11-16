from decimal import Decimal
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from productos.models import Producto
from .forms import SolicitudReservaForm, SubirComprobanteForm
from .models import CuentaBancaria, Reserva


def solicitar_reserva_view(request, slug):
    """
    HU 2: Solicitar reserva para apartar cupo en el lote.
    - Calcula el anticipo según la cantidad solicitada.
    - Muestra las cuentas bancarias autorizadas de la tienda.
    - Crea la reserva en estado 'Pendiente de Pago'.
    """
    producto = get_object_or_404(Producto, slug=slug, activo=True)
    cuentas = CuentaBancaria.objects.filter(activo=True)

    if producto.stock_disponible <= 0:
        messages.error(
            request,
            f"Lo sentimos, no hay cupos disponibles actualmente para el lote de {producto.nombre}."
        )
        return redirect('productos:detalle', slug=producto.slug)

    if request.method == 'POST':
        form = SolicitudReservaForm(request.POST, producto=producto)
        if form.is_valid():
            with transaction.atomic():
                reserva = form.save(commit=False)
                cantidad = form.cleaned_data['cantidad']

                # 1. Cálculo del anticipo y precios del lote apartado
                precio_total = producto.precio * cantidad
                anticipo_total = producto.anticipo_requerido * cantidad
                saldo_tienda = precio_total - anticipo_total

                reserva.producto = producto
                reserva.cantidad = cantidad
                reserva.precio_unitario = producto.precio
                reserva.precio_total = precio_total
                reserva.monto_anticipo = anticipo_total
                reserva.saldo_en_tienda = saldo_tienda
                
                # 2. Estado obligatorio: Pendiente de Pago
                reserva.estado = Reserva.ESTADO_PENDIENTE_PAGO
                reserva.save()

                # 3. Apartar cupo del lote (descontar del stock disponible)
                producto.stock_disponible = max(0, producto.stock_disponible - cantidad)
                producto.save(update_fields=['stock_disponible'])

            messages.success(
                request,
                f"¡Tu cupo ha sido apartado provisionalmente! Tu reserva {reserva.codigo} fue creada en estado 'Pendiente de Pago'."
            )
            return redirect('reservas:resumen', codigo=reserva.codigo)
    else:
        form = SolicitudReservaForm(producto=producto)

    context = {
        'producto': producto,
        'form': form,
        'cuentas': cuentas,
        'anticipo_unitario': producto.anticipo_requerido,
        'precio_unitario': producto.precio,
        'saldo_unitario': producto.saldo_en_tienda,
    }
    return render(request, 'reservas/solicitar.html', context)


def resumen_reserva_view(request, codigo):
    """
    Vista de confirmación y resumen de la reserva para el cliente:
    - Muestra estado dinámico: 'Pendiente de Pago', 'Comprobante en Revisión',
      'Reserva Confirmada' (HU 4) o 'Comprobante Rechazado' (con motivo).
    - Desglose financiero y cuentas bancarias.
    - Formulario de subida de comprobante (HU 3).
    """
    reserva = get_object_or_404(
        Reserva.objects.select_related('producto', 'producto__marca', 'producto__categoria'),
        codigo=codigo
    )
    cuentas = CuentaBancaria.objects.filter(activo=True)
    form_comprobante = SubirComprobanteForm(instance=reserva)

    context = {
        'reserva': reserva,
        'cuentas': cuentas,
        'form_comprobante': form_comprobante,
    }
    return render(request, 'reservas/resumen.html', context)


def subir_comprobante_view(request, codigo):
    """
    HU 3: Como cliente, quiero subir el comprobante de anticipo para registrar el pago.
    Condición: 'Permite adjuntar JPG/PNG/PDF. Pasa a Comprobante en Revisión.'
    """
    reserva = get_object_or_404(
        Reserva.objects.select_related('producto', 'producto__marca'),
        codigo=codigo
    )

    if request.method == 'POST':
        form = SubirComprobanteForm(request.POST, request.FILES, instance=reserva)
        if form.is_valid():
            reserva = form.save(commit=False)
            
            # Criterio clave HU 3: Pasa a Comprobante en Revisión
            reserva.estado = Reserva.ESTADO_COMPROBANTE_REVISION
            reserva.fecha_subida_comprobante = timezone.now()
            reserva.save()

            messages.success(
                request,
                f"¡Comprobante adjuntado con éxito! Tu reserva {reserva.codigo} ha pasado a estado 'Comprobante en Revisión'. "
                f"Un asesor de nuestro centro tecnológico verificará el anticipo para confirmar tu cupo."
            )
            return redirect('reservas:resumen', codigo=reserva.codigo)
        else:
            cuentas = CuentaBancaria.objects.filter(activo=True)
            messages.error(
                request,
                "No fue posible adjuntar el comprobante. Verifica que el archivo sea JPG, PNG o PDF (máx. 10 MB)."
            )
            return render(request, 'reservas/resumen.html', {
                'reserva': reserva,
                'cuentas': cuentas,
                'form_comprobante': form,
            })

    return redirect('reservas:resumen', codigo=reserva.codigo)


def consultar_reserva_view(request):
    """
    Permite al cliente buscar y revisar el estado de su reserva mediante su código.
    """
    codigo = request.GET.get('codigo', '').strip()
    reserva = None
    error = None

    if codigo:
        try:
            reserva = Reserva.objects.select_related('producto', 'producto__marca').get(codigo__iexact=codigo)
            return redirect('reservas:resumen', codigo=reserva.codigo)
        except Reserva.DoesNotExist:
            error = f"No se encontró ninguna reserva registrada con el código '{codigo}'."

    return render(request, 'reservas/consultar.html', {'error': error, 'codigo_busqueda': codigo})


# ==============================================================================
# HU 4: PANEL DEL GESTOR FINANCIERO (VALIDACIÓN DE COMPROBANTES DE ABONO)
# ==============================================================================

@staff_member_required(login_url='/admin/login/?next=/reservas/panel-financiero/')
def panel_financiero_view(request):
    """
    HU 4: 'Como gestor financiero, quiero validar comprobantes para confirmar el abono.'
    Criterio de Aceptación: 'Panel para aprobar o rechazar con motivo. Pasa a Reserva Confirmada.'
    """
    filtro = request.GET.get('filtro', 'revision').strip()
    query = request.GET.get('q', '').strip()

    reservas = Reserva.objects.select_related('producto', 'producto__marca', 'validado_por')

    # Métricas para el Gestor Financiero
    total_en_revision = Reserva.objects.filter(estado=Reserva.ESTADO_COMPROBANTE_REVISION).count()
    total_confirmadas = Reserva.objects.filter(estado=Reserva.ESTADO_CONFIRMADA).count()
    total_rechazadas = Reserva.objects.filter(estado=Reserva.ESTADO_RECHAZADA).count()
    total_pendientes_pago = Reserva.objects.filter(estado=Reserva.ESTADO_PENDIENTE_PAGO).count()

    suma_anticipos_confirmados = (
        Reserva.objects.filter(estado=Reserva.ESTADO_CONFIRMADA)
        .aggregate(total=Sum('monto_anticipo'))['total'] or Decimal('0.00')
    )

    # Filtrado por pestaña de estado
    if filtro == 'revision':
        reservas = reservas.filter(estado=Reserva.ESTADO_COMPROBANTE_REVISION)
    elif filtro == 'confirmadas':
        reservas = reservas.filter(estado=Reserva.ESTADO_CONFIRMADA)
    elif filtro == 'rechazadas':
        reservas = reservas.filter(estado=Reserva.ESTADO_RECHAZADA)
    elif filtro == 'pendientes':
        reservas = reservas.filter(estado=Reserva.ESTADO_PENDIENTE_PAGO)
    # 'todas': no aplica filtro de estado

    # Búsqueda por texto (código, cliente, documento, teléfono, producto)
    if query:
        reservas = reservas.filter(
            Q(codigo__icontains=query) |
            Q(nombre_cliente__icontains=query) |
            Q(documento_identidad__icontains=query) |
            Q(telefono_cliente__icontains=query) |
            Q(producto__nombre__icontains=query) |
            Q(numero_transaccion__icontains=query)
        )

    context = {
        'reservas': reservas,
        'filtro_actual': filtro,
        'query': query,
        'total_en_revision': total_en_revision,
        'total_confirmadas': total_confirmadas,
        'total_rechazadas': total_rechazadas,
        'total_pendientes_pago': total_pendientes_pago,
        'suma_anticipos_confirmados': suma_anticipos_confirmados,
    }
    return render(request, 'reservas/panel_financiero.html', context)


@staff_member_required(login_url='/admin/login/?next=/reservas/panel-financiero/')
def aprobar_reserva_view(request, codigo):
    """
    HU 4: Acción de Aprobar Abono.
    Pasa la reserva a estado 'Reserva Confirmada'.
    """
    reserva = get_object_or_404(Reserva, codigo=codigo)

    if request.method == 'POST':
        reserva.aprobar_abono(usuario=request.user)
        messages.success(
            request,
            f"✓ Reserva {reserva.codigo} aprobada exitosamente. El abono de ${reserva.monto_anticipo:,.2f} fue confirmado. "
            f"El estado pasó a 'Reserva Confirmada'."
        )
    return redirect('reservas:panel_financiero')


@staff_member_required(login_url='/admin/login/?next=/reservas/panel-financiero/')
def rechazar_reserva_view(request, codigo):
    """
    HU 4: Acción de Rechazar con motivo.
    Permite ingresar la razón del rechazo y almacena el motivo para el cliente.
    """
    reserva = get_object_or_404(Reserva, codigo=codigo)

    if request.method == 'POST':
        motivo = request.POST.get('motivo_rechazo', '').strip()
        if not motivo:
            motivo = "Comprobante no valido o valor no acreditado en las cuentas bancarias de la tienda."

        reserva.rechazar_abono(motivo=motivo, usuario=request.user)
        messages.warning(
            request,
            f"⚠ Reserva {reserva.codigo} rechazada. Se registro el motivo: '{motivo}' para notificación al cliente."
        )
    return redirect('reservas:panel_financiero')
