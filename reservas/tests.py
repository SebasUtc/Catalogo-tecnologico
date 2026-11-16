from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from productos.models import Categoria, Marca, Producto
from reservas.models import CuentaBancaria, Reserva


class SolicitudReservaTests(TestCase):
    """
    Suite de pruebas para HU 2 y HU 3:
    - HU 2: 'Como cliente, quiero solicitar una reserva para apartar cupo en el lote.'
      Criterio: 'Calcula anticipo, muestra cuentas y crea reserva en Pendiente de Pago.'
    - HU 3: 'Como cliente, quiero subir el comprobante de anticipo para registrar el pago.'
      Criterio: 'Permite adjuntar JPG/PNG/PDF. Pasa a Comprobante en Revisión.'
    """

    def setUp(self):
        self.client = Client()

        self.categoria = Categoria.objects.create(nombre="Laptops", slug="laptops")
        self.marca = Marca.objects.create(nombre="ASUS ROG", slug="asus-rog")

        self.producto = Producto.objects.create(
            sku="LAP-ROG-TEST",
            nombre="ASUS ROG Zephyrus G16",
            slug="asus-rog-zephyrus-g16",
            categoria=self.categoria,
            marca=self.marca,
            descripcion_corta="Laptop gamer ultra rápida",
            ficha_tecnica="RAM: 32GB\nSSD: 1TB",
            precio=Decimal("2000.00"),
            porcentaje_anticipo=Decimal("20.00"),  # Anticipo: $400.00 por unidad
            stock_disponible=5,
            activo=True
        )

        self.cuenta_1 = CuentaBancaria.objects.create(
            banco="Banco Nacional",
            tipo_cuenta="Cuenta Corriente",
            numero_cuenta="1234-5678-90",
            titular="Tech Store S.A.S.",
            documento_titular="NIT: 900.123.456",
            activo=True,
            orden=1
        )

        self.cuenta_inactiva = CuentaBancaria.objects.create(
            banco="Banco Inactivo",
            tipo_cuenta="Ahorros",
            numero_cuenta="9999-9999-99",
            titular="Tech Store",
            documento_titular="NIT: 900.123.456",
            activo=False,
            orden=2
        )

    def test_vista_solicitar_reserva_muestra_cuentas_y_calculo_anticipo(self):
        """
        Verifica que la página de solicitud calcule el anticipo y muestre las cuentas bancarias autorizadas.
        """
        response = self.client.get(reverse('reservas:solicitar', kwargs={'slug': self.producto.slug}))
        self.assertEqual(response.status_code, 200)

        # Muestra información del producto y cálculo de anticipo
        self.assertContains(response, "ASUS ROG Zephyrus G16")
        self.assertContains(response, "LAP-ROG-TEST")
        self.assertContains(response, "$400.00")  # 20% de 2000.00

        # "Muestra cuentas": La cuenta activa debe estar presente, la inactiva no
        self.assertContains(response, "Banco Nacional")
        self.assertContains(response, "1234-5678-90")
        self.assertNotContains(response, "Banco Inactivo")

    def test_creacion_reserva_calcula_anticipo_y_asigna_pendiente_de_pago(self):
        """
        Verifica la condición clave de HU 2:
        'Calcula anticipo, muestra cuentas y crea reserva en Pendiente de Pago.'
        """
        datos = {
            'cantidad': 2,
            'nombre_cliente': 'Alejandro Morales',
            'email_cliente': 'alejandro.morales@test.com',
            'telefono_cliente': '+57 310 987 6543',
            'documento_identidad': 'CC 10203040',
            'notas': 'Retiro en la tarde'
        }

        response = self.client.post(
            reverse('reservas:solicitar', kwargs={'slug': self.producto.slug}),
            data=datos
        )

        # Debe redirigir al resumen de la reserva
        self.assertEqual(response.status_code, 302)

        # Verificar existencia en BD
        reserva = Reserva.objects.get(documento_identidad='CC 10203040')
        self.assertIsNotNone(reserva.codigo)

        # 1. Estado en "Pendiente de Pago"
        self.assertEqual(reserva.estado, Reserva.ESTADO_PENDIENTE_PAGO)
        self.assertEqual(reserva.get_estado_display(), 'Pendiente de Pago')

        # 2. Cálculos financieros (2 unidades * 2000.00 = 4000.00; anticipo = 800.00)
        self.assertEqual(reserva.cantidad, 2)
        self.assertEqual(reserva.precio_total, Decimal("4000.00"))
        self.assertEqual(reserva.monto_anticipo, Decimal("800.00"))
        self.assertEqual(reserva.saldo_en_tienda, Decimal("3200.00"))

        # 3. Apartar cupo del lote: el stock disponible disminuye de 5 a 3
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock_disponible, 3)

        # Redirección correcta a la vista de resumen
        self.assertRedirects(response, reverse('reservas:resumen', kwargs={'codigo': reserva.codigo}))

    def test_vista_resumen_muestra_estado_pendiente_de_pago_y_cuentas(self):
        """
        Verifica que en el resumen de la reserva se muestre claramente:
        - Estado 'Pendiente de Pago'
        - El monto exacto de anticipo a transferir
        - Las cuentas bancarias autorizadas
        """
        reserva = Reserva.objects.create(
            producto=self.producto,
            cantidad=1,
            precio_unitario=Decimal("2000.00"),
            precio_total=Decimal("2000.00"),
            monto_anticipo=Decimal("400.00"),
            saldo_en_tienda=Decimal("1600.00"),
            nombre_cliente="Beatriz Gómez",
            email_cliente="beatriz@test.com",
            telefono_cliente="+57 320 111 2233",
            documento_identidad="CC 98765432",
            estado=Reserva.ESTADO_PENDIENTE_PAGO
        )

        response = self.client.get(reverse('reservas:resumen', kwargs={'codigo': reserva.codigo}))
        self.assertEqual(response.status_code, 200)

        # Estado Pendiente de Pago
        self.assertContains(response, "Pendiente de Pago")
        self.assertContains(response, reserva.codigo)

        # Monto de anticipo
        self.assertContains(response, "$400.00")
        self.assertContains(response, "$1,600.00")

        # Muestra cuentas
        self.assertContains(response, "Banco Nacional")
        self.assertContains(response, "1234-5678-90")

    def test_validacion_stock_insuficiente(self):
        """
        Verifica que no se pueda reservar una cantidad superior al cupo/stock disponible en el lote.
        """
        datos = {
            'cantidad': 10,  # El stock es 5
            'nombre_cliente': 'Cliente Exceso',
            'email_cliente': 'exceso@test.com',
            'telefono_cliente': '123456789',
            'documento_identidad': 'CC 000000',
        }

        response = self.client.post(
            reverse('reservas:solicitar', kwargs={'slug': self.producto.slug}),
            data=datos
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response,
            'form',
            'cantidad',
            "No hay suficientes cupos disponibles en este lote. Máximo disponible: 5 unidad(es)."
        )
        # No se crea la reserva
        self.assertEqual(Reserva.objects.count(), 0)

    def test_consulta_reserva_por_codigo(self):
        """
        Verifica que el cliente pueda consultar su reserva introduciendo su código.
        """
        reserva = Reserva.objects.create(
            producto=self.producto,
            cantidad=1,
            precio_unitario=Decimal("2000.00"),
            precio_total=Decimal("2000.00"),
            monto_anticipo=Decimal("400.00"),
            saldo_en_tienda=Decimal("1600.00"),
            nombre_cliente="Laura Rojas",
            email_cliente="laura@test.com",
            telefono_cliente="+57 312 000 1122",
            documento_identidad="CC 55566677",
            estado=Reserva.ESTADO_PENDIENTE_PAGO
        )

        response = self.client.get(reverse('reservas:consultar'), {'codigo': reserva.codigo})
        self.assertRedirects(response, reverse('reservas:resumen', kwargs={'codigo': reserva.codigo}))

    # --- PRUEBAS HU 3: SUBIDA DE COMPROBANTE Y CAMBIO DE ESTADO ---

    def test_subir_comprobante_jpg_pasa_a_comprobante_en_revision(self):
        """
        Criterio HU 3: 'Permite adjuntar JPG/PNG/PDF. Pasa a Comprobante en Revisión.'
        Prueba con archivo JPG.
        """
        reserva = Reserva.objects.create(
            producto=self.producto,
            cantidad=1,
            precio_unitario=Decimal("2000.00"),
            precio_total=Decimal("2000.00"),
            monto_anticipo=Decimal("400.00"),
            saldo_en_tienda=Decimal("1600.00"),
            nombre_cliente="Cliente JPG",
            email_cliente="jpg@test.com",
            telefono_cliente="123456",
            documento_identidad="CC 111111",
            estado=Reserva.ESTADO_PENDIENTE_PAGO
        )

        archivo_jpg = SimpleUploadedFile(
            "recibo_pago.jpg",
            b"\xff\xd8\xff\xe0\x00\x10JFIFfakejpgdata",
            content_type="image/jpeg"
        )

        response = self.client.post(
            reverse('reservas:subir_comprobante', kwargs={'codigo': reserva.codigo}),
            data={
                'comprobante': archivo_jpg,
                'banco_origen': 'Banco Pichincha',
                'numero_transaccion': 'TRX-998877'
            }
        )

        self.assertRedirects(response, reverse('reservas:resumen', kwargs={'codigo': reserva.codigo}))

        reserva.refresh_from_db()
        # Condición: Pasa a Comprobante en Revisión
        self.assertEqual(reserva.estado, Reserva.ESTADO_COMPROBANTE_REVISION)
        self.assertEqual(reserva.get_estado_display(), 'Comprobante en Revisión')
        self.assertTrue(bool(reserva.comprobante))
        self.assertTrue(reserva.es_imagen_comprobante)
        self.assertEqual(reserva.banco_origen, 'Banco Pichincha')
        self.assertEqual(reserva.numero_transaccion, 'TRX-998877')
        self.assertIsNotNone(reserva.fecha_subida_comprobante)

    def test_subir_comprobante_png_pasa_a_comprobante_en_revision(self):
        """
        Criterio HU 3: Permite adjuntar PNG y pasa a Comprobante en Revisión.
        """
        reserva = Reserva.objects.create(
            producto=self.producto,
            cantidad=1,
            precio_unitario=Decimal("2000.00"),
            precio_total=Decimal("2000.00"),
            monto_anticipo=Decimal("400.00"),
            saldo_en_tienda=Decimal("1600.00"),
            nombre_cliente="Cliente PNG",
            email_cliente="png@test.com",
            telefono_cliente="222222",
            documento_identidad="CC 222222",
            estado=Reserva.ESTADO_PENDIENTE_PAGO
        )

        archivo_png = SimpleUploadedFile(
            "transferencia.png",
            b"\x89PNG\r\n\x1a\nfakepngdata",
            content_type="image/png"
        )

        response = self.client.post(
            reverse('reservas:subir_comprobante', kwargs={'codigo': reserva.codigo}),
            data={'comprobante': archivo_png}
        )
        self.assertRedirects(response, reverse('reservas:resumen', kwargs={'codigo': reserva.codigo}))

        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, Reserva.ESTADO_COMPROBANTE_REVISION)
        self.assertEqual(reserva.get_estado_display(), 'Comprobante en Revisión')
        self.assertTrue(reserva.es_imagen_comprobante)

    def test_subir_comprobante_pdf_pasa_a_comprobante_en_revision(self):
        """
        Criterio HU 3: Permite adjuntar PDF y pasa a Comprobante en Revisión.
        """
        reserva = Reserva.objects.create(
            producto=self.producto,
            cantidad=1,
            precio_unitario=Decimal("2000.00"),
            precio_total=Decimal("2000.00"),
            monto_anticipo=Decimal("400.00"),
            saldo_en_tienda=Decimal("1600.00"),
            nombre_cliente="Cliente PDF",
            email_cliente="pdf@test.com",
            telefono_cliente="333333",
            documento_identidad="CC 333333",
            estado=Reserva.ESTADO_PENDIENTE_PAGO
        )

        archivo_pdf = SimpleUploadedFile(
            "comprobante_bancario.pdf",
            b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>%%EOF",
            content_type="application/pdf"
        )

        response = self.client.post(
            reverse('reservas:subir_comprobante', kwargs={'codigo': reserva.codigo}),
            data={'comprobante': archivo_pdf}
        )
        self.assertRedirects(response, reverse('reservas:resumen', kwargs={'codigo': reserva.codigo}))

        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, Reserva.ESTADO_COMPROBANTE_REVISION)
        self.assertEqual(reserva.get_estado_display(), 'Comprobante en Revisión')
        self.assertTrue(reserva.es_pdf_comprobante)

    def test_subir_comprobante_formato_no_permitido_rechazado(self):
        """
        Verifica que solo se permitan formatos JPG, PNG o PDF.
        Archivos como .exe, .txt o .zip deben ser rechazados.
        """
        reserva = Reserva.objects.create(
            producto=self.producto,
            cantidad=1,
            precio_unitario=Decimal("2000.00"),
            precio_total=Decimal("2000.00"),
            monto_anticipo=Decimal("400.00"),
            saldo_en_tienda=Decimal("1600.00"),
            nombre_cliente="Cliente Invalido",
            email_cliente="invalido@test.com",
            telefono_cliente="444444",
            documento_identidad="CC 444444",
            estado=Reserva.ESTADO_PENDIENTE_PAGO
        )

        archivo_invalido = SimpleUploadedFile(
            "archivo_malicioso.exe",
            b"fake exe executable payload",
            content_type="application/octet-stream"
        )

        response = self.client.post(
            reverse('reservas:subir_comprobante', kwargs={'codigo': reserva.codigo}),
            data={'comprobante': archivo_invalido}
        )

        # No debe redirigir al resumen exitoso, sino renderizar el formulario con error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Solo se aceptan archivos JPG, JPEG, PNG o PDF")

        reserva.refresh_from_db()
        # Debe mantenerse en Pendiente de Pago
        self.assertEqual(reserva.estado, Reserva.ESTADO_PENDIENTE_PAGO)
        self.assertFalse(bool(reserva.comprobante))

    def test_vista_resumen_refleja_comprobante_en_revision(self):
        """
        Verifica que la página de resumen muestre el estado 'Comprobante en Revisión'
        y el enlace o vista previa del archivo cargado.
        """
        archivo_jpg = SimpleUploadedFile(
            "recibo.jpg",
            b"\xff\xd8\xff\xe0\x00\x10JFIFfakejpgdata",
            content_type="image/jpeg"
        )

        reserva = Reserva.objects.create(
            producto=self.producto,
            cantidad=1,
            precio_unitario=Decimal("2000.00"),
            precio_total=Decimal("2000.00"),
            monto_anticipo=Decimal("400.00"),
            saldo_en_tienda=Decimal("1600.00"),
            nombre_cliente="Cliente Verificado",
            email_cliente="verificado@test.com",
            telefono_cliente="555555",
            documento_identidad="CC 555555",
            estado=Reserva.ESTADO_COMPROBANTE_REVISION,
            comprobante=archivo_jpg,
            banco_origen="Bancolombia",
            numero_transaccion="REF-12345"
        )

        response = self.client.get(reverse('reservas:resumen', kwargs={'codigo': reserva.codigo}))
        self.assertEqual(response.status_code, 200)

        # Debe mostrar el nuevo estado
        self.assertContains(response, "Comprobante en Revisión")
        self.assertContains(response, "Bancolombia")
        self.assertContains(response, "REF-12345")
        self.assertContains(response, "Ver Imagen Completa")
