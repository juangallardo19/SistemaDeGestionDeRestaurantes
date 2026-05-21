# Sistema de Gestión de Restaurante

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.2-092E20?style=flat&logo=django&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat&logo=sqlite&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=flat&logo=bootstrap&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat)

Aplicación web para la gestión integral de un restaurante: menú, pedidos, reservas, inventario y reportes, con tres roles diferenciados (cliente, mesero y administrador).

---

## Descripción general

RestaurApp es un sistema de gestión de restaurante desarrollado con Django que centraliza las operaciones diarias del negocio en una sola plataforma. El sistema implementa tres roles con distintos niveles de acceso: el **cliente** puede explorar el menú, agregar platos al carrito, confirmar pedidos con pago simulado, realizar reservas de mesas y consultar su historial de compras. El **mesero** accede a la lista de pedidos activos, puede cambiar su estado a lo largo del flujo de preparación y gestionar las reservas del día. El **administrador** tiene acceso completo al sistema: además de todas las funciones anteriores, dispone de un panel con KPIs diarios, gráficos estadísticos, gestión de inventario con descuento automático de stock, administración de usuarios, y exportación de reportes en PDF y Excel filtrados por fecha.

---

## Tecnologías utilizadas

| Tecnología | Versión | Uso en el proyecto |
|---|---|---|
| Django | 4.2 | Framework principal, MVT, ORM, autenticación |
| Python | 3.10+ | Lenguaje base del backend |
| SQLite | 3 | Base de datos local de desarrollo |
| Bootstrap | 5.3 | Estilos, grilla responsive y componentes UI |
| Chart.js | 4.x | Gráficos de ventas y platos más pedidos en el dashboard |
| ReportLab | 4.x | Generación de reportes en PDF |
| openpyxl | 3.x | Exportación de datos a Excel (.xlsx) |
| pandas | 2.x | Procesamiento de datos para reportes y estadísticas |
| Pillow | 10.x | Manejo y redimensionado de imágenes (platos, perfil) |
| django-crispy-forms | 2.x | Renderizado de formularios con estilos Bootstrap |

---

## Estructura del proyecto

El proyecto sigue la arquitectura **MVT (Model – View – Template)** de Django. Cada módulo de negocio es una app independiente con sus propios modelos, vistas y URLs. Las plantillas HTML se centralizan en la carpeta `templates/` en la raíz del proyecto y heredan de un `base.html` común.

```
SistemaDeGestionDeRestaurantes/
│
├── restaurante/                # Configuración del proyecto
│   ├── settings/
│   │   ├── base.py             # Configuración compartida
│   │   ├── development.py      # Configuración local (SQLite, debug)
│   │   └── production.py       # Configuración de producción
│   ├── urls.py                 # URLs raíz
│   └── wsgi.py
│
├── accounts/                   # Autenticación, usuarios y roles
├── menu/                       # Platos, categorías e ingredientes
├── orders/                     # Pedidos, carrito de compras y pagos simulados
├── reservations/               # Reservas de mesas
├── inventory/                  # Control de stock de cocina
├── dashboard/                  # Panel administrativo, gráficos y reportes
│
├── templates/                  # Plantillas HTML del proyecto
├── static/                     # CSS, JS e imágenes estáticas
├── media/                      # Archivos subidos por los usuarios
├── fixtures/                   # Datos de prueba (JSON)
│
├── manage.py
├── requirements.txt
└── .env.example
```

### Apps del proyecto

| App | Responsabilidad |
|---|---|
| `accounts` | Modelo de usuario personalizado, autenticación, roles y perfiles |
| `menu` | CRUD de platos, categorías, ingredientes y recetas (PlatoIngrediente) |
| `orders` | Carrito de sesión, creación de pedidos, estados y descuento de stock |
| `reservations` | Reservas de mesas con validación de disponibilidad y conflictos |
| `inventory` | Movimientos de stock, alertas de stock bajo y gestión de recetas |
| `dashboard` | KPIs diarios, gráficos con Chart.js y exportaciones PDF/Excel |

---

## Modelos principales

| Modelo | App | Campos principales | Relaciones |
|---|---|---|---|
| `CustomUser` | accounts | username, email, role (cliente / mesero / admin), phone, profile_picture | Extiende `AbstractUser` |
| `Categoria` | menu | nombre, descripcion, imagen, activo | — |
| `Ingrediente` | menu | nombre, unidad_medida, stock_actual, stock_minimo, activo | — |
| `Plato` | menu | nombre, descripcion, precio, imagen, disponible, tiempo_preparacion | FK → Categoria; M2M → Ingrediente a través de PlatoIngrediente |
| `PlatoIngrediente` | menu | cantidad_necesaria | FK → Plato; FK → Ingrediente |
| `Mesa` | reservations | numero, capacidad, ubicacion, activa | — |
| `Reserva` | reservations | fecha, hora_inicio, hora_fin, numero_personas, estado, notas | FK → CustomUser (cliente); FK → Mesa |
| `Pedido` | orders | estado, total, metodo_pago, notas | FK → CustomUser (cliente); FK → CustomUser (mesero); FK → Mesa |
| `DetallePedido` | orders | cantidad, precio_unitario | FK → Pedido; FK → Plato |
| `MovimientoInventario` | inventory | tipo, cantidad, fecha, motivo, stock_resultante | FK → Ingrediente; FK → CustomUser (responsable) |

---

## Requisitos previos

Antes de instalar el proyecto asegurate de tener:

- **Python 3.10** o superior
- **pip** (viene incluido con Python)
- **Git**
- Un editor de código — se recomienda **VS Code**

---

## Instalación y configuración local

### Paso 1 — Clonar el repositorio

```bash
git clone https://github.com/juangallardo19/SistemaDeGestionDeRestaurantes.git
cd SistemaDeGestionDeRestaurantes
```

### Paso 2 — Crear y activar el entorno virtual

```bash
# Crear el entorno virtual
python -m venv venv

# Activar en Windows
venv\Scripts\activate

# Activar en Mac / Linux
source venv/bin/activate
```

> El prompt de la terminal cambia a `(venv)` cuando el entorno está activo.

### Paso 3 — Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 4 — Configurar las variables de entorno

```bash
# Copiar el archivo de ejemplo
cp .env.example .env
```

Abrir el archivo `.env` y completar con los siguientes valores para desarrollo local:

```
SECRET_KEY=clave-local-desarrollo-no-importa-cual
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_SETTINGS_MODULE=restaurante.settings.development
```

> En desarrollo local no es necesario configurar email ni base de datos externa. SQLite se usa automáticamente y los correos se imprimen en la consola del servidor.

### Paso 5 — Correr las migraciones

```bash
python manage.py migrate
```

Este comando crea el archivo `db.sqlite3` con todas las tablas del sistema.

### Paso 6 — Crear el superusuario administrador

```bash
python manage.py createsuperuser
```

Ingresar los siguientes datos cuando el sistema los solicite:

- **Username:** `admin`
- **Email:** `admin@restaurante.com`
- **Password:** `Admin1234!`

### Paso 7 — Cargar los datos de prueba

Los fixtures deben cargarse en este orden exacto debido a las dependencias entre modelos:

```bash
python manage.py loaddata fixtures/01_grupos.json
python manage.py loaddata fixtures/02_usuarios.json
python manage.py loaddata fixtures/03_menu.json
python manage.py loaddata fixtures/04_mesas.json
python manage.py loaddata fixtures/05_pedidos.json
python manage.py loaddata fixtures/06_reservas.json
```

### Paso 8 — Levantar el servidor

```bash
python manage.py runserver
```

Abrir el navegador en: **http://127.0.0.1:8000**

---

## Credenciales de prueba

| Rol | Usuario | Contraseña | Acceso |
|---|---|---|---|
| Administrador (superusuario) | `admin` | `Admin1234!` | Dashboard completo, /admin, reportes, inventario |
| Administrador (fixture) | `admin1` | `Demo1234!` | Dashboard completo, reportes, inventario |
| Mesero | `mesero1` | `Demo1234!` | Pedidos activos, cambio de estado, reservas |
| Mesero | `mesero2` | `Demo1234!` | Pedidos activos, cambio de estado, reservas |
| Cliente | `cliente1` | `Demo1234!` | Menú, carrito, pedidos, reservas |
| Cliente | `cliente2` | `Demo1234!` | Menú, carrito, pedidos, reservas |
| Cliente | `cliente3` | `Demo1234!` | Menú, carrito, pedidos, reservas |

---

## Funcionalidades principales

1. **Autenticación con roles** — registro público (rol cliente), login y control de acceso por rol (cliente, mesero, administrador)
2. **CRUD completo de menú** — gestión de platos, categorías e ingredientes con imágenes y control de disponibilidad
3. **Sistema de pedidos** — carrito de compras en sesión, confirmación de pedido con selección de mesa y pago simulado
4. **Reservas de mesas** — alta, edición y cancelación de reservas con validación de conflictos de horario
5. **Control de inventario** — descuento automático de stock al confirmar pedidos, alertas de stock bajo y registro de movimientos
6. **Notificaciones por correo** — confirmación de pedido, cambio de estado y alerta de stock bajo (en local se muestran en consola)
7. **Panel de administración** — KPIs del día: ventas, pedidos, platos vendidos e ingresos en proceso
8. **Gráficos estadísticos** — platos más vendidos e ingresos por mes renderizados con Chart.js
9. **Exportación de reportes** — descarga de reportes en PDF y Excel con filtros por rango de fecha
10. **Interfaz responsive** — diseño adaptado a móvil y escritorio con modo oscuro y modo claro

---

## Rutas principales del sistema

| URL | Vista | Roles con acceso |
|---|---|---|
| `/` | Redirección al dashboard o menú según rol | Todos (autenticados) |
| `/accounts/login/` | Inicio de sesión | Público |
| `/accounts/register/` | Registro de nueva cuenta | Público |
| `/menu/` | Lista de platos con carrito lateral | Todos |
| `/orders/carrito/` | Ver contenido del carrito | Cliente |
| `/orders/crear/` | Confirmar y crear pedido | Cliente |
| `/orders/mis-pedidos/` | Historial de pedidos del cliente | Cliente |
| `/orders/activos/` | Lista de pedidos pendientes | Mesero, Admin |
| `/reservations/reservar/` | Nueva reserva de mesa | Cliente |
| `/inventory/` | Control de stock e ingredientes | Mesero, Admin |
| `/dashboard/` | Panel con KPIs y gráficos | Admin |
| `/dashboard/exportar/pedidos/pdf/` | Exportar reporte en PDF | Admin |
| `/admin/` | Panel de administración de Django | Superusuario |

---

## Notas de desarrollo

- Los correos en modo local se imprimen en la consola donde corre el servidor — no se envían por SMTP real.
- Las imágenes subidas se guardan en la carpeta `media/` en la raíz del proyecto.
- La base de datos SQLite se crea en `db.sqlite3` en la raíz — este archivo está en `.gitignore` y no se sube al repositorio.
- Para reiniciar la base de datos completamente: eliminar `db.sqlite3`, correr `python manage.py migrate` y luego cargar los fixtures nuevamente.

---

## Autores

| Nombre | Rol en el proyecto |
|---|---|
| Juan Pablo Gallardo | Backend Core — modelos, autenticación, configuración y despliegue |
| Sebastián López | Backend Features — pedidos, reservas, inventario y reportes |
| Miguel Ángel Mendoza | Frontend y Dashboard — templates, estilos, gráficos y UX |

---

## Licencia

Este proyecto fue desarrollado con fines académicos bajo la licencia [MIT](https://opensource.org/licenses/MIT).
