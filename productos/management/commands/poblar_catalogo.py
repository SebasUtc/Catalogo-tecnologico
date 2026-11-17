import os
import shutil
from decimal import Decimal
from django.conf import settings
from django.core.management.base import BaseCommand
from productos.models import Categoria, Marca, Producto
from reservas.models import CuentaBancaria


class Command(BaseCommand):
    help = "Puebla la base de datos con categorías, marcas, cuentas bancarias y productos con fotos 100% locales"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Iniciando carga de datos de prueba para el Catálogo Tecnológico..."))

        # 1. Asegurar directorios de imágenes locales
        media_productos_dir = os.path.join(settings.MEDIA_ROOT, 'productos')
        static_productos_dir = os.path.join(settings.BASE_DIR, 'static', 'img', 'productos')
        os.makedirs(media_productos_dir, exist_ok=True)

        # 2. Categorías
        categorias_data = [
            {"nombre": "Laptops & Portátiles", "slug": "laptops", "icono": "bi-laptop", "descripcion": "Laptops gamer, ultrabooks y estaciones de trabajo portátiles."},
            {"nombre": "Smartphones & Móviles", "slug": "smartphones", "icono": "bi-phone", "descripcion": "Smartphones de alta gama, cámaras avanzadas y conectividad 5G."},
            {"nombre": "Consolas & Gaming", "slug": "gaming", "icono": "bi-controller", "descripcion": "Consolas de última generación y accesorios gaming."},
            {"nombre": "Tablets & iPads", "slug": "tablets", "icono": "bi-tablet", "descripcion": "Tablets para diseño, productividad y entretenimiento."},
            {"nombre": "Audio & Periféricos", "slug": "audio-perifericos", "icono": "bi-headphones", "descripcion": "Auriculares pro, teclados mecánicos y periféricos de precisión."},
            {"nombre": "Monitores & Pantallas", "slug": "monitores", "icono": "bi-display", "descripcion": "Monitores gamer de alta tasa de refresco y pantallas 4K para creadores."},
        ]

        categorias_map = {}
        for c in categorias_data:
            obj, _ = Categoria.objects.update_or_create(
                slug=c["slug"],
                defaults={
                    "nombre": c["nombre"],
                    "icono": c["icono"],
                    "descripcion": c["descripcion"],
                    "activo": True
                }
            )
            categorias_map[c["slug"]] = obj
        self.stdout.write(self.style.SUCCESS(f"✓ {len(categorias_map)} Categorías creadas/actualizadas"))

        # 3. Marcas
        marcas_data = [
            {"nombre": "Apple", "slug": "apple", "descripcion": "Ecosistema premium iOS y macOS."},
            {"nombre": "ASUS ROG", "slug": "asus-rog", "descripcion": "Línea gamer de alto rendimiento Republic of Gamers."},
            {"nombre": "Sony", "slug": "sony", "descripcion": "PlayStation, audio de estudio y fotografía."},
            {"nombre": "Samsung", "slug": "samsung", "descripcion": "Líder en pantallas Dynamic AMOLED y telefonía Galaxy."},
            {"nombre": "Lenovo", "slug": "lenovo", "descripcion": "Línea Legion y ThinkPad de alta durabilidad."},
            {"nombre": "Logitech G", "slug": "logitech-g", "descripcion": "Periféricos profesionales para eSports."},
        ]

        marcas_map = {}
        for m in marcas_data:
            obj, _ = Marca.objects.update_or_create(
                slug=m["slug"],
                defaults={
                    "nombre": m["nombre"],
                    "descripcion": m["descripcion"],
                    "activo": True
                }
            )
            marcas_map[m["slug"]] = obj
        self.stdout.write(self.style.SUCCESS(f"✓ {len(marcas_map)} Marcas creadas/actualizadas"))

        # 4. Productos con fotos locales, SKU, ficha técnica estructurada, precio y anticipo
        productos_data = [
            {
                "sku": "LAP-ASUS-G16-4070",
                "nombre": "Laptop ASUS ROG Zephyrus G16 (2024) RTX 4070",
                "slug": "asus-rog-zephyrus-g16-2024",
                "categoria": categorias_map["laptops"],
                "marca": marcas_map["asus-rog"],
                "descripcion_corta": "Laptop ultra delgada para gaming y creación con pantalla OLED 240Hz y gráfica RTX 4070.",
                "ficha_tecnica": (
                    "Procesador: Intel Core Ultra 9 185H (16 núcleos / 22 hilos)\n"
                    "Gráfica: NVIDIA GeForce RTX 4070 8GB GDDR6\n"
                    "Memoria RAM: 32 GB LPDDR5X 7467MHz\n"
                    "Almacenamiento: 1 TB SSD PCIe 4.0 NVMe M.2\n"
                    "Pantalla: 16 pulgadas ROG Nebula Display OLED 2.5K (2560x1600) 240Hz 0.2ms\n"
                    "Batería: 90Wh con carga rápida Type-C de 100W\n"
                    "Peso: 1.85 kg con chasis de aluminio mecanizado CNC\n"
                    "Sistema Operativo: Windows 11 Home en Español\n"
                    "Garantía: 1 Año oficial ASUS International"
                ),
                "precio": Decimal("2199.00"),
                "porcentaje_anticipo": Decimal("20.00"),
                "stock_disponible": 4,
                "destacado": True,
                "imagen": "productos/LAP-ASUS-G16-4070.jpg",
                "imagen_url": None,
            },
            {
                "sku": "LAP-MBP-14-M3P",
                "nombre": "Apple MacBook Pro 14 pulgadas Chip M3 Pro",
                "slug": "apple-macbook-pro-14-m3-pro",
                "categoria": categorias_map["laptops"],
                "marca": marcas_map["apple"],
                "descripcion_corta": "Potencia profesional con el chip M3 Pro, pantalla Liquid Retina XDR y hasta 18 horas de batería.",
                "ficha_tecnica": (
                    "Chip: Apple M3 Pro (CPU 12 núcleos, GPU 18 núcleos)\n"
                    "Memoria Unificada: 18 GB\n"
                    "Almacenamiento: 512 GB SSD ultra veloz\n"
                    "Pantalla: Liquid Retina XDR de 14.2 pulgadas con ProMotion 120Hz\n"
                    "Brillo: 1,000 nits sostenidos, pico de 1,600 nits en HDR\n"
                    "Puertos: 3x Thunderbolt 4, HDMI, ranura SDXC, MagSafe 3\n"
                    "Batería: Hasta 18 horas de reproducción continua\n"
                    "Acabado: Negro Espacial (Space Black)\n"
                    "Garantía: 1 Año Apple Care"
                ),
                "precio": Decimal("2399.00"),
                "porcentaje_anticipo": Decimal("25.00"),
                "stock_disponible": 6,
                "destacado": True,
                "imagen": "productos/LAP-MBP-14-M3P.jpg",
                "imagen_url": None,
            },
            {
                "sku": "PHN-IP15-PM-256",
                "nombre": "iPhone 15 Pro Max 256GB Titanio Natural",
                "slug": "iphone-15-pro-max-256gb-titanio",
                "categoria": categorias_map["smartphones"],
                "marca": marcas_map["apple"],
                "descripcion_corta": "Diseño en titanio de grado aeroespacial, chip A17 Pro revolucionario y cámara telefoto 5x.",
                "ficha_tecnica": (
                    "Procesador: Apple A17 Pro de 3nm con trazado de rayos por hardware\n"
                    "Capacidad: 256 GB NVMe\n"
                    "Pantalla: Super Retina XDR OLED de 6.7 pulgadas con ProMotion y Always-On\n"
                    "Cámara Principal: 48 MP f/1.78 con estabilización por desplazamiento de sensor\n"
                    "Telefoto: 12 MP con zoom óptico 5x (120 mm)\n"
                    "Conector: USB-C con velocidades USB 3 (hasta 10 Gb/s)\n"
                    "Material: Titanio Grado 5 con vidrio mate texturizado\n"
                    "Resistencia: Certificación IP68 (hasta 6 metros durante 30 min)\n"
                    "Garantía: 1 Año oficial Apple"
                ),
                "precio": Decimal("1399.00"),
                "porcentaje_anticipo": Decimal("20.00"),
                "stock_disponible": 8,
                "destacado": True,
                "imagen": "productos/PHN-IP15-PM-256.jpg",
                "imagen_url": None,
            },
            {
                "sku": "PHN-S24-ULTRA-512",
                "nombre": "Samsung Galaxy S24 Ultra 512GB Titanium Gray",
                "slug": "samsung-galaxy-s24-ultra-512gb",
                "categoria": categorias_map["smartphones"],
                "marca": marcas_map["samsung"],
                "descripcion_corta": "Con Galaxy AI integrada, S-Pen incorporado y la cámara de 200MP más avanzada del mercado.",
                "ficha_tecnica": (
                    "Procesador: Qualcomm Snapdragon 8 Gen 3 for Galaxy\n"
                    "Memoria RAM: 12 GB LPDDR5X\n"
                    "Almacenamiento: 512 GB UFS 4.0\n"
                    "Pantalla: Dynamic AMOLED 2X de 6.8 pulgadas QHD+ 120Hz con Corning Gorilla Armor\n"
                    "Cámara Cuádruple: 200 MP Principal + 50 MP Periscopio 5x + 10 MP 3x + 12 MP Gran Angular\n"
                    "Batería: 5,000 mAh con carga de 45W\n"
                    "Accesorios: S-Pen integrado con baja latencia\n"
                    "Inteligencia Artificial: Galaxy AI con Circle to Search y Live Translate"
                ),
                "precio": Decimal("1450.00"),
                "porcentaje_anticipo": Decimal("15.00"),
                "stock_disponible": 5,
                "destacado": False,
                "imagen": "productos/PHN-S24-ULTRA-512.jpg",
                "imagen_url": None,
            },
            {
                "sku": "CNS-PS5-SLIM-1TB",
                "nombre": "Consola Sony PlayStation 5 Slim 1TB con Lector",
                "slug": "sony-playstation-5-slim-1tb",
                "categoria": categorias_map["gaming"],
                "marca": marcas_map["sony"],
                "descripcion_corta": "Nuevo diseño estilizado, 1TB de almacenamiento ultra rápido y mando DualSense con retroalimentación háptica.",
                "ficha_tecnica": (
                    "Procesador: AMD Zen 2 de 8 núcleos a 3.5 GHz\n"
                    "GPU: Motor gráfico AMD Radeon RDNA 2 con Ray Tracing\n"
                    "Memoria: 16 GB GDDR6 / 448 GB/s\n"
                    "Almacenamiento: 1 TB SSD integrado (5.5 GB/s de velocidad de lectura)\n"
                    "Resolución: Salida 4K a 120Hz y soporte 8K con HDR\n"
                    "Unidad Óptica: Reproductor Ultra HD Blu-ray 4K\n"
                    "Audio: Tempest 3D AudioTech para inmersión espacial\n"
                    "Control: Mando inalámbrico DualSense incluido"
                ),
                "precio": Decimal("549.00"),
                "porcentaje_anticipo": Decimal("20.00"),
                "stock_disponible": 10,
                "destacado": True,
                "imagen": "productos/CNS-PS5-SLIM-1TB.jpg",
                "imagen_url": None,
            },
            {
                "sku": "AUD-SONY-WH1000XM5",
                "nombre": "Sony WH-1000XM5 Auriculares Inalámbricos Noise Cancelling",
                "slug": "sony-wh-1000xm5-auriculares-noise-cancelling",
                "categoria": categorias_map["audio-perifericos"],
                "marca": marcas_map["sony"],
                "descripcion_corta": "Líderes en cancelación de ruido activa con procesador V1, audio Hi-Res y 30 horas de autonomía.",
                "ficha_tecnica": (
                    "Cancelación de Ruido: Procesador HD QN1 y Procesador Integrado V1 con 8 micrófonos\n"
                    "Drivers: Unidad de diafragma de 30 mm diseñada con fibra de carbono\n"
                    "Formatos Soportados: LDAC, AAC, SBC (Hi-Res Audio Wireless certificado)\n"
                    "Conectividad: Bluetooth 5.2 con conexión multipunto simultánea\n"
                    "Batería: 30 horas con ANC encendido, carga rápida (3 min = 3 horas)\n"
                    "Llamadas: 4 micrófonos con formación de haces y reducción de viento por IA\n"
                    "Peso: 250 g con almohadillas de cuero sintético suave"
                ),
                "precio": Decimal("399.00"),
                "porcentaje_anticipo": Decimal("20.00"),
                "stock_disponible": 12,
                "destacado": False,
                "imagen": "productos/AUD-SONY-WH1000XM5.jpg",
                "imagen_url": None,
            },
            {
                "sku": "TAB-IPA-AIR-M2",
                "nombre": "iPad Air de 11 pulgadas Chip M2 128GB Wi-Fi",
                "slug": "apple-ipad-air-11-chip-m2-128gb",
                "categoria": categorias_map["tablets"],
                "marca": marcas_map["apple"],
                "descripcion_corta": "Rendimiento veloz con chip M2, pantalla Liquid Retina antirreflejo y compatibilidad con Apple Pencil Pro.",
                "ficha_tecnica": (
                    "Procesador: Apple M2 (CPU 8 núcleos, GPU 9 núcleos, Neural Engine 16 núcleos)\n"
                    "Capacidad: 128 GB\n"
                    "Pantalla: Liquid Retina de 11 pulgadas con tecnología True Tone y gama de colores P3\n"
                    "Cámara Frontal: Ultra gran angular de 12 MP en el borde horizontal con Encuadre Centrado\n"
                    "Cámara Trasera: Gran angular de 12 MP con grabación en 4K\n"
                    "Conectividad: Wi-Fi 6E ultra rápido y Bluetooth 5.3\n"
                    "Compatibilidad: Apple Pencil Pro y Magic Keyboard"
                ),
                "precio": Decimal("649.00"),
                "porcentaje_anticipo": Decimal("20.00"),
                "stock_disponible": 7,
                "destacado": False,
                "imagen": "productos/TAB-IPA-AIR-M2.jpg",
                "imagen_url": None,
            },
            {
                "sku": "PER-LOG-GPRO-X2",
                "nombre": "Mouse Gamer Logitech G Pro X Superlight 2",
                "slug": "mouse-logitech-g-pro-x-superlight-2",
                "categoria": categorias_map["audio-perifericos"],
                "marca": marcas_map["logitech-g"],
                "descripcion_corta": "Mouse profesional para eSports de solo 60 gramos con sensor HERO 2 de 32,000 DPI y switches LIGHTFORCE.",
                "ficha_tecnica": (
                    "Sensor: HERO 2 de última generación (100 a 32,000 DPI, >500 IPS)\n"
                    "Switches: Híbridos óptico-mecánicos LIGHTFORCE de latencia ultra baja\n"
                    "Tasa de Sondeo: 2,000 Hz / 4,000 Hz vía LIGHTSPEED Wireless\n"
                    "Peso: 60 gramos sin orificios en chasis\n"
                    "Batería: Hasta 95 horas de movimiento constante con puerto USB-C\n"
                    "Patines: 100% PTFE sin aditivos de deslizamiento fluido"
                ),
                "precio": Decimal("159.00"),
                "porcentaje_anticipo": Decimal("20.00"),
                "stock_disponible": 15,
                "destacado": False,
                "imagen": "productos/PER-LOG-GPRO-X2.jpg",
                "imagen_url": None,
            },
            {
                "sku": "LAP-LEN-LEG-PRO7",
                "nombre": "Lenovo Legion Pro 7i Gen 8 Core i9 RTX 4080",
                "slug": "lenovo-legion-pro-7i-gen-8-rtx-4080",
                "categoria": categorias_map["laptops"],
                "marca": marcas_map["lenovo"],
                "descripcion_corta": "Laptop gaming de máxima potencia con sistema de refrigeración de cámara de vapor y chip Lenovo LA-2 AI.",
                "ficha_tecnica": (
                    "Procesador: Intel Core i9-13900HX (24 núcleos / 32 hilos hasta 5.4 GHz)\n"
                    "Tarjeta de Video: NVIDIA GeForce RTX 4080 12GB GDDR6 (TGP 175W)\n"
                    "Memoria: 32 GB DDR5 5600MHz en doble canal\n"
                    "Almacenamiento: 1 TB SSD M.2 2280 PCIe Gen4\n"
                    "Pantalla: 16 pulgadas WQXGA (2560 x 1600) IPS 240Hz 500 nits 100% sRGB\n"
                    "Refrigeración: Coldfront 5.0 con cámara de vapor y metal líquido\n"
                    "Teclado: Legion TrueStrike con iluminación RGB por tecla"
                ),
                "precio": Decimal("2699.00"),
                "porcentaje_anticipo": Decimal("20.00"),
                "stock_disponible": 3,
                "destacado": True,
                "imagen": "productos/LAP-LEN-LEG-PRO7.jpg",
                "imagen_url": None,
            },
        ]

        for prod_data in productos_data:
            sku = prod_data["sku"]
            img_filename = f"{sku}.jpg"
            src_static = os.path.join(static_productos_dir, img_filename)
            dest_media = os.path.join(media_productos_dir, img_filename)

            # Si el archivo está en static y no en media, copiarlo localmente
            if os.path.exists(src_static) and not os.path.exists(dest_media):
                shutil.copy2(src_static, dest_media)

            obj, created = Producto.objects.update_or_create(
                sku=prod_data["sku"],
                defaults=prod_data
            )
            accion = "Creado" if created else "Actualizado"
            foto_origen = obj.url_foto or "Sin foto"
            self.stdout.write(f"  • [{obj.sku}] {obj.nombre} ({accion}) - Foto Local: {foto_origen}")

        # 5. Cuentas Bancarias de la Tienda
        cuentas_data = [
            {
                "banco": "Banco Nacional / Central",
                "tipo_cuenta": "Cuenta Corriente Empresarial",
                "numero_cuenta": "100-245896-01",
                "titular": "Centro de Ventas Tecnológicas S.A.S.",
                "documento_titular": "NIT: 900.584.210-3",
                "correo_notificacion": "pagos@tecnoreserva.com",
                "instrucciones": "Indicar tu Código de Reserva en la descripción o concepto de la transferencia.",
                "orden": 1,
            },
            {
                "banco": "Banco Digital Tech",
                "tipo_cuenta": "Cuenta de Ahorros",
                "numero_cuenta": "452-987412-88",
                "titular": "Centro de Ventas Tecnológicas S.A.S.",
                "documento_titular": "NIT: 900.584.210-3",
                "correo_notificacion": "pagos@tecnoreserva.com",
                "instrucciones": "Transferencia inmediata sin comisión.",
                "orden": 2,
            },
            {
                "banco": "Billetera Digital / Transferencia Móvil",
                "tipo_cuenta": "Pago Rápido / QR",
                "numero_cuenta": "+57 300 987 6543",
                "titular": "Centro de Ventas Tecnológicas",
                "documento_titular": "NIT: 900.584.210-3",
                "correo_notificacion": "pagos@tecnoreserva.com",
                "instrucciones": "Disponible 24/7. Envía el comprobante con tu código de reserva.",
                "orden": 3,
            },
        ]

        for c_data in cuentas_data:
            c_obj, _ = CuentaBancaria.objects.update_or_create(
                numero_cuenta=c_data["numero_cuenta"],
                defaults=c_data
            )
            self.stdout.write(f"  • Cuenta habilitada: {c_obj.banco} ({c_obj.numero_cuenta})")

        self.stdout.write(self.style.SUCCESS(f"\n¡Éxito! Se han cargado {len(productos_data)} productos con imágenes 100% locales y {len(cuentas_data)} cuentas bancarias."))
