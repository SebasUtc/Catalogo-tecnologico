from decimal import Decimal
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from productos.models import Producto
from .forms import SolicitudReservaForm
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
    Vista de confirmación y resumen de la reserva:
    - Muestra el estado actual ('Pendiente de Pago').
    - Muestra el desglose financiero (Total, Anticipo a transferir, Saldo en tienda).
    - Muestra las cuentas bancarias de la tienda para que el cliente realice la transferencia.
    """
    reserva = get_object_or_404(
        Reserva.objects.select_related('producto', 'producto__marca', 'producto__categoria'),
        codigo=codigo
    )
    cuentas = CuentaBancaria.objects.filter(activo=True)

    context = {
        'reserva': reserva,
        'cuentas': cuentas,
    }
    return render(request, 'reservas/resumen.html', context)


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
