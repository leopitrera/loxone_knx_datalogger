# Loxone Entity Analyzer

Script Python para analizar y clasificar todos los controles de Loxone Miniserver y monitorizar cambios de estado en CSV optimizado.

## 🎯 Características

- **Análisis completo**: Descarga y clasifica todos los controles del Miniserver por tipo y habitación
- **Monitor de grupo**: Selección interactiva de entidades para monitorizar
- **Grabación optimizada**: Solo guarda en CSV cuando el estado cambia (reduce tamaño hasta 100x)
- **Soporte multi-formato**: Compatible con formatos LoxAPP3 con y sin wrapper 'LL'
- **Puerto personalizable**: Funciona con cualquier puerto del Miniserver
- **Más de 30 tipos de controles**: Luces, persianas, clima, audio, seguridad, etc.

## 📋 Requisitos

- Python 3.9 o superior
- Loxone Miniserver accesible por HTTP
- Credenciales de acceso al Miniserver

## 🔧 Instalación

```bash
# Clonar repositorio
git clone https://github.com/leopitrera/loxone-entity-analyzer.git
cd loxone-entity-analyzer

# Instalar dependencias
pip install requests
```

## ⚙️ Configuración

Antes de ejecutar el script, configura las variables de entorno:

```bash
export LOXONE_IP="192.168.x.x"
export LOXONE_PORT="8050"  # Opcional, por defecto 80
export LOXONE_USER="admin"
export LOXONE_PASSWORD="tu_contraseña"
```

## 🚀 Uso

```bash
python3 loxone_entity_analyzer.py
```

### Menú Principal

Al ejecutar el script verás:

```
📋 MENÚ PRINCIPAL:
  1. Análisis completo de controles
  2. Monitor de grupo (grabación optimizada CSV)
  3. Salir
```

### 1️⃣ Análisis Completo

Esta opción:
- Descarga toda la estructura del Miniserver desde `/data/LoxAPP3.json`
- Clasifica todos los controles por tipo (luces, persianas, clima, etc.)
- Agrupa por habitaciones automáticamente
- Muestra resumen en consola
- Guarda el resultado en `loxone_analysis.json`

**Ejemplo de salida:**

```
📊 ANÁLISIS COMPLETO DE LOXONE MINISERVER
📈 RESUMEN:
  • Total controles: 87
  • Total habitaciones: 8
  • Total categorías: 5

🏠 HABITACIONES (8):
  1. Salón
  2. Cocina
  3. Dormitorio Principal
  ...

🎛️  CONTROLES POR TIPO:
  📌 Regulador de luz (12):
    • Luz Salón Principal [Salón]
    • Luz Cocina Techo [Cocina]
    ...
```

### 2️⃣ Monitor de Grupo

Esta opción permite monitorizar entidades específicas y guardar **solo los cambios** en un CSV.

#### Paso 1: Selección de Entidades

El script muestra todas las entidades numeradas:

```
   1. [Dimmer          ] Luz Salón                      [Salón]          = 85
   2. [Jalousie        ] Persiana Cocina                [Cocina]         = 50
   3. [IRoomController ] Climatización Dormitorio       [Dormitorio]     = 22.5
   ...
```

#### Paso 2: Añadir Entidades Interactivamente

El script te permite añadir entidades una por una:

```
➤ Entidad #1 (Enter para terminar): 5
  ✓ Añadida: Temperatura Salón

➤ Entidad #2 (Enter para terminar): 10-15
  ✓ Añadida: Luz Cocina
  ✓ Añadida: Luz Dormitorio
  ✓ Añadida: Persiana Salón
  ...

➤ Entidad #3 (Enter para terminar): 20,25,30
  ✓ Añadida: Sensor Humedad
  ✓ Añadida: Puerta Principal
  ✓ Añadida: Ventana Cocina

➤ Entidad #4 (Enter para terminar): [Enter vacío]
```

**Opciones de selección:**
- `5` → Añadir entidad número 5
- `10-15` → Añadir entidades de la 10 a la 15
- `1,5,10` → Añadir entidades 1, 5 y 10
- `todos` o `all` → Añadir todas las entidades
- Enter vacío → Terminar selección

#### Paso 3: Nombre del Archivo CSV

```
📄 Nombre del archivo CSV (Enter para auto): sensores_salon.csv
```

O deja vacío para generar nombre automático: `monitor_group_YYYYMMDD_HHMMSS.csv`

#### Paso 4: Monitorización en Tiempo Real

El script empieza a monitorizar y **solo guarda cuando detecta cambios**:

```
📝 Guardando estado inicial...
✓ Estado inicial guardado (3 registros)

🔄 [2026-02-11T00:15:30] Luz Salón: 75 → 100
🔄 [2026-02-11T00:16:45] Persiana Cocina: 0 → 50
📊 Comprobaciones: 100 | Cambios detectados: 2

⚠️  Presiona ENTER para detener el monitoreo
```

#### Paso 5: Detener el Monitor

Simplemente presiona **Enter** para detener:

```
✓ Monitoreo finalizado
  📈 Total comprobaciones: 340
  🔄 Total cambios guardados: 5
  📄 Archivo: sensores_salon.csv
🛑 Monitoreo detenido por el usuario
```

## 📊 Formato del CSV Generado

El CSV contiene **solo los cambios de estado** detectados:

```csv
timestamp,uuid,name,type,room,state
2026-02-11T00:15:00,0f1e-2d3c-4b5a,Luz Salón,Dimmer,Salón,75
2026-02-11T00:15:30,0f1e-2d3c-4b5a,Luz Salón,Dimmer,Salón,100
2026-02-11T00:16:45,1a2b-3c4d-5e6f,Persiana Cocina,Jalousie,Cocina,50
2026-02-11T00:17:10,2b3c-4d5e-6f7a,Clima Dormitorio,IRoomController,Dormitorio,23
```

**Ventajas:**
- Archivos hasta 100x más pequeños que grabación continua
- Fácil análisis en Excel, pandas, Grafana
- Incluye timestamp preciso de cada cambio
- Mantiene todo el contexto (nombre, tipo, habitación)

## 🎛️ Tipos de Controles Soportados

### Iluminación
- Switch, Pushbutton, Dimmer, LightController, ColorPicker

### Persianas y Sombreado
- Jalousie, Gate, Window, Blind, EIBDimmer

### Climatización
- IRoomController, IRoomControllerV2, Heatmixer

### Multimedia
- AudioZone, MediaClient, MediaServer

### Seguridad
- Alarm, Tracker, Presence, SmokeAlarm

### Medición y Energía
- Meter, EnergyMonitor

### Puertas y Accesos
- Gate, Intercom, NFC Code Touch

### Otros
- Ventilation, Pool, InfoOnlyAnalog, InfoOnlyDigital, TextInput
- +20 tipos adicionales

## 💡 Casos de Uso

### Análisis de Rendimiento
```bash
# Monitorizar temperatura de varias habitaciones durante una semana
python3 loxone_entity_analyzer.py
# Opción 2 → Seleccionar sensores de temperatura → Dejar corriendo
```

### Auditoría de Seguridad
```bash
# Registrar todas las aperturas de puertas y ventanas
python3 loxone_entity_analyzer.py
# Opción 2 → Seleccionar sensores binarios de puertas/ventanas
```

### Análisis Energético
```bash
# Monitorizar consumo de luces y climatización
python3 loxone_entity_analyzer.py
# Opción 2 → Seleccionar luces y controladores de clima
```

### Diagnóstico de Fallos
```bash
# Detectar dispositivos que dejan de responder
python3 loxone_entity_analyzer.py
# Opción 1 → Ver lista completa de dispositivos y su estado
```

## 🔍 Troubleshooting

### Error de Conexión

```
❌ Error de conexión: Connection timeout
```

**Soluciones:**
- Verifica que el Miniserver esté encendido
- Comprueba la IP: `ping 192.168.1.50`
- Verifica el puerto (por defecto 80, algunos usan 8080 o 8050)
- Comprueba que estés en la misma red

### Error de Autenticación

```
❌ Error: 401 Unauthorized
```

**Soluciones:**
- Verifica usuario y contraseña
- Prueba con credenciales por defecto: `admin` / `admin`
- Comprueba que el usuario tenga permisos

### Formato de Respuesta Inesperado

```
❌ Error: Formato de respuesta inesperado
```

**Soluciones:**
- Este error ya está corregido en la última versión
- El script detecta automáticamente formato con o sin wrapper 'LL'
- Actualiza a la última versión del script

## 📄 Archivos Generados

- `loxone_analysis.json` - Análisis completo de la instalación
- `monitor_group_*.csv` - Datos de monitorización (solo cambios)

## 🤝 Contribuciones

Las contribuciones son bienvenidas! Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/NuevaFuncionalidad`)
3. Commit tus cambios (`git commit -m 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/NuevaFuncionalidad`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

## 🔗 Enlaces Útiles

- [Documentación Loxone Miniserver](https://www.loxone.com/dede/kb/api/)
- [Formato LoxAPP3.json](https://www.loxone.com/dede/kb/api/)
- [Issues y Soporte](https://github.com/leopitrera/loxone-entity-analyzer/issues)

## ⭐ Créditos

Desarrollado para facilitar el análisis y mantenimiento de instalaciones Loxone.

---

**¿Te ha sido útil?** Dale una ⭐ al repositorio!
