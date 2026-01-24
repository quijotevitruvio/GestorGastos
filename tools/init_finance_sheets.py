import gspread
from google.oauth2.service_account import Credentials
import os
import json
import logging

# Configuración de log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 1. Cargar Sheet Name desde .env (Manual)
SHEET_NAME = None
try:
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('GOOGLE_SHEET_NAME='):
                SHEET_NAME = line.split('=')[1].strip().strip('"').strip("'")
                logger.info(f"Sheet Name encontrado: {SHEET_NAME}")
                break
except Exception as e:
    logger.warning(f"Error leyendo .env: {e}")

if not SHEET_NAME:
    # Fallback env var
    SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "GestorGastos")

# Constantes
SCOPE = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# Definición de estructuras
SHEETS_CONFIG = {
    "Ingresos": [
        "Fecha", "Concepto", "Monto", "Divisa", "Fuente", "Recurrencia", "Comentario"
    ],
    "Deudas": [
        "ID", "FechaCreacion", "Tipo", "Persona", "Concepto", 
        "MontoOriginal", "Divisa", "MontoPagado", "Estado", "FechaLimite", "Comentario", "Alerta"
    ],
    "GestorGastos": [
        "Fecha", "Concepto", "Monto", "Divisa", "Categoria", 
        "Lugar", "MedioPago", "Banco", "Score", "Justificacion", 
        "Recurrencia", "Alerta"
    ]
}

def connect_sheets():
    """Conecta usando credentials.json."""
    try:
        # Prioridad: credentials.json
        if os.path.exists('credentials.json'):
            logger.info("Usando credentials.json")
            creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPE)
        else:
            raise FileNotFoundError("No se encuentra credentials.json")
            
        client = gspread.authorize(creds)
        return client.open(SHEET_NAME)
    except Exception as e:
        logger.error(f"Error conectando: {e}")
        raise

def init_sheets():
    """Crea las hojas necesarias."""
    try:
        sh = connect_sheets()
        logger.info(f"Conectado a: {sh.title}")
        
        existing_titles = [w.title for w in sh.worksheets()]
        logger.info(f"Hojas existentes: {existing_titles}")
        
        for sheet_title, headers in SHEETS_CONFIG.items():
            if sheet_title not in existing_titles:
                logger.info(f"Creando hoja '{sheet_title}'...")
                worksheet = sh.add_worksheet(title=sheet_title, rows=100, cols=len(headers))
                worksheet.append_row(headers)
                worksheet.format('A1:Z1', {'textFormat': {'bold': True}})
                logger.info(f"✅ Creada: {sheet_title}")
            else:
                logger.info(f"ℹ️ Existe: {sheet_title}")
                
        return True
    except Exception as e:
        logger.error(f"Fallo init: {e}")
        return False

if __name__ == "__main__":
    init_sheets()


