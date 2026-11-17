from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from productos.models import Categoria, Marca, Producto


class CatalogoProductosTests(TestCase):
    """
    Pruebas unitarias y de integración para Sprint 1:
    HU 1: 'Como cliente, quiero ver productos y anticipos para evaluar mi reserva'
    Criterios de aceptación:
    - Muestra foto, SKU, ficha, precio y anticipo.
    - Filtra por marca y categoría.
    """

    def setUp(self):
        self.client = Client()

        # Categorías de prueba
        self.cat_laptops = Categoria.objects.create(
            nombre="Laptops", slug="laptops", icono="bi-laptop"
        )
        self.cat_moviles = Categoria.objects.create(
            nombre="Móviles", slug="moviles", icono="bi-phone"
        )

        # Marcas de prueba
        self.marca_asus = Marca.objects.create(nombre="ASUS", slug="asus")
        self.marca_apple = Marca.objects.create(nombre="Apple", slug="apple")

        # Producto 1: Con porcentaje de anticipo (20%)
        self.prod_asus = Producto.objects.create(
            sku="LAP-ASUS-001",
            nombre="Laptop ASUS ROG Strix",
            slug="laptop-asus-rog-strix",
            categoria=self.cat_laptops,
            marca=self.marca_asus,
            descripcion_corta="Laptop gamer de alto rendimiento",
            ficha_tecnica="Procesador: AMD Ryzen 9\nRAM: 32 GB\nAlmacenamiento: 1 TB SSD",
            precio=Decimal("1500.00"),
            porcentaje_anticipo=Decimal("20.00"),
            stock_disponible=5,
            activo=True,
            destacado=True,
            imagen_url="https://example.com/asus.jpg"
        )

        # Producto 2: Con monto fijo de anticipo ($300.00)
        self.prod_apple = Producto.objects.create(
            sku="PHN-APL-002",
            nombre="iPhone 15 Pro",
            slug="iphone-15-pro",
            categoria=self.cat_moviles,
            marca=self.marca_apple,
            descripcion_corta="Smartphone en titanio",
            ficha_tecnica="Chip: A17 Pro\nPantalla: 6.1 OLED\nCámara: 48 MP",
            precio=Decimal("1200.00"),
            monto_anticipo=Decimal("300.00"),
            stock_disponible=3,
            activo=True,
            destacado=False,
            imagen_url="https://example.com/iphone.jpg"
        )

    def test_calculo_anticipo_porcentual_y_saldo(self):
        """Verifica que el anticipo se calcule adecuadamente según el porcentaje y el saldo en tienda."""
        # 20% de 1500.00 = 300.00
        self.assertEqual(self.prod_asus.anticipo_requerido, Decimal("300.00"))
        # Saldo en tienda: 1500.00 - 300.00 = 1200.00
        self.assertEqual(self.prod_asus.saldo_en_tienda, Decimal("1200.00"))

    def test_calculo_anticipo_monto_fijo(self):
        """Verifica que si se especifica un monto_anticipo fijo, este tenga prioridad."""
        # Monto fijo = 300.00
        self.assertEqual(self.prod_apple.anticipo_requerido, Decimal("300.00"))
        # Saldo en tienda: 1200.00 - 300.00 = 900.00
        self.assertEqual(self.prod_apple.saldo_en_tienda, Decimal("900.00"))

    def test_parseo_ficha_tecnica(self):
        """Verifica que la ficha técnica se convierta en una lista de clave y valor."""
        items = self.prod_asus.ficha_tecnica_lista()
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0]["clave"], "Procesador")
        self.assertEqual(items[0]["valor"], "AMD Ryzen 9")

    def test_vista_catalogo_muestra_elementos_criterio_aceptacion(self):
        """
        Criterio: Muestra foto, SKU, ficha (o resumen), precio y anticipo.
        """
        response = self.client.get(reverse('productos:catalogo'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Sprint 1 • HU 1: Catálogo y Evaluación de Anticipos")
        self.assertContains(response, "Catálogo de Equipos y Reservas")

        # SKU
        self.assertContains(response, "LAP-ASUS-001")
        self.assertContains(response, "PHN-APL-002")

        # Foto / URL
        self.assertContains(response, "https://example.com/asus.jpg")

        # Ficha / Resumen
        self.assertContains(response, "Laptop gamer de alto rendimiento")

        # Precio total
        self.assertContains(response, "1,500")

        # Anticipo
        self.assertContains(response, "300")

    def test_filtro_por_categoria(self):
        """Criterio: Filtra por categoría."""
        # Filtrar por laptops
        response = self.client.get(reverse('productos:catalogo'), {'categoria': 'laptops'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "LAP-ASUS-001")
        self.assertNotContains(response, "PHN-APL-002")

        # Filtrar por móviles
        response_moviles = self.client.get(reverse('productos:catalogo'), {'categoria': 'moviles'})
        self.assertEqual(response_moviles.status_code, 200)
        self.assertContains(response_moviles, "PHN-APL-002")
        self.assertNotContains(response_moviles, "LAP-ASUS-001")

    def test_filtro_por_marca(self):
        """Criterio: Filtra por marca."""
        # Filtrar por ASUS
        response = self.client.get(reverse('productos:catalogo'), {'marca': 'asus'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Laptop ASUS ROG Strix")
        self.assertNotContains(response, "iPhone 15 Pro")

        # Filtrar por Apple
        response_apple = self.client.get(reverse('productos:catalogo'), {'marca': 'apple'})
        self.assertEqual(response_apple.status_code, 200)
        self.assertContains(response_apple, "iPhone 15 Pro")
        self.assertNotContains(response_apple, "Laptop ASUS ROG Strix")

    def test_filtro_combinado_marca_y_categoria(self):
        """Verifica el filtrado simultáneo por marca y categoría."""
        response = self.client.get(reverse('productos:catalogo'), {'categoria': 'laptops', 'marca': 'asus'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "LAP-ASUS-001")

        # Combinación inexistente
        response_vacia = self.client.get(reverse('productos:catalogo'), {'categoria': 'moviles', 'marca': 'asus'})
        self.assertEqual(response_vacia.status_code, 200)
        self.assertContains(response_vacia, "No se encontraron productos con estos criterios")

    def test_vista_detalle_producto(self):
        """Verifica que la página de detalle muestre la ficha completa y desglose de reserva."""
        response = self.client.get(reverse('productos:detalle', kwargs={'slug': self.prod_asus.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "LAP-ASUS-001")
        self.assertContains(response, "AMD Ryzen 9")
        self.assertContains(response, "Ficha Técnica y Especificaciones")
        self.assertContains(response, "Anticipo Requerido")
        self.assertContains(response, "Saldo a pagar en tienda")
