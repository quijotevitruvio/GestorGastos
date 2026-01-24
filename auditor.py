#!/usr/bin/env python3
"""
============================================================
Ge$torGasto$ - Auditor Financiero con IA (Gemini)
============================================================

Este módulo analiza cada gasto usando IA (Google Gemini) y asigna:
- Score (1-5): Qué tan necesario fue el gasto
- Justificación: Explicación del análisis
- Color: Código visual según la puntuación
- Categoría sugerida: Recomendación de categorización

El análisis considera:
- El concepto del gasto
- El monto y divisa
- El medio de pago (crédito vs efectivo)
- El lugar de compra
"""

# ============================================================
# IMPORTACIÓN DE LIBRERÍAS
# ============================================================
import os
import json
import time
from datetime import datetime
import gspread
import google.generativeai as genai
from dotenv import load_dotenv
from prompt import AUDITOR_SYSTEM_PROMPT
from utils import clean_json_string, print_result
from colorama import init

# Inicializar colorama (colores en consola)
init()

# Cargar variables de entorno (.env para local)
load_dotenv()

# ============================================================
# FUNCIONES PARA OBTENER SECRETOS
# ============================================================
# Soporta tanto .env (local) como st.secrets (Streamlit Cloud)

def obtener_secreto(nombre, default=None):
    """
    Obtiene un secreto desde st.secrets (Cloud) o os.getenv (local).
    """
    try:
        import streamlit as st
        return st.secrets.get(nombre, os.getenv(nombre, default))
    except:
        return os.getenv(nombre, default)

# ============================================================
# CONSTANTES
# ============================================================
GEMINI_API_KEY = obtener_secreto("GEMINI_API_KEY")
GOOGLE_SHEET_NAME = obtener_secreto("GOOGLE_SHEET_NAME")
GOOGLE_CREDENTIALS_FILE = "credentials.json"

# ============================================================
# FUNCIONES DE CONFIGURACIÓN
# ============================================================

def configure_gemini():
    """
    Configura la conexión con la API de Gemini.
    
    Returns:
        GenerativeModel configurado con el prompt de auditor
        
    Raises:
        ValueError si no hay API key
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY no encontrada en .env")
    
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel(
        'gemini-flash-latest', 
        system_instruction=AUDITOR_SYSTEM_PROMPT
    )


def connect_sheets():
    """
    Conecta con Google Sheets usando credenciales disponibles.
    
    Intenta:
    1. Archivo credentials.json local
    2. Variable de entorno GOOGLE_CREDENTIALS
    3. st.secrets (Streamlit Cloud)
    
    Returns:
        Worksheet (primera hoja del spreadsheet)
    """
    # Opción 1: Archivo local
    if os.path.exists(GOOGLE_CREDENTIALS_FILE):
        gc = gspread.service_account(filename=GOOGLE_CREDENTIALS_FILE)
    
    # Opción 2: Variable de entorno (para cloud)
    elif os.getenv("GOOGLE_CREDENTIALS"):
        creds_json = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
        gc = gspread.service_account_from_dict(creds_json)
    
    # Opción 3: Streamlit secrets
    else:
        try:
            import streamlit as st
            creds_json = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
            gc = gspread.service_account_from_dict(creds_json)
        except:
            raise FileNotFoundError(
                f"No se encontró {GOOGLE_CREDENTIALS_FILE}, "
                "ni GOOGLE_CREDENTIALS en env o st.secrets"
            )
    
    try:
        sh = gc.open(GOOGLE_SHEET_NAME)
        return sh.sheet1 
    except gspread.exceptions.SpreadsheetNotFound:
        raise ValueError(f"No se encontró la hoja de cálculo: {GOOGLE_SHEET_NAME}")


# ============================================================
# FUNCIONES DE PROCESAMIENTO
# ============================================================

def process_expense(model, concepto, monto, divisa, categoria, lugar, medio_pago, banco, fecha):
    """
    Analiza un gasto individual con IA.
    
    Args:
        model: Modelo de Gemini configurado
        concepto: Descripción del gasto
        monto: Cantidad gastada
        divisa: Código de divisa (COP, USD, EUR)
        categoria: Categoría del gasto
        lugar: Dónde se realizó el gasto
        medio_pago: Efectivo, tarjeta, etc.
        banco: Entidad financiera
        fecha: Fecha del gasto
        
    Returns:
        dict con score, justificacion, color, categoria_sugerida
        None si hay error
    """
    # Preparar datos para el modelo
    input_data = {
        "concepto": concepto,
        "monto": monto,
        "divisa": divisa,
        "categoria": categoria,
        "lugar": lugar,
        "medio_pago": medio_pago,
        "banco": banco,
        "fecha": fecha
    }
    
    try:
        response = model.generate_content(json.dumps(input_data))
        json_str = clean_json_string(response.text)
        return json.loads(json_str)
    except Exception as e:
        print(f"❌ Error procesando '{concepto}': {e}")
        return None


def auditar_gasto(concepto, monto, divisa="COP"):
    """
    Audita un gasto individual para uso en tiempo real.
    
    Args:
        concepto: Descripción del gasto
        monto: Cantidad gastada
        divisa: Código de divisa
        
    Returns:
        Tuple (score, justificacion, categoria_sugerida, color)
    """
    try:
        model = configure_gemini()
        result = process_expense(
            model, concepto, monto, divisa, 
            "General", "Desconocido", "Efectivo", "N/A", 
            datetime.now().strftime("%Y-%m-%d")
        )
        
        if result:
            return (
                result.get('score', 3),
                result.get('justificacion', 'Análisis automático'),
                result.get('categoria_sugerida', 'Otro'),
                result.get('color', '#808080')
            )
    except Exception as e:
        print(f"Error en auditar_gasto: {e}")
    
    # Valores por defecto si falla
    return (3, "Sin análisis IA", "Otro", "#808080")


def run_audit():
    """
    Ejecuta la auditoría completa de todos los gastos pendientes.
    
    Procesa cada fila que no tenga Score asignado,
    guardando los resultados y el timestamp de auditoría.
    
    Returns:
        dict con estadísticas: {"processed": N, "updated": N, "errors": N}
    """
    print("🚀 Iniciando Auditor Financiero IA...")
    stats = {"processed": 0, "updated": 0, "errors": 0}
    
    try:
        model = configure_gemini()
        sheet = connect_sheets()
        
        rows = sheet.get_all_records()
        print(f"📋 Leyendo {len(rows)} filas de '{GOOGLE_SHEET_NAME}'...")
        
        # Obtener índices de columnas
        headers = sheet.row_values(1)
        
        def get_col_idx(name):
            """Obtiene el índice de una columna por nombre."""
            try: 
                return headers.index(name) + 1
            except: 
                return None
        
        # Columnas de resultados
        col_score = get_col_idx('Score')
        col_just = get_col_idx('Justificacion')
        col_color = get_col_idx('Color')
        col_sug = get_col_idx('CategoriaSugerida')
        col_fecha_audit = get_col_idx('FechaAuditoria')  # Nueva columna para historial
        
        for i, row in enumerate(rows):
            actual_row_idx = i + 2  # +2 porque Sheet es 1-indexed y hay header
            
            # Verificar si ya está procesado (tiene Score)
            if str(row.get('Score', '')).strip() != '':
                continue
            
            # Obtener datos del gasto
            concepto = row.get('Concepto')
            monto = row.get('Monto')
            
            # Si no hay concepto o monto, saltar
            if not concepto or not monto:
                continue

            # Campos adicionales
            divisa = row.get('Divisa', 'COP')
            lugar = row.get('Lugar', 'Desconocido')
            categoria = row.get('Categoria', 'General')
            medio_pago = row.get('MedioPago', 'Efectivo')
            banco = row.get('Banco', 'N/A')
            fecha = row.get('Fecha', '')

            print(f"🔍 Procesando fila {actual_row_idx}: {concepto} ({monto} {divisa})...")
            
            # Analizar con IA
            result = process_expense(
                model, concepto, monto, divisa, categoria, 
                lugar, medio_pago, banco, fecha
            )
            
            if result:
                print_result(concepto, monto, result)
                
                try:
                    # Guardar resultados en la hoja
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                    updates = 0
                    
                    if col_score: 
                        sheet.update_cell(actual_row_idx, col_score, result['score'])
                        updates += 1
                    if col_just: 
                        sheet.update_cell(actual_row_idx, col_just, result['justificacion'])
                        updates += 1
                    if col_color: 
                        sheet.update_cell(actual_row_idx, col_color, result['color'])
                        updates += 1
                    if col_sug: 
                        sheet.update_cell(actual_row_idx, col_sug, result['categoria_sugerida'])
                        updates += 1
                    if col_fecha_audit:
                        sheet.update_cell(actual_row_idx, col_fecha_audit, timestamp)
                        updates += 1
                    
                    stats["processed"] += 1
                    stats["updated"] += updates
                    
                except Exception as e:
                    print(f"❌ Error actualizando hoja: {e}")
                    stats["errors"] += 1
            
            # Esperar para evitar rate limits de la API
            time.sleep(2)

    except Exception as e:
        print(f"💥 Error fatal: {e}")
        return stats
        
    print(f"\n✅ Auditoría completada: {stats['processed']} procesados, {stats['errors']} errores")
    return stats


# ============================================================
# PUNTO DE ENTRADA
# ============================================================

def main():
    """Función principal para ejecución directa."""
    run_audit()

if __name__ == "__main__":
    main()
