from django import forms
from .models import Reserva


class SolicitudReservaForm(forms.ModelForm):
    """
    Formulario para que el cliente solicite una reserva y aparte cupo en el lote.
    """
    cantidad = forms.IntegerField(
        min_value=1,
        initial=1,
        label="Cantidad a Reservar",
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg text-center fw-bold',
            'min': '1',
            'id': 'id_cantidad'
        })
    )

    class Meta:
        model = Reserva
        fields = [
            'cantidad',
            'nombre_cliente',
            'email_cliente',
            'telefono_cliente',
            'documento_identidad',
            'notas'
        ]
        widgets = {
            'nombre_cliente': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Carlos Mendoza',
                'required': 'required'
            }),
            'email_cliente': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. carlos.mendoza@email.com',
                'required': 'required'
            }),
            'telefono_cliente': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. +57 300 123 4567 / WhatsApp',
                'required': 'required'
            }),
            'documento_identidad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. C.I. / DNI / Cédula / RUT',
                'required': 'required'
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '¿Alguna indicación especial o preferencia de horario para retiro?'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.producto = kwargs.pop('producto', None)
        super().__init__(*args, **kwargs)
        if self.producto:
            max_stock = max(1, self.producto.stock_disponible)
            self.fields['cantidad'].widget.attrs['max'] = str(max_stock)
            self.fields['cantidad'].help_text = f"Cupos disponibles en este lote: {self.producto.stock_disponible}"

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if not cantidad or cantidad < 1:
            raise forms.ValidationError("La cantidad a apartar debe ser de al menos 1 unidad.")

        if self.producto and cantidad > self.producto.stock_disponible:
            raise forms.ValidationError(
                f"No hay suficientes cupos disponibles en este lote. Máximo disponible: {self.producto.stock_disponible} unidad(es)."
            )
        return cantidad


class SubirComprobanteForm(forms.ModelForm):
    """
    Formulario para HU 3: 'Como cliente, quiero subir el comprobante de anticipo para registrar el pago.'
    Condición: 'Permite adjuntar JPG/PNG/PDF. Pasa a Comprobante en Revisión.'
    """
    class Meta:
        model = Reserva
        fields = ['comprobante', 'banco_origen', 'numero_transaccion']
        widgets = {
            'comprobante': forms.FileInput(attrs={
                'class': 'form-control form-control-lg',
                'accept': '.jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf',
                'id': 'id_comprobante',
                'required': 'required'
            }),
            'banco_origen': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Bancolombia, Banco Pichincha, Nequi...'
            }),
            'numero_transaccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Nro. de aprobación o referencia bancaria'
            }),
        }

    def clean_comprobante(self):
        archivo = self.cleaned_data.get('comprobante')
        if not archivo:
            raise forms.ValidationError("Debes adjuntar el archivo de tu comprobante de pago.")
        return archivo
