from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, render
from .models import Categoria, Marca, Producto


# Muestra el catálogo con búsqueda, filtros, ordenamiento y paginación.
def catalogo_view(request):
    """
    Vista principal del catálogo para HU 1:
    - Muestra foto, SKU, ficha, precio y anticipo.
    - Filtra por marca y por categoría.
    - Soporta búsqueda por texto y ordenamiento.
    """
    productos = Producto.objects.filter(activo=True).select_related('categoria', 'marca')

    # Parámetros de filtrado
    categoria_slug = request.GET.get('categoria', '').strip()
    marca_slug = request.GET.get('marca', '').strip()
    query = request.GET.get('q', '').strip()
    orden = request.GET.get('orden', 'recientes')

    # Filtro por Categoría
    categoria_actual = None
    if categoria_slug:
        categoria_actual = get_object_or_404(Categoria, slug=categoria_slug, activo=True)
        productos = productos.filter(categoria=categoria_actual)

    # Filtro por Marca
    marca_actual = None
    if marca_slug:
        marca_actual = get_object_or_404(Marca, slug=marca_slug, activo=True)
        productos = productos.filter(marca=marca_actual)

    # Búsqueda por SKU, nombre o descripción
    if query:
        productos = productos.filter(
            Q(sku__icontains=query) |
            Q(nombre__icontains=query) |
            Q(descripcion_corta__icontains=query) |
            Q(ficha_tecnica__icontains=query)
        )

    # Ordenamiento
    if orden == 'precio_asc':
        productos = productos.order_by('precio')
    elif orden == 'precio_desc':
        productos = productos.order_by('-precio')
    elif orden == 'nombre':
        productos = productos.order_by('nombre')
    else:  # recientes o destacados primero
        productos = productos.order_by('-destacado', '-fecha_creacion')

    total_resultados = productos.count()

    # Paginación (9 productos por página)
    paginator = Paginator(productos, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Listados para los filtros laterales con contador de productos activos
    categorias = (
        Categoria.objects.filter(activo=True)
        .annotate(total=Count('productos', filter=Q(productos__activo=True)))
        .order_by('nombre')
    )
    marcas = (
        Marca.objects.filter(activo=True)
        .annotate(total=Count('productos', filter=Q(productos__activo=True)))
        .order_by('nombre')
    )

    # Preservar parámetros en la paginación
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    query_string = query_params.urlencode()

    context = {
        'page_obj': page_obj,
        'productos': page_obj.object_list,
        'categorias': categorias,
        'marcas': marcas,
        'categoria_actual': categoria_actual,
        'marca_actual': marca_actual,
        'categoria_slug': categoria_slug,
        'marca_slug': marca_slug,
        'query': query,
        'orden': orden,
        'total_resultados': total_resultados,
        'query_string': query_string,
    }
    return render(request, 'productos/catalogo.html', context)


# Presenta la ficha completa de un producto y opciones relacionadas.
def detalle_producto_view(request, slug):
    """
    Vista detallada del producto para evaluar la reserva:
    Muestra ficha técnica completa, desglose de precio y anticipo requerido,
    saldo a liquidar en tienda física y pasos del proceso.
    """
    producto = get_object_or_404(
        Producto.objects.select_related('categoria', 'marca'),
        slug=slug,
        activo=True
    )

    # Productos relacionados de la misma categoría o marca
    relacionados = (
        Producto.objects.filter(activo=True, categoria=producto.categoria)
        .exclude(id=producto.id)
        .select_related('categoria', 'marca')[:4]
    )

    context = {
        'producto': producto,
        'ficha_items': producto.ficha_tecnica_lista(),
        'relacionados': relacionados,
    }
    return render(request, 'productos/detalle.html', context)
