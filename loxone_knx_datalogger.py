#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
loxone_entity_analyzer.py - Análisis inteligente de controles de Loxone Miniserver
Características:
- Descarga automática de la estructura completa (LoxAPP3.json)
- Soporte para puerto personalizado
- Soporte para múltiples formatos de respuesta (con/sin wrapper LL)
- Clasificación inteligente por tipo de control
- Detección de habitaciones desde la configuración
- ⭐ Monitor de grupo con selección interactiva
- ⭐ Grabación en CSV SOLO cuando cambian valores
- Compatible con Miniserver Gen 1 y Gen 2
"""

import os
import re
import json
import csv
import requests
import time
import threading
from typing import Dict, Any, List, Optional, Set, Tuple
from collections import defaultdict
from datetime import datetime
from requests.auth import HTTPBasicAuth

# Configuración desde variables de entorno
LOXONE_IP = os.getenv("LOXONE_IP", "192.168.1.50")
LOXONE_PORT = os.getenv("LOXONE_PORT", "8050")
LOXONE_USER = os.getenv("LOXONE_USER", "admin")
LOXONE_PASSWORD = os.getenv("LOXONE_PASSWORD", "admin")

# Construir URL base con puerto
if LOXONE_PORT and LOXONE_PORT != "80":
    LOXONE_BASE_URL = f"http://{LOXONE_IP}:{LOXONE_PORT}"
else:
    LOXONE_BASE_URL = f"http://{LOXONE_IP}"


class LoxoneAnalyzer:
    """Analizador inteligente de controles de Loxone Miniserver"""

    def __init__(self):
        self.structure: Dict[str, Any] = {}
        self.controls: Dict[str, Any] = {}
        self.rooms: Dict[str, str] = {}
        self.categories: Dict[str, str] = {}
        self.analysis: Dict[str, Any] = {}
        self.auth = HTTPBasicAuth(LOXONE_USER, LOXONE_PASSWORD)

        print(f"🔧 Configuración:")
        print(f"   URL: {LOXONE_BASE_URL}")
        print(f"   Usuario: {LOXONE_USER}")

    def fetch_structure(self) -> bool:
        """Descarga la estructura completa del Miniserver (LoxAPP3.json)"""
        try:
            print("\n📡 Conectando a Loxone Miniserver...")
            url = f"{LOXONE_BASE_URL}/data/LoxAPP3.json"

            print(f"   Intentando: {url}")
            response = requests.get(url, auth=self.auth, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Detectar formato de respuesta
            # Formato 1: Con wrapper 'LL' -> {'LL': {'controls': {...}, 'rooms': {...}}}
            # Formato 2: Sin wrapper -> {'controls': {...}, 'rooms': {...}}

            if 'LL' in data:
                # Formato con wrapper LL (versiones antiguas)
                print("   ℹ️  Formato detectado: Con wrapper LL")
                self.structure = data['LL']
            elif 'controls' in data:
                # Formato directo (versiones modernas)
                print("   ℹ️  Formato detectado: Directo (sin wrapper LL)")
                self.structure = data
            else:
                print("❌ Error: Formato de respuesta inesperado")
                print(f"   Claves encontradas: {list(data.keys())}")
                return False

            self.controls = self.structure.get('controls', {})
            self.rooms = self.structure.get('rooms', {})
            self.categories = self.structure.get('cats', {})

            print(f"✓ Estructura descargada correctamente")
            print(f"  • Controles: {len(self.controls)}")
            print(f"  • Habitaciones: {len(self.rooms)}")
            print(f"  • Categorías: {len(self.categories)}")

            return True

        except requests.exceptions.ConnectionError as e:
            print(f"❌ Error de conexión: No se puede conectar al Miniserver")
            print(f"\n🔍 Diagnóstico:")
            print(f"   • URL intentada: {url}")
            print(f"   • Verifica que el Miniserver esté encendido")
            print(f"   • Verifica que la IP sea correcta: {LOXONE_IP}")
            print(f"   • Verifica que el puerto sea correcto: {LOXONE_PORT}")
            print(f"   • Verifica conectividad de red (ping {LOXONE_IP})")
            return False

        except requests.exceptions.Timeout:
            print(f"❌ Error: Tiempo de espera agotado")
            print(f"   El Miniserver no responde en {LOXONE_BASE_URL}")
            return False

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print(f"❌ Error de autenticación")
                print(f"   Usuario o contraseña incorrectos")
                print(f"   Usuario actual: {LOXONE_USER}")
            else:
                print(f"❌ Error HTTP {e.response.status_code}: {e}")
            return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Error de red: {e}")
            return False

        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return False

    def get_room_name(self, room_uuid: str) -> Optional[str]:
        """Obtiene el nombre de una habitación por su UUID"""
        if not room_uuid or room_uuid not in self.rooms:
            return None
        return self.rooms[room_uuid].get('name', 'Sin habitación')

    def get_category_name(self, cat_uuid: str) -> Optional[str]:
        """Obtiene el nombre de una categoría por su UUID"""
        if not cat_uuid or cat_uuid not in self.categories:
            return None
        return self.categories[cat_uuid].get('name', 'Sin categoría')

    def classify_control(self, uuid: str, control: Dict[str, Any]) -> Dict[str, Any]:
        """Clasifica un control según su tipo"""

        control_type = control.get('type', 'unknown')
        name = control.get('name', uuid)
        room_uuid = control.get('room', '')
        cat_uuid = control.get('cat', '')

        # Mapeo de tipos de Loxone a nombres legibles
        type_mapping = {
            # Luces y salidas
            'Switch': 'Interruptor',
            'Pushbutton': 'Pulsador',
            'Dimmer': 'Regulador de luz',
            'LightController': 'Controlador de luz',
            'ColorPicker': 'Selector de color RGB',
            'LightControllerV2': 'Controlador de luz V2',

            # Persianas y sombreado
            'Jalousie': 'Persiana/Estor',
            'Gate': 'Puerta motorizada',
            'Window': 'Ventana motorizada',
            'Blind': 'Cortina',

            # Clima
            'IRoomController': 'Control climático',
            'IRoomControllerV2': 'Control climático V2',
            'Heatmixer': 'Mezclador de calefacción',

            # Multimedia
            'AudioZone': 'Zona de audio',
            'MediaClient': 'Cliente multimedia',
            'MediaServer': 'Servidor multimedia',

            # Alarmas y seguridad
            'Alarm': 'Alarma',
            'AlarmClock': 'Despertador',
            'Tracker': 'Rastreador',
            'Presence': 'Detector de presencia',

            # Medidores
            'Meter': 'Medidor',
            'EnergyMonitor': 'Monitor de energía',

            # Comunicación
            'InfoOnlyDigital': 'Estado digital',
            'InfoOnlyAnalog': 'Estado analógico',
            'InfoOnlyText': 'Información texto',

            # Automatización
            'TimedSwitch': 'Temporizador',
            'UpDownDigital': 'Contador digital',
            'Webpage': 'Página web',
            'MessageCenter': 'Centro de mensajes',

            # Otros
            'Intercom': 'Intercomunicador',
            'CentralVentilation': 'Ventilación centralizada',
            'SmokeAlarm': 'Detector de humo',
            'Sauna': 'Sauna',
            'Pool': 'Piscina',
        }

        readable_type = type_mapping.get(control_type, control_type)

        classification = {
            'uuid': uuid,
            'name': name,
            'type': control_type,
            'type_readable': readable_type,
            'room': self.get_room_name(room_uuid),
            'category': self.get_category_name(cat_uuid),
            'states': control.get('states', {}),
            'details': control.get('details', {})
        }

        return classification

    def analyze_all(self) -> Dict[str, Any]:
        """Analiza todos los controles"""
        if not self.controls:
            print("❌ No hay controles cargados. Ejecuta fetch_structure() primero.")
            return {}

        print("\n🔍 Analizando controles...")

        analysis = {
            'timestamp': datetime.now().isoformat(),
            'miniserver_info': {
                'total_controls': len(self.controls),
                'total_rooms': len(self.rooms),
                'total_categories': len(self.categories),
            },
            'rooms': {},
            'controls_by_type': defaultdict(list),
            'controls_by_room': defaultdict(list),
            'all_controls': []
        }

        # Clasificar cada control
        for uuid, control in self.controls.items():
            classified = self.classify_control(uuid, control)

            # Añadir a lista completa
            analysis['all_controls'].append(classified)

            # Agrupar por tipo
            control_type = classified['type_readable']
            analysis['controls_by_type'][control_type].append(classified)

            # Agrupar por habitación
            room = classified['room'] or 'Sin habitación'
            analysis['controls_by_room'][room].append(classified)

        # Guardar información de habitaciones
        for room_uuid, room_data in self.rooms.items():
            analysis['rooms'][room_uuid] = {
                'name': room_data.get('name', ''),
                'type': room_data.get('type', 0)
            }

        self.analysis = analysis
        return analysis

    def print_analysis(self) -> None:
        """Imprime el análisis de forma legible"""
        if not self.analysis:
            print("❌ No hay análisis disponible. Ejecuta analyze_all() primero.")
            return

        print("\n" + "="*70)
        print("📊 ANÁLISIS COMPLETO DE LOXONE MINISERVER")
        print("="*70)

        info = self.analysis['miniserver_info']
        print(f"\n📈 RESUMEN:")
        print(f"  • Total controles: {info['total_controls']}")
        print(f"  • Total habitaciones: {info['total_rooms']}")
        print(f"  • Total categorías: {info['total_categories']}")

        # Habitaciones
        print(f"\n🏠 HABITACIONES ({len(self.analysis['rooms'])}):")
        for i, (uuid, room_data) in enumerate(self.analysis['rooms'].items(), 1):
            print(f"  {i}. {room_data['name']}")

        # Controles por tipo
        print(f"\n🎛️  CONTROLES POR TIPO:")
        for control_type, controls in sorted(self.analysis['controls_by_type'].items()):
            print(f"\n  📌 {control_type} ({len(controls)}):")
            for control in controls[:10]:
                room = f" [{control['room']}]" if control['room'] else ""
                print(f"    • {control['name']}{room}")

            if len(controls) > 10:
                print(f"    ... y {len(controls)-10} más")

        # Controles por habitación
        print(f"\n🏠 CONTROLES POR HABITACIÓN:")
        for room, controls in sorted(self.analysis['controls_by_room'].items()):
            if controls:
                print(f"\n  📍 {room} ({len(controls)} controles):")
                for control in controls[:8]:
                    print(f"    • {control['name']} ({control['type_readable']})")

                if len(controls) > 8:
                    print(f"    ... y {len(controls)-8} más")

        print("\n" + "="*70)

    def save_analysis(self, filepath: str = "loxone_analysis.json") -> bool:
        """Guarda el análisis en un archivo JSON"""
        if not self.analysis:
            print("❌ No hay análisis disponible.")
            return False

        try:
            # Convertir defaultdict a dict para JSON
            analysis_copy = json.loads(json.dumps(self.analysis, default=list))

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis_copy, f, ensure_ascii=False, indent=2)

            print(f"✓ Análisis guardado en: {filepath}")
            return True

        except Exception as e:
            print(f"❌ Error guardando análisis: {e}")
            return False

    # ⭐ FUNCIONALIDADES DE MONITOR DE GRUPO

    def list_all_controls_numbered(self) -> List[Dict[str, Any]]:
        """Lista todos los controles con numeración para selección"""
        if not self.analysis or not self.analysis.get('all_controls'):
            print("❌ No hay controles disponibles. Ejecuta analyze_all() primero.")
            return []

        controls_list = self.analysis['all_controls']

        print("\n" + "="*90)
        print("📋 LISTA COMPLETA DE CONTROLES")
        print("="*90)

        for idx, control in enumerate(controls_list, 1):
            room = f"[{control['room']}]" if control['room'] else "[Sin habitación]"
            type_str = control['type_readable']
            name = control['name']

            print(f"{idx:4d}. {room:20s} {type_str:25s} {name}")

        print("="*90)
        print(f"Total: {len(controls_list)} controles\n")

        # Añadir índice a cada control
        for idx, control in enumerate(controls_list, 1):
            control['index'] = idx

        return controls_list

    def select_controls_interactive(self, controls_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Permite añadir controles una por una de forma interactiva"""
        print("\n📌 SELECCIÓN INTERACTIVA DE CONTROLES")
        print("="*80)
        print("Instrucciones:")
        print("  • Escribe 'todos' o 'all' para seleccionar TODOS")
        print("  • Escribe el número del control para añadirlo")
        print("  • Escribe rangos: 1-10, 15-20")
        print("  • Presiona Enter (vacío) cuando termines de añadir")
        print("="*80)

        selected_controls = []
        selected_indices = set()

        while True:
            current_count = len(selected_controls)
            prompt = f"\n➤ Control #{current_count + 1} (Enter para terminar): "
            selection = input(prompt).strip().lower()

            # Si presiona Enter vacío, terminar
            if not selection:
                if selected_controls:
                    print(f"\n✓ Selección completada: {len(selected_controls)} controles")
                    break
                else:
                    print("❌ No se seleccionó ningún control")
                    return []

            # Opción: todos
            if selection in ['todos', 'all', '*']:
                print(f"✓ Seleccionados TODOS los controles ({len(controls_list)})")
                return controls_list

            # Parsear selección
            try:
                new_indices = set()

                parts = selection.split(',')
                for part in parts:
                    part = part.strip()

                    if '-' in part:
                        range_parts = part.split('-')
                        if len(range_parts) == 2:
                            start = int(range_parts[0].strip())
                            end = int(range_parts[1].strip())
                            new_indices.update(range(start, end + 1))
                    else:
                        new_indices.add(int(part))

                # Añadir nuevos controles
                added = 0
                for idx in new_indices:
                    if idx not in selected_indices and 1 <= idx <= len(controls_list):
                        control = controls_list[idx - 1]
                        selected_controls.append(control)
                        selected_indices.add(idx)
                        added += 1
                        print(f"  ✓ Añadido: {control['name']} ({control['type_readable']})")

                if added == 0:
                    print("  ⚠️  Control(es) ya seleccionado(s) o número inválido")

            except ValueError:
                print("  ❌ Formato inválido. Usa números, rangos o 'todos'")

        # Mostrar resumen
        if selected_controls:
            print(f"\n📊 RESUMEN DE SELECCIÓN ({len(selected_controls)} controles):")
            for i, control in enumerate(selected_controls[:10], 1):
                room = f" [{control['room']}]" if control['room'] else ""
                print(f"  {i}. {control['name']}{room}")
            if len(selected_controls) > 10:
                print(f"  ... y {len(selected_controls) - 10} más")

        return selected_controls

    def get_control_state(self, uuid: str) -> Optional[str]:
        """Obtiene el estado actual de un control mediante la API de Loxone"""
        try:
            # Endpoint para obtener estado
            url = f"{LOXONE_BASE_URL}/jdev/sps/io/{uuid}/state"
            response = requests.get(url, auth=self.auth, timeout=5)
            response.raise_for_status()

            data = response.json()

            # Loxone devuelve el estado en LL.value
            if 'LL' in data and 'value' in data['LL']:
                return str(data['LL']['value'])

            return None

        except:
            return None

    def start_group_monitoring(self, selected_controls: List[Dict[str, Any]], csv_filename: str = None):
        """Inicia monitoreo continuo guardando SOLO cuando cambian los valores"""

        if not selected_controls:
            print("❌ No hay controles seleccionados para monitorizar")
            return

        # Generar nombre de archivo si no se proporciona
        if csv_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"loxone_monitor_{timestamp}.csv"

        print("\n" + "="*80)
        print("🎬 INICIANDO MONITOR DE GRUPO LOXONE")
        print("="*80)
        print(f"📄 Archivo CSV: {csv_filename}")
        print(f"📊 Controles monitorizados: {len(selected_controls)}")
        print(f"⚡ Modo: SOLO guardar cuando cambian valores")
        print(f"⏱️  Intervalo de comprobación: 1 segundo")
        print("\n⚠️  Presiona ENTER para detener el monitoreo")
        print("="*80)

        monitoring = {"active": True}

        # Diccionario para guardar el último estado conocido
        last_states = {}

        try:
            # Columnas del CSV
            fieldnames = ['timestamp', 'uuid', 'name', 'type', 'room', 'state']

            # Abrir archivo CSV
            file_exists = os.path.exists(csv_filename)
            csvfile = open(csv_filename, 'a', newline='', encoding='utf-8')
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')

            if not file_exists:
                writer.writeheader()

            # Inicializar estados previos y escribir estado inicial
            print("\n📝 Guardando estado inicial...")
            for control in selected_controls:
                uuid = control['uuid']
                current_state = self.get_control_state(uuid)

                if current_state is not None:
                    last_states[uuid] = current_state

                    # Guardar estado inicial
                    row = {
                        'timestamp': datetime.now().isoformat(),
                        'uuid': uuid,
                        'name': control['name'],
                        'type': control['type_readable'],
                        'room': control['room'] or 'Sin habitación',
                        'state': current_state
                    }

                    writer.writerow(row)

            csvfile.flush()
            print(f"✓ Estado inicial guardado ({len(selected_controls)} registros)")

            # Thread para monitoreo continuo
            def monitor_loop():
                changes_count = 0
                checks_count = 0

                while monitoring["active"]:
                    checks_count += 1
                    timestamp = datetime.now().isoformat()

                    for control in selected_controls:
                        uuid = control['uuid']

                        # Obtener estado actual
                        new_state = self.get_control_state(uuid)

                        if new_state is not None:
                            old_state = last_states.get(uuid)

                            # Solo guardar si cambió el estado
                            if new_state != old_state:
                                changes_count += 1
                                last_states[uuid] = new_state

                                row = {
                                    'timestamp': timestamp,
                                    'uuid': uuid,
                                    'name': control['name'],
                                    'type': control['type_readable'],
                                    'room': control['room'] or 'Sin habitación',
                                    'state': new_state
                                }

                                writer.writerow(row)
                                csvfile.flush()

                                # Mostrar cambio
                                print(f"🔄 [{timestamp}] {control['name']}: {old_state} → {new_state}")

                    # Mostrar estadísticas cada 100 comprobaciones
                    if checks_count % 100 == 0:
                        print(f"📊 Comprobaciones: {checks_count} | Cambios detectados: {changes_count}")

                    # Esperar antes de la siguiente comprobación (1 segundo)
                    time.sleep(1)

                csvfile.close()
                print(f"\n✓ Monitoreo finalizado")
                print(f"  📈 Total comprobaciones: {checks_count}")
                print(f"  🔄 Total cambios guardados: {changes_count}")
                print(f"  📄 Archivo: {csv_filename}")

            # Iniciar thread de monitoreo
            monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
            monitor_thread.start()

            # Esperar a que el usuario presione Enter
            input()

            # Detener monitoreo
            monitoring["active"] = False
            monitor_thread.join(timeout=5)

            print("\n" + "="*80)
            print("🛑 Monitoreo detenido por el usuario")
            print("="*80)

        except Exception as e:
            print(f"❌ Error durante el monitoreo: {e}")
            monitoring["active"] = False


def main():
    """Función principal"""
    print("="*70)
    print("🏠 ANALIZADOR DE LOXONE MINISERVER")
    print("   Compatible con Gen 1 y Gen 2")
    print("="*70)

    while True:
        print("\n📋 MENÚ PRINCIPAL:")
        print("  1. Análisis completo de controles")
        print("  2. Monitor de grupo (grabación optimizada CSV)")
        print("  3. Salir")

        choice = input("\n➤ Selecciona una opción (1-3): ").strip()

        if choice == "1":
            # Análisis completo
            analyzer = LoxoneAnalyzer()

            if not analyzer.fetch_structure():
                continue

            analyzer.analyze_all()
            analyzer.print_analysis()
            analyzer.save_analysis()

            print("\n💾 Análisis completo guardado en: loxone_analysis.json")

        elif choice == "2":
            # Monitor de grupo
            analyzer = LoxoneAnalyzer()

            if not analyzer.fetch_structure():
                continue

            analyzer.analyze_all()

            # Listar todos los controles con números
            controls_list = analyzer.list_all_controls_numbered()

            if not controls_list:
                continue

            # Seleccionar controles de forma interactiva
            selected = analyzer.select_controls_interactive(controls_list)

            if selected:
                # Preguntar nombre de archivo
                csv_name = input("\n📄 Nombre del archivo CSV (Enter para auto): ").strip()
                csv_name = csv_name if csv_name else None

                # Iniciar monitoreo optimizado
                analyzer.start_group_monitoring(selected, csv_name)

        elif choice == "3":
            print("\n👋 ¡Hasta luego!")
            break

        else:
            print("❌ Opción no válida")


if __name__ == "__main__":
    main()
