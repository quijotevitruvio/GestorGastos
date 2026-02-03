import json
import re
import os
import hashlib
import gspread
from datetime import datetime
try:
    import streamlit as st
except ImportError:
    st = None
from colorama import Fore, Style

def obtener_secreto(key, default=None):
    """Obtiene un secreto de st.secrets, os.getenv o devuelve default."""
    # 1. Streamlit Secrets
    if st is not None:
        try:
            return st.secrets.get(key, default)
        except (AttributeError, FileNotFoundError):
            pass # Si no estamos en Streamlit o no hay secrets file
    
    # 2. Environment Variables
    env_val = os.getenv(key)
    if env_val is not None:
        return env_val
        
    return default

def connect_sheets_utility(target_sheet=0):
    """
    Establece la conexión con Google Sheets.
    Lógica compartida para app.py y auditor.py.
    """
    GOOGLE_CREDENTIALS_FILE = "credentials.json"
    GOOGLE_SHEET_NAME = obtener_secreto("GOOGLE_SHEET_NAME")
    
    gc = None
    
    # Opción 1: Archivo local
    if os.path.exists(GOOGLE_CREDENTIALS_FILE):
        gc = gspread.service_account(filename=GOOGLE_CREDENTIALS_FILE)
    
    # Opción 2: Variable de entorno
    elif os.getenv("GOOGLE_CREDENTIALS"):
        creds_json = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
        gc = gspread.service_account_from_dict(creds_json)
    
    # Opción 3: Streamlit secrets
    elif st is not None:
        try:
            creds = st.secrets["GOOGLE_CREDENTIALS"]
            if hasattr(creds, 'to_dict'):
                creds_dict = creds.to_dict()
            elif isinstance(creds, dict):
                creds_dict = dict(creds)
            elif isinstance(creds, str):
                creds_dict = json.loads(creds)
            else:
                creds_dict = dict(creds)
            
            gc = gspread.service_account_from_dict(creds_dict)
        except Exception:
            pass
            
    if gc is None:
         raise FileNotFoundError("No se encontraron credenciales de Google (JSON local, ENV o Secrets).")
    
    try:
        sh = gc.open(GOOGLE_SHEET_NAME)
        if target_sheet == 0:
            return sh.sheet1
        else:
            return sh.worksheet(target_sheet)
    except gspread.exceptions.WorksheetNotFound:
        # Auto-crear hojas si no existen
        if target_sheet == "Usuarios":
            sh = gc.open(GOOGLE_SHEET_NAME)
            ws = sh.add_worksheet("Usuarios", rows=100, cols=5)
            ws.append_row(["Usuario", "Password_Hash", "Rol", "Estado", "Fecha_Registro"])
            
            admin_pass = obtener_secreto("ADMIN_PASSWORD", "admin123")
            pass_hash = hashlib.sha256(admin_pass.encode()).hexdigest()
            ws.append_row([obtener_secreto("ADMIN_USER", "admin"), pass_hash, "ADMIN", "ACTIVO", str(datetime.now())])
            return ws
        
        elif target_sheet == "Presupuestos":
            sh = gc.open(GOOGLE_SHEET_NAME)
            ws = sh.add_worksheet("Presupuestos", rows=100, cols=3)
            ws.append_row(["Categoria", "Monto_Limite", "Periodo"])
            # Inicializar con categorías comunes
            ws.append_row(["Comida", 500000, "Mensual"])
            ws.append_row(["Transporte", 300000, "Mensual"])
            ws.append_row(["Ocio", 200000, "Mensual"])
            return ws

        elif target_sheet == "Suscripciones":
            sh = gc.open(GOOGLE_SHEET_NAME)
            ws = sh.add_worksheet("Suscripciones", rows=100, cols=6)
            ws.append_row(["Servicio", "Monto", "Divisa", "Periodo", "Fecha_Cobro", "Estado"])
            return ws

        else:
            raise gspread.exceptions.WorksheetNotFound(f"Worksheet '{target_sheet}' not found")
    except gspread.exceptions.SpreadsheetNotFound:
        raise ValueError(f"No se encontró la hoja de cálculo: {GOOGLE_SHEET_NAME}")

def clean_json_string(json_string):
    """
    Intenta limpiar la respuesta de Gemini para obtener un JSON válido.
    Elimina bloques de markdown ```json ... ``` si existen.
    """
    try:
        # Buscar patrón de bloque de código
        match = re.search(r"```json\s*(\{.*?\})\s*```", json_string, re.DOTALL)
        if match:
            return match.group(1)
        
        # Si no hay bloques, intentar buscar llaves
        match = re.search(r"(\{.*?\})", json_string, re.DOTALL)
        if match:
            return match.group(0)
            
        return json_string
    except Exception:
        return json_string

def print_result(concepto, monto, result):
    """
    Imprime el resultado en consola con colores.
    """
    score = result.get("score", 0)
    color_hex = result.get("color", "#ffffff")
    
    # Mapeo simple de hex a colorama (aproximado para consola)
    console_color = Fore.WHITE
    if score >= 5: console_color = Fore.GREEN
    elif score == 4: console_color = Fore.GREEN
    elif score == 3: console_color = Fore.YELLOW
    elif score == 2: console_color = Fore.YELLOW # Naranja suele ser similar a amarillo en ansi básico
    elif score <= 1: console_color = Fore.RED

    print(f"\n{Style.BRIGHT}Análisis para: {concepto} (${monto}){Style.RESET_ALL}")
    print(f"Puntuación: {console_color}{score}/5{Style.RESET_ALL}")
    print(f"Justificación: {result.get('justificacion')}")
    print(f"Sugerencia: {result.get('categoria_sugerida')}")
    print("-" * 40)

# ============================================================
# AUDITOR PROMPT
# ============================================================
AUDITOR_SYSTEM_PROMPT = """
Entrada de datos: Recibirás un objeto con:
- "concepto": string
- "monto": number
- "divisa": string (COP, USD, EUR)
- "categoria": string
- "lugar": string (Contexto de dónde se compró)
- "medio_pago": string (Contexto de liquidez vs deuda)
- "banco": string (Entidad financiera)
- "fecha": string

Tu tarea:

1. Analiza el gasto considerando NO SOLO el concepto, sino también el medio de pago y lugar.
   - Ejemplo: Pagar un café con tarjeta de crédito a 36 cuotas es PEOR que pagarlo en efectivo.
   - Ejemplo: Comprar en una tienda de lujo vs tienda de barrio afecta la percepción de "necesidad".

2. Asigna una puntuación de 0 a 5.

3. Genera una justificación breve pero afilada. Si el usuario usó crédito para algo pequeño, menciónalo.

4. Asigna un color hexadecimal basado en la puntuación:
   5: #2ecc71 (Vital)
   4: #27ae60 (Necesario)
   3: #f1c40f (Opcional)
   2: #e67e22 (Prescindible)
   0-1: #e74c3c (Innecesario/Hormiga)

Formato de Salida Requerido (Estrictamente JSON):

{
  "score": number,
  "justificacion": "string",
  "color": "string",
  "categoria_sugerida": "string"
}
Restricción: No incluyas texto fuera del bloque JSON.
"""

# ============================================================
# CHAT ASSISTANT PROMPT
# ============================================================

PERSONALITY_PROMPTS = {
    "Neutro": "Mantén un tono profesional, objetivo y eficiente. Solo comenta lo necesario.",
    "Estricto": """
    ACTÚA COMO UN AUDITOR FINANCIERO SEVERO.
    - Juzga cada gasto. Si es innecesario (comida chatarra, vicios, lujos), REGAÑA al usuario.
    - Usa frases como: "¿En serio necesitabas esto?", "Tu yo del futuro está llorando", "Así nunca serás libre".
    - Si el gasto es bueno (educación, salud, ahorro), felicítalo brevemente.
    - Sé crudo y directo. No tengas piedad con el despilfarro.
    """,
    "Sarcástico": "Ten un humor ácido, cínico y sarcástico. Burlate sutilmente de los gastos, especialmente si son caprichos. Haz referencias a que el usuario probablemente morirá pobre si sigue así."
}

CHAT_SYSTEM_PROMPT = """
Eres el asistente financiero de Ge$torGasto$. Tu misión es ayudar al usuario a registrar transacciones o consultar información mediante conversación natural.

MODO DE PERSONALIDAD ACTIVO:
{personality_instruction}

Información actual:
- Fecha de hoy: {fecha_actual}

INTENCIONES SOPORTADAS:
- `gasto`: Registrar un gasto.
  - Campos obligatorios: concepto, monto.
  - Campos deseables: categoria (default: Otros), medio_pago (default: Efectivo), divisa (default: COP).
- `ingreso`: Registrar un ingreso.
  - Campos obligatorios: concepto, monto.
  - Campos deseables: fuente (default: Otros), divisa (default: COP).
- `deuda`: Registrar deuda/préstamo.
  - Campos obligatorios: persona, monto, tipo (ME_DEBEN o YO_DEBO), divisa (default: COP).
- `consulta`: Preguntas sobre datos (ej: "¿Cuánto gasté en comida?").
- `desconocido`: No entiendes la solicitud.

FORMATO DE RESPUESTA (JSON):
{{
  "intent": "gasto" | "ingreso" | "deuda" | "consulta" | "desconocido",
  "data": {{
    "concepto": "...",
    "monto": 0.0,
    "divisa": "COP",
    "categoria": "...",
    "medio_pago": "...",
    "fuente": "...",
    "persona": "...",
    "tipo": "..."
  }},
  "missing_info": [], 
  "response": "Texto para el usuario."
}}

REGLAS:
1. Si faltan campos OBLIGATORIOS, pregúntalos en `response`. `missing_info` debe listar qué falta.
2. Si tienes todos los obligatorios, asume defaults razonables para los deseables si no se especifican.
3. Si la intención es `consulta`, responde la pregunta en `response` usando la información del contexto.
4. Si la intención es transaccional y tienes los datos completos, `response` debe pedir confirmación explicita: "Entendido. ¿Registro el gasto de [Monto] en [Concepto]?"
5. Devuelve SOLO JSON válido sin bloques de código markdown.
"""
