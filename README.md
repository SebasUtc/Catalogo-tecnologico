# Sistema de Gestión de Pedidos y Reservas
### *Reservas por adelantado para un Centro de Ventas Tecnológicas*

Este sistema permite a los clientes explorar un catálogo especializado de productos tecnológicos, evaluar las especificaciones técnicas y el **anticipo mínimo requerido** para reservar un producto. En lugar de procesar pagos directos en línea con pasarelas tradicionales, el cliente genera una solicitud de reserva respaldada por un comprobante de anticipo (transferencia/depósito), el cual es verificado por un vendedor en la tienda física para asegurar el producto y permitir que el saldo restante sea cancelado personalmente al momento del retiro.

---

## 🏃 Metodología de Desarrollo: Marco Scrum

El desarrollo se organiza en Sprints iterativos e incrementales:

- **Sprint 1 (En curso - Historias de Usuario completadas):**
  - **HU 1:** Catálogo de productos, ficha técnica, precios, cálculo de anticipos y filtros por marca y categoría.
  - **HU 2:** Solicitud de reserva para apartar cupo en el lote: cálculo de anticipo según cantidad, visualización de cuentas bancarias de la tienda y creación de la reserva en estado **Pendiente de Pago**.
- **Sprint 2 (Próximo):** Carga y validación del comprobante de transferencia bancaria por parte del cliente y confirmación de apartado por el vendedor.
- **Sprint 3:** Panel del vendedor para gestión de lotes y validación de comprobantes.
- **Sprint 4:** Liquidación de saldo restante y entrega física del equipo en tienda.

---

## 🎯 Sprint 1: Historias de Usuario Desarrolladas

### 📌 Historia de Usuario 1 (HU 1)
> *"Como cliente, quiero ver productos y anticipos para evaluar mi reserva."*
> - **Criterios de Aceptación:** Muestra foto, SKU, ficha técnica, precio y anticipo. Filtra por marca y por categoría.

### 📌 Historia de Usuario 2 (HU 2)
> *"Como cliente, quiero solicitar una reserva para apartar cupo en el lote."*
> - **Criterios de Aceptación Cumplidos:**
>   - [x] **Calcula anticipo:** Multiplica el anticipo unitario por la cantidad solicitada con recálculo dinámico e interactivo en tiempo real y validación en servidor.
>   - [x] **Muestra cuentas:** Presenta las cuentas bancarias autorizadas de la tienda (banco, tipo, número de cuenta con botón para copiar, titular, documento e instrucciones de pago).
>   - [x] **Crea reserva en "Pendiente de Pago":** Asigna automáticamente el código único (ej. `RES-2026-X8K29`), aparta provisionalmente el cupo del lote (descontando del inventario disponible) y registra el estado inicial `PENDIENTE_PAGO`.

---

## 🏗️ Estructura del Proyecto

```text
Catalogo tecnologico/
├── gestion_reservas/        # Configuración principal del proyecto Django
│   ├── settings.py          # Configuración de apps, media, static y localización
│   ├── urls.py              # Enrutador principal (productos + reservas + media)
│   └── wsgi.py
├── productos/               # App de catálogo de productos
│   ├── models.py            # Modelos: Categoria, Marca, Producto
│   ├── views.py             # Catálogo y detalle de producto
│   ├── urls.py
│   ├── admin.py             # Admin del catálogo
│   ├── tests.py             # Pruebas de HU 1
│   ├── templatetags/        # Filtros de formato moneda ($1,500.00)
│   └── management/commands/
│       └── poblar_catalogo.py # Carga productos, marcas y cuentas bancarias
├── reservas/                # App de gestión de reservas y cupos (HU 2)
│   ├── models.py            # Modelos: CuentaBancaria, Reserva (estado PENDIENTE_PAGO)
│   ├── forms.py             # SolicitudReservaForm (validación de stock/cupo)
│   ├── views.py             # solicitar_reserva_view, resumen_reserva_view, consultar_reserva_view
│   ├── urls.py              # Rutas de solicitud y consulta de reserva
│   ├── admin.py             # Panel de control de reservas y cuentas bancarias
│   └── tests.py             # Pruebas de HU 2 (cálculo de anticipo, cuentas, PENDIENTE_PAGO)
├── templates/
│   ├── base.html            # Layout maestro con mensajes, navbar y consulta de reserva
│   ├── productos/
│   │   ├── catalogo.html    # Grilla de productos, sidebar y filtros
│   │   └── detalle.html     # Ficha técnica y botón de solicitud de reserva
│   └── reservas/
│       ├── solicitar.html   # Formulario con cálculo de anticipo en vivo y cuentas
│       ├── resumen.html     # Resumen de reserva en estado Pendiente de Pago
│       └── consultar.html   # Búsqueda de reserva por código
├── static/
│   └── css/
│       └── estilos.css      # Estilos tecnológicos responsivos
├── requirements.txt
├── manage.py
└── README.md
```

---

## 🚀 Guía de Puesta en Marcha

### 1. Activar el Entorno Virtual
```bash
source venv/bin/activate
```

### 2. Instalar Dependencias (si es necesario)
```bash
pip install -r requirements.txt
```

### 3. Aplicar Migraciones
```bash
python manage.py migrate
```

### 4. Cargar Datos de Prueba (Seed Data)
El comando crea 6 categorías, 6 marcas y 9 productos tecnológicos de alta gama con fichas técnicas y fotos:
```bash
python manage.py poblar_catalogo
```

### 5. Ejecutar la Suite de Pruebas Automatizadas
```bash
python manage.py test
```

### 6. Iniciar el Servidor de Desarrollo
```bash
python manage.py runserver
```

Abre tu navegador en:
- **Catálogo Web para Clientes:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Panel Administrativo (Vendedores/Admin):** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
  - **Usuario:** `admin`
  - **Contraseña:** `admin1234`
