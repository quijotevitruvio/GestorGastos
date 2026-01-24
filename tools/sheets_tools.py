#!/usr/bin/env python3
"""
============================================================
Ge$torGasto$ - Herramientas de Google Sheets
============================================================

Script de utilidades para administrar la conexión y estructura
de Google Sheets usado por Ge$torGasto$.

USO:
    python tools/sheets_tools.py check    - Verificar conexión a Google Sheets
    python tools/sheets_tools.py headers  - Verificar estructura de columnas
    python tools/sheets_tools.py results  - Ver estado de procesamiento de filas
    python tools/sheets_tools.py init     - Inicializar hoja con encabezados

Este script consolida las funciones de los archivos originales:
- check_access.py
- verify_headers.py
- verify_results.py
- init_sheet.py
"""

# ============================================================
# IMPORTACIÓN DE LIBRERÍAS
# ============================================================
import sys    # Para leer argumentos de línea de comandos
import os     # Para manejo de rutas y variables de entorno

# Agregar directorio padre al path para poder importar módulos del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gspread                  # Librería para interactuar con Google Sheets
from dotenv import load_dotenv  # Cargar variables desde archivo .env

# Cargar variables de entorno
load_dotenv()

# ============================================================
# CONSTANTES
# ============================================================
# Lista de encabezados esperados en la hoja de cálculo
# El orden debe coincidir con el formulario de ingreso en app.py
ENCABEZADOS_ESPERADOS = [
    "Fecha",              # Fecha del gasto
    "Concepto",           # Descripción del gasto
    "Monto",              # Cantidad gastada
    "Divisa",             # COP, USD, EUR
    "Categoria",          # Categoría del gasto
    "Lugar",              # Dónde se realizó el gasto
    "MedioPago",          # Efectivo, Tarjeta, etc.
    "Banco",              # Entidad financiera
    "Score",              # Puntuación IA (1-5)
    "Justificacion",      # Explicación de la IA
    "Color",              # Color hexadecimal según Score
    "CategoriaSugerida"   # Categoría recomendada por IA
]

# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def obtener_credenciales():
    """
    Obtiene la conexión a Google Sheets usando las credenciales disponibles.
    
    Intenta en este orden:
    1. Archivo credentials.json local (para desarrollo)
    2. Variable de entorno GOOGLE_CREDENTIALS (para producción/nube)
    
    Returns:
        Objeto gspread.Client autenticado
        
    Raises:
        FileNotFoundError si no encuentra credenciales
    """
    # Ruta al archivo de credenciales (en la raíz del proyecto)
    ruta_credenciales = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        "credentials.json"
    )
    
    # Opción 1: Archivo local (desarrollo)
    if os.path.exists(ruta_credenciales):
        return gspread.service_account(filename=ruta_credenciales)
    
    # Opción 2: Variable de entorno (producción)
    elif os.getenv("GOOGLE_CREDENTIALS"):
        import json
        credenciales_json = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
        return gspread.service_account_from_dict(credenciales_json)
    
    else:
        raise FileNotFoundError(
            "No se encontraron credenciales.\n"
            "Opciones:\n"
            "  1. Colocar credentials.json en la raíz del proyecto\n"
            "  2. Definir variable de entorno GOOGLE_CREDENTIALS"
        )

# ============================================================
# COMANDOS DISPONIBLES
# ============================================================

def verificar_acceso():
    """
    Verifica la conexión a Google Sheets y lista las hojas disponibles.
    
    Útil para:
    - Confirmar que las credenciales funcionan
    - Ver qué hojas están compartidas con la cuenta de servicio
    """
    try:
        gc = obtener_credenciales()
        print("✅ Autenticación exitosa.")
        
        print("\n📋 Listando hojas de cálculo disponibles...")
        lista_archivos = gc.list_spreadsheet_files()
        
        if not lista_archivos:
            print("⚠️  No se encontraron hojas de cálculo.")
            print("   ¿Compartiste la hoja con el email de la cuenta de servicio?")
        else:
            print(f"Se encontraron {len(lista_archivos)} hojas:")
            for archivo in lista_archivos:
                print(f"  - {archivo['name']} (ID: {archivo['id']})")
                
    except Exception as e:
        print(f"❌ Error: {e}")


def verificar_encabezados():
    """
    Verifica que la hoja tenga todos los encabezados esperados.
    
    Compara los encabezados actuales con ENCABEZADOS_ESPERADOS
    y muestra cuáles faltan (si hay alguno).
    """
    try:
        gc = obtener_credenciales()
        nombre_hoja = os.getenv("GOOGLE_SHEET_NAME")
        sh = gc.open(nombre_hoja)
        worksheet = sh.sheet1
        
        encabezados_actuales = worksheet.row_values(1)
        
        print(f"📋 Verificando encabezados de '{nombre_hoja}'...")
        print(f"Encabezados encontrados: {encabezados_actuales}")
        
        # Buscar encabezados faltantes
        faltantes = [h for h in ENCABEZADOS_ESPERADOS if h not in encabezados_actuales]
        
        if faltantes:
            print(f"\n❌ ENCABEZADOS FALTANTES: {faltantes}")
            print("Por favor, agrega estas columnas en la primera fila de tu hoja.")
        else:
            print("\n✅ Todos los encabezados están presentes. ¡Estructura correcta!")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def verificar_resultados():
    """
    Muestra el estado de procesamiento de cada fila.
    
    Una fila está "procesada" si tiene Score asignado por la IA.
    Útil para ver cuántos gastos faltan por auditar.
    """
    try:
        gc = obtener_credenciales()
        nombre_hoja = os.getenv("GOOGLE_SHEET_NAME")
        sh = gc.open(nombre_hoja)
        worksheet = sh.sheet1
        
        filas = worksheet.get_all_records()
        print(f"📊 Verificando {len(filas)} filas...")
        
        contador_procesadas = 0
        for fila in filas:
            concepto = fila.get('Concepto', 'N/A')
            score = str(fila.get('Score', '')).strip()
            
            if score != '':
                contador_procesadas += 1
                print(f"  ✅ Procesada: {concepto} - Score: {score}")
            else:
                print(f"  ❌ Pendiente: {concepto}")
                
        print("\n" + "=" * 40)
        
        # Resumen
        if contador_procesadas == len(filas) and len(filas) > 0:
            print(f"✅ ÉXITO: ¡Todas las {len(filas)} filas procesadas!")
        elif len(filas) == 0:
            print("⚠️  ADVERTENCIA: No hay filas en la hoja.")
        else:
            print(f"📊 PARCIAL: {contador_procesadas}/{len(filas)} filas procesadas.")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def inicializar_hoja():
    """
    Inicializa la hoja agregando encabezados si está vacía.
    
    Si la hoja ya tiene contenido, no hace nada para evitar
    sobrescribir datos existentes.
    """
    try:
        gc = obtener_credenciales()
        nombre_hoja = os.getenv("GOOGLE_SHEET_NAME")
        sh = gc.open(nombre_hoja)
        worksheet = sh.sheet1
        
        encabezados_actuales = worksheet.row_values(1)
        
        if not encabezados_actuales:
            print(f"📝 La hoja '{nombre_hoja}' está vacía. Agregando encabezados...")
            worksheet.append_row(ENCABEZADOS_ESPERADOS)
            print("✅ ¡Encabezados agregados exitosamente!")
        else:
            print(f"ℹ️  La hoja '{nombre_hoja}' ya tiene contenido. Omitiendo inicialización.")
            print(f"Encabezados actuales: {encabezados_actuales}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

# ============================================================
# PUNTO DE ENTRADA PRINCIPAL
# ============================================================

def main():
    """
    Función principal que procesa los argumentos de línea de comandos
    y ejecuta el comando correspondiente.
    """
    # Si no hay argumentos, mostrar ayuda
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    comando = sys.argv[1].lower()
    
    # Mapeo de comandos a funciones
    comandos = {
        'check': verificar_acceso,      # Verificar conexión
        'headers': verificar_encabezados,  # Verificar estructura
        'results': verificar_resultados,    # Ver estado de filas
        'init': inicializar_hoja        # Inicializar hoja
    }
    
    if comando in comandos:
        comandos[comando]()
    else:
        print(f"❌ Comando desconocido: {comando}")
        print(__doc__)

# Ejecutar solo si se llama directamente (no como import)
if __name__ == "__main__":
    main()
