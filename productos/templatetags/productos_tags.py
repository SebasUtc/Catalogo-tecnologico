from decimal import Decimal
from django import template

register = template.Library()


@register.filter(name='moneda')
def moneda(valor):
    """
    Formatea un valor decimal o numérico como moneda legible: $1,500.00
    """
    if valor is None:
        return "$0.00"
    try:
        if isinstance(valor, str):
            valor = Decimal(valor)
        return f"${valor:,.2f}"
    except Exception:
        return f"${valor}"
