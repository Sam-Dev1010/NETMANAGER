# Network Traffic Manager

Herramienta de línea de comandos para monitorear, analizar y controlar el tráfico de red en Linux (compatible con Windows).

## Características

- **Monitor de ancho de banda en vivo** con gráficos de barras visuales
- **Conexiones activas** con proceso asociado y estado TCP
- **Análisis de tráfico** con tasas de transferencia y comparación de muestras
- **Firewall** con bloqueo/desbloqueo de IPs y puertos (aplica reglas reales con `iptables` en Linux)
- **Información de red** completa: interfaces, gateway, DNS, sistema

## Instalación

```bash
# Clonar o copiar el proyecto
cd NetworkTrafficManager

# Instalar dependencias
pip install -r requirements.txt

# Opcional: instalar comando global
chmod +x netmanager
sudo cp netmanager /usr/local/bin/
```

## Uso

```bash
# Ejecutar con permisos completos (recomendado)
sudo python3 main.py

# O si instalaste el comando global
sudo netmanager
```

## Menú Principal

| Opción | Descripción |
|--------|-------------|
| 1 | Monitoreo de Ancho de Banda |
| 2 | Conexiones Activas |
| 3 | Análisis de Tráfico |
| 4 | Firewall / Filtrado |
| 5 | Información de Red |
| 0 | Salir |

## Módulos

### 1. Monitoreo de Ancho de Banda

| Sub-opción | Descripción |
|------------|-------------|
| 1 | **Monitor en vivo** - Velocidad de subida/bajada en tiempo real con barras de progreso |
| 2 | **Instantánea** - Estado actual de la red (bytes, paquetes, errores) |
| 3 | **Tráfico por interfaz** - Desglose por cada tarjeta de red |
| 4 | **Estadísticas** - Paquetes, errores y descartados |

### 2. Conexiones Activas

| Sub-opción | Descripción |
|------------|-------------|
| 1 | **Listar todas** - PID, direcciones locales/remotas, estado, proceso |
| 2 | **Por estado** - Agrupación de conexiones por estado TCP |
| 3 | **Por proceso** - Conexiones agrupadas por nombre de proceso |
| 4 | **Top hosts** - Los hosts remotos con más conexiones |
| 5 | **Buscar por puerto** - Encuentra qué proceso usa un puerto específico |

### 3. Análisis de Tráfico

| Sub-opción | Descripción |
|------------|-------------|
| 1 | **Análisis en vivo** - Monitoreo temporizado con tasas de transferencia |
| 2 | **Reporte** - Resumen completo del tráfico actual |
| 3 | **Comparar muestras** - Diferencia entre la primera y última captura |
| 4 | **Guardar log** - Exporta muestras a JSON |
| 5 | **Cargar log** - Importa muestras desde JSON |

### 4. Firewall

| Sub-opción | Descripción |
|------------|-------------|
| 1 | Listar todas las reglas |
| 2 | Bloquear IP (aplica `iptables -A INPUT -s IP -j DROP`) |
| 3 | Desbloquear IP |
| 4 | Bloquear puerto (aplica `iptables -A INPUT -p tcp --dport PORT -j DROP`) |
| 5 | Desbloquear puerto |
| 6 | Whitelist - Permitir IP |
| 7 | Remover de whitelist |
| 8 | Ver elementos bloqueados |
| 9 | Ver elementos permitidos |
| 10 | Exportar reglas a JSON |
| 11 | Limpiar todas las reglas |

> Las reglas se guardan en `firewall_rules.json` y se aplican automáticamente con `iptables` cuando se ejecuta como root.

### 5. Información de Red

| Sub-opción | Descripción |
|------------|-------------|
| 1 | Interfaces detalladas (estado, velocidad, MTU, IPs) |
| 2 | Interfaces simples (solo IPs) |
| 3 | Gateway / Puerta de enlace |
| 4 | Servidores DNS |
| 5 | Info del sistema (OS, CPU, RAM, disco) |

## Estructura del Proyecto

```
NetworkTrafficManager/
├── main.py              # Menú principal
├── netmanager           # Script ejecutable global
├── requirements.txt     # Dependencias
├── firewall_rules.json  # Reglas del firewall (se crea automáticamente)
└── modules/
    ├── utils.py         # Funciones compartidas (format_bytes, etc.)
    ├── bandwidth.py     # Monitor de ancho de banda
    ├── connections.py   # Tracker de conexiones
    ├── analyzer.py      # Análisis de tráfico
    ├── firewall.py      # Gestor de firewall
    └── netinfo.py       # Información de red
```

## Permisos

- **Sin sudo**: La mayoría de las funciones de lectura funcionan (monitoreo, interfaces, etc.)
- **Con sudo**: Acceso completo incluyendo listar todas las conexiones y aplicar reglas de firewall

## Dependencias

- Python 3.8+
- `psutil` - Monitoreo de procesos y sistema
- `rich` - Interfaz de terminal con tablas, paneles y colores
