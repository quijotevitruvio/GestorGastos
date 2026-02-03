#!/usr/bin/env python3
"""
============================================================
Ge$torGasto$ - Aplicación Principal (Interfaz Web)
============================================================

Esta es la aplicación principal que muestra la interfaz web usando Streamlit.
Permite al usuario:
- Iniciar sesión con credenciales seguras
- Registrar nuevos gastos manualmente
- Ejecutar auditorías con IA (Gemini)
- Ver estadísticas, gráficos y tendencias de gastos
- Filtrar datos por fecha, categoría, divisa y score
- Ver presupuesto y alertas

Para ejecutar: streamlit run app.py
"""

# ============================================================
# IMPORTACIÓN DE LIBRERÍAS
# ============================================================
import streamlit as st       # Framework para crear la interfaz web
import pandas as pd          # Manejo de datos tabulares
import plotly.express as px  # Gráficos interactivos
import gspread               # Conexión con Google Sheets
import json
import base64
import time
import os                    # Variables de entorno
from datetime import datetime, timedelta
from dotenv import load_dotenv  # Cargar variables desde .env
from currency import convertir_columna, formatear_moneda, obtener_tasas  # Conversión de divisas
from validators import (  # Validación de datos
    sanitizar_texto, validar_monto, validar_fecha, validar_concepto,
    validar_formulario_gasto, validar_formulario_ingreso, validar_formulario_deuda
)

# ============================================================
# CONFIGURACIÓN INICIAL
# ============================================================
load_dotenv()
st.set_page_config(page_title="Ge$torGasto$", page_icon="assets/logo.jpg", layout="wide")

# CSS Premium - Estética Moderna con Glassmorphism
st.markdown("""
<style>
    /* ========== GE$TORGASTO$ PREMIUM THEME ========== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    :root {
        --bg: #0a0a0a;
        --bg-gradient: linear-gradient(135deg, #0a0a0a 0%, #111111 50%, #0d1117 100%);
        --surface: #111111;
        --surface-glass: rgba(17, 17, 17, 0.85);
        --card-bg: rgba(20, 20, 20, 0.9);
        --border: #1a1a1a;
        --border-glow: #2a2a2a;
        --neon-green: #c8ff00;
        --neon-green-dim: rgba(200, 255, 0, 0.15);
        --neon-blue: #00d4ff;
        --neon-pink: #ff3366;
        --neon-red: #ff4444;
        --neon-orange: #ff9500;
        --text: #ffffff;
        --text-secondary: #a0a0a0;
        --text-dim: #666666;
        --success: #22c55e;
        --warning: #f59e0b;
        --danger: #ef4444;
    }
    
    /* ===== BASE ===== */
    .stApp { 
        background: var(--bg-gradient) !important; 
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: var(--text) !important;
    }
    
    /* ===== SIDEBAR PREMIUM ===== */
    [data-testid="stSidebar"] { 
        background: linear-gradient(180deg, #0a0a0a 0%, #111 100%) !important;
        border-right: 1px solid var(--border) !important;
    }
    
    [data-testid="stSidebar"] .stRadio > label {
        color: var(--text-secondary) !important;
    }
    
    /* ===== TARJETAS PRINCIPALES (GLASSMORPHISM) ===== */
    .patrimonio-card {
        background: linear-gradient(145deg, var(--neon-green) 0%, #a8d700 100%) !important;
        border-radius: 24px;
        padding: 28px;
        color: #000;
        box-shadow: 0 20px 60px rgba(200, 255, 0, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .patrimonio-card::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 100%;
        height: 100%;
        background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%);
        pointer-events: none;
    }
    
    .glass-card {
        background: var(--surface-glass) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--border-glow);
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .glass-card:hover {
        border-color: var(--neon-green);
        box-shadow: 0 12px 48px rgba(200, 255, 0, 0.1);
        transform: translateY(-2px);
    }
    
    /* ===== MÉTRICAS MEJORADAS ===== */
    [data-testid="stMetric"] {
        background: var(--card-bg) !important;
        border: 1px solid var(--border) !important;
        border-radius: 16px !important;
        padding: 20px 24px !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid="stMetric"]:hover {
        border-color: var(--neon-green) !important;
        box-shadow: 0 0 30px rgba(200, 255, 0, 0.15) !important;
        transform: translateY(-2px);
    }
    
    [data-testid="stMetricValue"] {
        color: var(--text) !important;
        font-size: 2rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    [data-testid="stMetricDelta"] {
        font-weight: 600 !important;
    }
    
    /* ===== BOTONES PREMIUM ===== */
    .stButton > button {
        background: transparent !important;
        color: var(--neon-green) !important;
        border: 2px solid var(--neon-green) !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.3px !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    .stButton > button:hover {
        background: var(--neon-green) !important;
        color: #000 !important;
        box-shadow: 0 0 40px rgba(200, 255, 0, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Botones Circulares para Acciones Rápidas */
    .action-btn {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        border: 2px solid var(--border);
        background: var(--surface);
        transition: all 0.3s ease;
        cursor: pointer;
        text-decoration: none;
    }
    
    .action-btn:hover {
        transform: scale(1.1);
        box-shadow: 0 0 25px currentColor;
    }
    
    .action-btn.gasto { color: var(--neon-pink); border-color: var(--neon-pink); }
    .action-btn.ingreso { color: var(--neon-green); border-color: var(--neon-green); }
    .action-btn.transfer { color: var(--neon-blue); border-color: var(--neon-blue); }
    .action-btn.cuentas { color: var(--neon-orange); border-color: var(--neon-orange); }
    
    /* ===== BARRA DE PROGRESO PREMIUM ===== */
    .progress-container {
        background: var(--border);
        border-radius: 10px;
        height: 12px;
        overflow: hidden;
        position: relative;
    }
    
    .progress-bar {
        height: 100%;
        border-radius: 10px;
        transition: width 0.5s ease;
        background: linear-gradient(90deg, var(--neon-green) 0%, #a8d700 100%);
        box-shadow: 0 0 15px rgba(200, 255, 0, 0.5);
    }
    
    .progress-bar.warning {
        background: linear-gradient(90deg, var(--warning) 0%, #d97706 100%);
        box-shadow: 0 0 15px rgba(245, 158, 11, 0.5);
    }
    
    .progress-bar.danger {
        background: linear-gradient(90deg, var(--danger) 0%, #dc2626 100%);
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.5);
    }
    
    /* ===== TOOLTIPS OCULTOS ===== */
    .stButton > button::after,
    .stFormSubmitButton > button::after,
    [data-testid="stFormSubmitButton"] > button::after,
    button[kind="formSubmit"]::before,
    button[kind="formSubmit"]::after,
    [data-testid="baseButton-secondary"]::after,
    [data-testid="baseButton-primary"]::after,
    [data-baseweb="tooltip"] {
        display: none !important;
        content: none !important;
    }
    
    /* ===== INPUTS MODERNOS ===== */
    input, textarea, select {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        color: var(--text) !important;
        padding: 12px 16px !important;
        transition: all 0.2s ease !important;
    }
    
    input:focus, textarea:focus, select:focus {
        border-color: var(--neon-green) !important;
        box-shadow: 0 0 20px rgba(200, 255, 0, 0.2) !important;
        outline: none !important;
    }
    
    /* ===== TABS PREMIUM ===== */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--surface) !important;
        border-radius: 12px !important;
        padding: 4px !important;
        gap: 4px !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: var(--text-dim) !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text-secondary) !important;
        background: var(--border) !important;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #000 !important;
        background: var(--neon-green) !important;
        border-bottom: none !important;
    }
    
    /* ===== TABLAS PREMIUM ===== */
    .stDataFrame {
        border: 1px solid var(--border) !important;
        border-radius: 16px !important;
        overflow: hidden !important;
    }
    
    /* ===== SCROLLBAR ELEGANTE ===== */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: var(--bg); border-radius: 4px; }
    ::-webkit-scrollbar-thumb { 
        background: var(--border-glow); 
        border-radius: 4px;
        transition: background 0.2s ease;
    }
    ::-webkit-scrollbar-thumb:hover { background: var(--neon-green); }
    
    /* ===== HEADERS CON ESTILO ===== */
    h1 { 
        color: var(--text) !important;
        font-weight: 800 !important;
        font-size: 2.2rem !important;
        letter-spacing: -0.5px !important;
    }
    
    h2 { 
        color: var(--text) !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
    }
    
    h3 { 
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
    }
    
    /* ===== BADGE ALERTA ===== */
    .badge-alert {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .badge-alert.warning {
        background: rgba(245, 158, 11, 0.15);
        color: var(--warning);
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    
    .badge-alert.danger {
        background: rgba(239, 68, 68, 0.15);
        color: var(--danger);
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    .badge-alert.success {
        background: rgba(34, 197, 94, 0.15);
        color: var(--success);
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    
    /* ===== RESUMEN CARD ===== */
    .summary-card {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 20px;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    
    .summary-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
    }
    
    .summary-icon.green { background: var(--neon-green-dim); }
    .summary-icon.blue { background: rgba(0, 212, 255, 0.15); }
    .summary-icon.pink { background: rgba(255, 51, 102, 0.15); }
    
    /* ===== FAB (Floating Action Button) ===== */
    .fab-container {
        position: fixed;
        bottom: 80px;
        right: 30px;
        z-index: 9999;
    }
    
    .fab-btn {
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--neon-green) 0%, #a8d700 100%);
        border: none;
        box-shadow: 0 8px 25px rgba(200, 255, 0, 0.4);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        color: #000;
        transition: all 0.3s ease;
    }
    
    .fab-btn:hover {
        transform: scale(1.1) rotate(90deg);
        box-shadow: 0 12px 35px rgba(200, 255, 0, 0.6);
    }
    
    /* ===== ANIMACIONES ===== */
    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 20px rgba(200, 255, 0, 0.3); }
        50% { box-shadow: 0 0 40px rgba(200, 255, 0, 0.6); }
    }
    
    @keyframes slide-up {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-pulse { animation: pulse-glow 2s infinite; }
    .animate-slide-up { animation: slide-up 0.5s ease-out; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# FUNCIONES PARA OBTENER SECRETOS
# ============================================================
# Soporta tanto .env (local) como st.secrets (Streamlit Cloud)

def obtener_secreto(nombre, default=None):
    """
    Obtiene un secreto desde st.secrets (Cloud) o os.getenv (local).
    Prioriza st.secrets para compatibilidad con Streamlit Cloud.
    """
    try:
        if nombre in st.secrets:
            return st.secrets[nombre]
    except:
        pass
    return os.getenv(nombre, default)

# ============================================================
# CONEXIÓN A GOOGLE SHEETS (para Streamlit Cloud)
# ============================================================
def connect_sheets(target_sheet=0):
    """
    Conecta con Google Sheets usando credenciales disponibles.
    target_sheet: Índice (0) o Nombre de la pestaña ("Ingresos", "Deudas")
    """
    GOOGLE_CREDENTIALS_FILE = "credentials.json"
    GOOGLE_SHEET_NAME = obtener_secreto("GOOGLE_SHEET_NAME")
    
    gc = None
    
    # Opción 1: Archivo local (desarrollo)
    if os.path.exists(GOOGLE_CREDENTIALS_FILE):
        gc = gspread.service_account(filename=GOOGLE_CREDENTIALS_FILE)
    
    # Opción 2: Variable de entorno
    elif os.getenv("GOOGLE_CREDENTIALS"):
        creds_json = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
        gc = gspread.service_account_from_dict(creds_json)
    
    # Opción 3: Streamlit secrets (tabla TOML o string JSON)
    else:
        try:
            creds = st.secrets["GOOGLE_CREDENTIALS"]
            # Si es un AttrDict/dict (formato tabla TOML), convertir a dict normal
            if hasattr(creds, 'to_dict'):
                creds_dict = creds.to_dict()
            elif isinstance(creds, dict):
                creds_dict = dict(creds)
            elif isinstance(creds, str):
                creds_dict = json.loads(creds)
            else:
                creds_dict = dict(creds)
            
            gc = gspread.service_account_from_dict(creds_dict)
        except Exception as e:
            raise FileNotFoundError(f"No se encontraron credenciales de Google: {e}")
    
    try:
        sh = gc.open(GOOGLE_SHEET_NAME)
        if target_sheet == 0:
            return sh.sheet1
        else:
            return sh.worksheet(target_sheet)
    except gspread.exceptions.WorksheetNotFound:
        # Lanzar excepción para que el llamador pueda manejar la creación de la hoja
        raise gspread.exceptions.WorksheetNotFound(f"Worksheet '{target_sheet}' not found")
    except gspread.exceptions.SpreadsheetNotFound:
        raise ValueError(f"No se encontró la hoja de cálculo: {GOOGLE_SHEET_NAME}")

# ============================================================
# SISTEMA DE AUTENTICACIÓN
# ============================================================
USUARIO_ADMIN = obtener_secreto("ADMIN_USER")
CONTRASEÑA_ADMIN = obtener_secreto("ADMIN_PASSWORD")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

import extra_streamlit_components as stx

def get_base64_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def verificar_login():
    """Muestra el formulario de login si el usuario no está autenticado."""
    
    # 1. Inicializar Cookie Manager
    cookie_manager = stx.CookieManager()
    
    # 2. Verificar si ya está autenticado en sesión actual
    if st.session_state.get("authenticated", False):
        return True
    
    # 3. Verificar si hay cookie de "recordarme"
    cookies = cookie_manager.get_all()
    if cookies.get("gestor_gastos_auth") == "true":
        st.session_state["authenticated"] = True
        return True
    
    # 4. Mostrar formulario de login con fondo premium
    bg_img = ""
    try:
        bin_str = get_base64_bin_file("assets/hero_bg.png")
        bg_img = f'data:image/png;base64,{bin_str}'
    except:
        pass
        
    st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("{bg_img}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        div[data-testid="stForm"] {{
            background: rgba(20, 20, 20, 0.7);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(200, 255, 0, 0.2);
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            animation: slide-up 0.8s ease-out;
        }}
        .stTextInput > div > div > input {{
            background: rgba(255,255,255,0.05) !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            color: white !important;
            border-radius: 12px !important;
        }}
        </style>
    """, unsafe_allow_html=True)
    
    # Intentar copiar assets a static para que Streamlit los sirva si es necesario
    # (Streamlit 1.10+ sirve /assets pero a veces necesita /static/assets)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div style='height: 10vh'></div>", unsafe_allow_html=True)
        st.markdown("""
            <div style='text-align: center; margin-bottom: 2rem;'>
                <h1 style='color: #c8ff00; font-size: 3.5rem; font-weight: 800; margin-bottom: 0;'>Ge$torGasto$</h1>
                <p style='color: #fff; opacity: 0.8; font-size: 1.1rem;'>Control financiero inteligente con IA</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("formulario_login"):
            usuario = st.text_input("👤 Usuario", placeholder="Ingresa tu usuario...")
            contraseña = st.text_input("🔑 Contraseña", type="password", placeholder="••••••••")
            recordarme = st.checkbox("💾 Recordarme en este dispositivo")
            
            st.markdown("<br>", unsafe_allow_html=True)
            enviado = st.form_submit_button("🚀 Iniciar Sesión", use_container_width=True)
            
            if enviado:
                if usuario == USUARIO_ADMIN and contraseña == CONTRASEÑA_ADMIN:
                    st.session_state["authenticated"] = True
                    if recordarme:
                        cookie_manager.set("gestor_gastos_auth", "true", key="set_auth_cookie", expires_at=datetime.now() + timedelta(days=30))
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")
    
    return False

if not verificar_login():
    st.stop()

# ============================================================
# TÍTULO PRINCIPAL - Centrado y pequeño
# ============================================================
try:
    col_l, col_c, col_r = st.columns([2, 1, 2])
    with col_c:
        st.image("assets/logo.jpg", width=120)
except:
    pass

st.markdown("""
<div style="text-align: center; padding: 0 0 20px 0;">
    <h2 style="color: #c8ff00; margin: 0; font-weight: 800;">💰 Ge$torGasto$</h2>
    <p style="color: #a0a0a0; font-size: 0.85rem; margin: 5px 0 0 0;">Tu Asistente Financiero con IA</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR: CONTROLES PRINCIPALES
# ============================================================

# Header con icono de logout
col_header, col_logout = st.sidebar.columns([4, 1])
with col_header:
    st.markdown("**⚙️ Panel**")
with col_logout:
    if st.button("🚪", help="Cerrar sesión"):
        st.session_state["authenticated"] = False
        st.rerun()

# ============================================================
# MENÚ DE NAVEGACIÓN PRINCIPAL (Fase 3)
# ============================================================

st.sidebar.markdown("---")

# Selector de Módulo
modulo = st.sidebar.radio(
    "Navegación", 
    ["🏠 Inicio", "💸 Egresos", "💰 Ingresos", "🏦 Cuentas", "🐷 Bolsillos", "🤝 Deudas", "🤖 Asistente IA"],
    index=0, # Default: Inicio (Dashboard)
    key="navegacion_principal"
)

st.sidebar.markdown("---")

# ============================================================
# FUNCIONES DE MÓDULOS (NUEVAS)
# ============================================================

# ============================================================
# MODALES FLOTANTES (Funciones Decoradas)
# ============================================================
@st.dialog("📝 Registrar Nuevo Ingreso")
def dialog_ingreso():
    with st.form("form_ingresos_modal"):
        fecha = st.date_input("Fecha", key="ing_fecha")
        concepto = st.text_input("Concepto", placeholder="Ej: Nómina")
        
        c1, c2 = st.columns(2)
        divisa = c1.selectbox("Divisa", ["COP", "USD", "EUR"], key="ing_divisa")
        monto = c2.number_input("Monto", min_value=0.0, step=10000.0, key="ing_monto")
        
        fuente = st.selectbox("Fuente", ["Nómina", "Negocio", "Inversión", "Regalo", "Otros"])
        recurrencia = st.selectbox("Frecuencia", ["Único", "Mensual", "Quincenal", "Anual"], index=1)
        comentario = st.text_area("Notas", height=2)
        
        if st.form_submit_button("💾 Guardar Ingreso", use_container_width=True):
            if monto > 0 and concepto:
                try:
                    sh = connect_sheets("Ingresos")
                    sh.append_row([
                        str(fecha), concepto, monto, divisa, fuente, recurrencia, comentario
                    ])
                    st.toast("✅ ¡Ingreso registrado exitosamente!")
                    st.cache_data.clear() 
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error guardando: {e}")
            else:
                st.warning("Completa concepto y monto.")

def render_ingresos():
    st.title("💰 Gestión de Ingresos")
    
    # Botón Flotante Principal
    col_btn, _ = st.columns([1, 4])
    if col_btn.button("➕ Nuevo Ingreso", use_container_width=True, type="primary"):
        dialog_ingreso()

    # --- Filtros ---
    with st.expander("🔍 Filtros", expanded=False):
        f1, f2 = st.columns(2)
        filtro_fuente = f1.multiselect("Fuente", ["Nómina", "Negocio", "Inversión", "Regalo", "Otros"])
        filtro_fecha = f2.date_input("Rango de Fechas", [])

    # --- Ver Datos (Full Width) ---
    try:
        sh = connect_sheets("Ingresos")
        records = sh.get_all_records()
        
        if records:
            df = pd.DataFrame(records)
            
            # Aplicar filtros
            if filtro_fuente and 'Fuente' in df.columns:
                df = df[df['Fuente'].isin(filtro_fuente)]
            
            # KPI Rápido
            k1, k2, k3 = st.columns(3)
            
            with k1:
                total_cop = df[df['Divisa'] == 'COP']['Monto'].sum() if 'Divisa' in df.columns else df['Monto'].sum()
                st.metric("Total Ingresos (COP)", f"${total_cop:,.0f}")
                
            with k2:
                df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
                hoy = datetime.now()
                mes_actual = df[
                    (df['Fecha'].dt.month == hoy.month) & 
                    (df['Fecha'].dt.year == hoy.year)
                ]
                total_mes_cop = mes_actual[mes_actual['Divisa'] == 'COP']['Monto'].sum() if 'Divisa' in mes_actual.columns else mes_actual['Monto'].sum()
                st.metric(f"Ingresos {hoy.strftime('%B')}", f"${total_mes_cop:,.0f}")
            
            with k3:
                st.metric("Registros", len(df))

            # --- Gráficos Plotly ---
            t1, t2 = st.tabs(["📊 Por Fuente", "📅 Tendencia"])
            with t1:
                if 'Fuente' in df.columns:
                    ing_fuente = df.groupby('Fuente')['Monto'].sum().reset_index()
                    fig_pie = px.pie(ing_fuente, values='Monto', names='Fuente', 
                                     hole=0.4, title="Distribución por Fuente")
                    fig_pie.update_layout(template="plotly_dark")
                    st.plotly_chart(fig_pie, use_container_width=True)
            
            with t2:
                df_trend = df.dropna(subset=['Fecha']).sort_values('Fecha')
                if not df_trend.empty:
                    fig_line = px.line(df_trend, x='Fecha', y='Monto', markers=True,
                                       title="Tendencia de Ingresos")
                    fig_line.update_layout(template="plotly_dark")
                    st.plotly_chart(fig_line, use_container_width=True)

            st.divider()
            
            # --- Vista Tarjetas / Tabla ---
            st.subheader("📋 Historial de Ingresos")
            
            # Toggle vista
            vista_ing = st.radio("Vista:", ["🃏 Tarjetas", "📋 Tabla"], horizontal=True, index=0, key="vista_ingresos")
            
            df_display = df.copy()
            df_display.insert(0, 'Fila', range(2, len(df) + 2))
            
            if vista_ing == "🃏 Tarjetas":
                # Vista de Tarjetas para Ingresos
                cols = st.columns(3)
                for idx, (_, row) in enumerate(df_display.iterrows()):
                    with cols[idx % 3]:
                        fuente = row.get('Fuente', 'Otros')
                        
                        # Colores según fuente
                        colores_fuente = {
                            'Nómina': '#00ff88',
                            'Negocio': '#00d4ff', 
                            'Inversión': '#aa00ff',
                            'Regalo': '#ff00aa',
                            'Otros': '#ffaa00'
                        }
                        border_color = colores_fuente.get(fuente, '#00ff88')
                        
                        fecha_str = str(row.get('Fecha', ''))[:10] if row.get('Fecha') else ''
                        
                        st.markdown(f"""
                        <div style="
                            background: #111;
                            border: 2px solid {border_color};
                            border-radius: 12px;
                            padding: 16px;
                            margin-bottom: 12px;
                            box-shadow: 0 0 15px {border_color}33;
                        ">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <span style="background: {border_color}22; color: {border_color}; padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600;">
                                    {fuente}
                                </span>
                                <span style="color: #666; font-size: 0.8rem;">Fila {row.get('Fila', '')}</span>
                            </div>
                            <h4 style="margin: 8px 0; color: #fff;">{row.get('Concepto', 'Sin concepto')[:35]}</h4>
                            <p style="font-size: 1.5rem; font-weight: 700; color: {border_color}; margin: 4px 0;">
                                +{formatear_moneda(row.get('Monto', 0), row.get('Divisa', 'COP'))}
                            </p>
                            <small style="color: #666;">📅 {fecha_str}</small>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.divider()
            
            cols_display = ['Fila', 'Fecha', 'Concepto', 'Monto', 'Divisa', 'Fuente', 'Recurrencia']
            cols_existentes = [c for c in cols_display if c in df_display.columns]
            
            st.markdown("**Acciones:**")
            
            col_select, col_edit, col_delete = st.columns([2, 1, 1])
            
            with col_select:
                filas_disponibles = df_display['Fila'].tolist()
                if filas_disponibles:
                    fila_seleccionada = st.selectbox(
                        "Fila #", 
                        options=filas_disponibles,
                        format_func=lambda x: f"Fila {x}: {df_display[df_display['Fila']==x]['Concepto'].values[0] if len(df_display[df_display['Fila']==x]) > 0 else 'N/A'}",
                        key="selector_fila_ingreso"
                    )
                else:
                    fila_seleccionada = None
            
            with col_edit:
                if st.button("✏️ Editar", use_container_width=True, key="btn_editar_ingreso") and fila_seleccionada:
                    st.session_state['editar_fila_ingreso'] = fila_seleccionada
                    st.session_state['datos_fila_ingreso'] = df_display[df_display['Fila'] == fila_seleccionada].iloc[0].to_dict()
            
            with col_delete:
                if st.button("🗑️ Eliminar", use_container_width=True, type="secondary", key="btn_eliminar_ingreso") and fila_seleccionada:
                    st.session_state['eliminar_fila_ingreso'] = fila_seleccionada
            
            # Modal de Edición
            if 'editar_fila_ingreso' in st.session_state and st.session_state.get('editar_fila_ingreso'):
                fila = st.session_state['editar_fila_ingreso']
                datos = st.session_state.get('datos_fila_ingreso', {})
                
                with st.form(f"form_editar_ingreso_{fila}"):
                    st.markdown(f"### ✏️ Editando Ingreso (Fila {fila})")
                    
                    new_fecha = st.date_input("Fecha", value=pd.to_datetime(datos.get('Fecha', datetime.now())).date())
                    new_concepto = st.text_input("Concepto", value=datos.get('Concepto', ''))
                    
                    c1, c2 = st.columns(2)
                    new_divisa = c1.selectbox("Divisa", ["COP", "USD", "EUR"], 
                                              index=["COP", "USD", "EUR"].index(datos.get('Divisa', 'COP')) if datos.get('Divisa') in ["COP", "USD", "EUR"] else 0)
                    new_monto = c2.number_input("Monto", value=float(datos.get('Monto', 0)), min_value=0.0)
                    
                    new_fuente = st.selectbox("Fuente", ["Nómina", "Negocio", "Inversión", "Regalo", "Otros"],
                        index=["Nómina", "Negocio", "Inversión", "Regalo", "Otros"].index(datos.get('Fuente', 'Otros')) if datos.get('Fuente') in ["Nómina", "Negocio", "Inversión", "Regalo", "Otros"] else 4
                    )
                    
                    col_save, col_cancel = st.columns(2)
                    if col_save.form_submit_button("💾 Guardar Cambios", use_container_width=True):
                        try:
                            ws = connect_sheets("Ingresos")
                            ws.update_cell(fila, 1, str(new_fecha))
                            ws.update_cell(fila, 2, new_concepto)
                            ws.update_cell(fila, 3, new_monto)
                            ws.update_cell(fila, 4, new_divisa)
                            ws.update_cell(fila, 5, new_fuente)
                            
                            st.success("✅ Ingreso actualizado")
                            st.session_state.pop('editar_fila_ingreso', None)
                            st.session_state.pop('datos_fila_ingreso', None)
                            st.cache_data.clear()
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                    
                    if col_cancel.form_submit_button("❌ Cancelar", use_container_width=True):
                        st.session_state.pop('editar_fila_ingreso', None)
                        st.session_state.pop('datos_fila_ingreso', None)
                        st.rerun()
            
            # Modal de Eliminación
            if 'eliminar_fila_ingreso' in st.session_state and st.session_state.get('eliminar_fila_ingreso'):
                fila = st.session_state['eliminar_fila_ingreso']
                concepto_eliminar = df_display[df_display['Fila'] == fila]['Concepto'].values[0] if len(df_display[df_display['Fila'] == fila]) > 0 else 'este registro'
                
                st.warning(f"⚠️ ¿Eliminar **{concepto_eliminar}** (Fila {fila})?")
                
                col_confirm, col_cancel = st.columns(2)
                if col_confirm.button("🗑️ Confirmar", use_container_width=True, type="primary", key="confirm_del_ing"):
                    try:
                        ws = connect_sheets("Ingresos")
                        ws.delete_rows(fila)
                        st.success("✅ Eliminado")
                        st.session_state.pop('eliminar_fila_ingreso', None)
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                
                if col_cancel.button("❌ Cancelar", use_container_width=True, key="cancel_del_ing"):
                    st.session_state.pop('eliminar_fila_ingreso', None)
                    st.rerun()
            
            # Tabla solo si está seleccionada
            if vista_ing == "📋 Tabla":
                st.dataframe(df_display[cols_existentes], use_container_width=True, height=400)
        else:
            st.info("ℹ️ No hay ingresos registrados. Pulsa el botón para agregar uno.")
            
    except Exception as e:
        st.error(f"Error cargando hoja de Ingresos: {e}")
@st.dialog("🤝 Registrar Deuda / Préstamo")
def dialog_deuda():
    tipo_operacion = st.selectbox("Tipo", ["📥 Me Deben", "📤 Yo Debo"], key="modal_deuda_tipo")
    
    with st.form("form_deudas_modal"):
        persona = st.text_input("Persona / Entidad", placeholder="¿Quién?")
        concepto = st.text_input("Concepto", placeholder="¿Por qué?")
        
        c1, c2 = st.columns(2)
        divisa = c1.selectbox("Divisa", ["COP", "USD", "EUR"], key="modal_dd_div")
        monto = c2.number_input("Monto", min_value=0.0, step=10000.0)
        
        fecha_limite = st.date_input("Vence", key="modal_dd_limite")
        comentario = st.text_area("Notas", height=1)
        alerta = st.checkbox("🔔 Alerta", value=True)
        
        if st.form_submit_button("💾 Guardar", use_container_width=True):
            if persona and monto > 0:
                try:
                    tipo_db = "ME_DEBEN" if "Me Deben" in tipo_operacion else "YO_DEBO"
                    id_unico = f"{tipo_db[:2]}_{int(pd.Timestamp.now().timestamp())}"
                    
                    sh = connect_sheets("Deudas")
                    sh.append_row([
                        id_unico, 
                        str(datetime.now().date()), 
                        tipo_db, 
                        persona, 
                        concepto, 
                        monto, 
                        divisa, 
                        0, 
                        "PENDIENTE", 
                        str(fecha_limite),
                        comentario,
                        "SÍ" if alerta else "NO"
                    ])
                    st.toast("✅ Registro exitoso")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Completa quién y cuánto.")

def render_deudas():
    st.title("🤝 Control de Deudas")
    
    col_btn, _ = st.columns([1, 4])
    if col_btn.button("➕ Nueva Obligación", use_container_width=True, type="primary"):
        dialog_deuda()

    # --- Filtros ---
    with st.expander("🔍 Filtros", expanded=False):
        f1, f2, f3 = st.columns(3)
        filtro_tipo = f1.selectbox("Tipo", ["Todos", "📥 Me Deben", "📤 Yo Debo"])
        filtro_estado = f2.selectbox("Estado", ["Todos", "PENDIENTE", "PAGADO"])
        filtro_persona = f3.text_input("Buscar Persona")

    # --- Main Content: Dashboard (Full Width) ---
    try:
        sh = connect_sheets("Deudas")
        records = sh.get_all_records()
        
        if records:
            df = pd.DataFrame(records)
            
            # Aplicar filtros
            if filtro_tipo != "Todos":
                tipo_filtro = "ME_DEBEN" if "Me Deben" in filtro_tipo else "YO_DEBO"
                df = df[df['Tipo'] == tipo_filtro]
            if filtro_estado != "Todos" and 'Estado' in df.columns:
                df = df[df['Estado'] == filtro_estado]
            if filtro_persona and 'Persona' in df.columns:
                df = df[df['Persona'].str.contains(filtro_persona, case=False, na=False)]
            
            # --- KPIs ---
            k1, k2, k3 = st.columns(3)
            
            activos = df[(df['Tipo'] == 'ME_DEBEN') & (df['Estado'] == 'PENDIENTE')]['MontoOriginal'].sum() if 'MontoOriginal' in df.columns else 0
            pasivos = df[(df['Tipo'] == 'YO_DEBO') & (df['Estado'] == 'PENDIENTE')]['MontoOriginal'].sum() if 'MontoOriginal' in df.columns else 0
            balance_deudas = activos - pasivos
                
            with k1:
                st.metric("🟢 Me Deben", f"${activos:,.0f}", delta="Activos")
            with k2:
                st.metric("🔴 Yo Debo", f"${pasivos:,.0f}", delta="-Pasivos", delta_color="inverse")
            with k3:
                st.metric("📊 Balance Neto", f"${balance_deudas:,.0f}", 
                         delta="A favor" if balance_deudas >= 0 else "En contra",
                         delta_color="normal" if balance_deudas >= 0 else "inverse")
                
            # --- Gráfico ---
            if 'Tipo' in df.columns and 'MontoOriginal' in df.columns:
                deudas_tipo = df.groupby('Tipo')['MontoOriginal'].sum().reset_index()
                deudas_tipo['Tipo'] = deudas_tipo['Tipo'].map({'ME_DEBEN': 'Me Deben', 'YO_DEBO': 'Yo Debo'})
                fig_pie = px.pie(deudas_tipo, values='MontoOriginal', names='Tipo', 
                                 hole=0.4, title="Distribución de Deudas",
                                 color_discrete_map={'Me Deben': '#22c55e', 'Yo Debo': '#ef4444'})
                fig_pie.update_layout(template="plotly_dark")
                st.plotly_chart(fig_pie, use_container_width=True)
                
            st.divider()
            
            # --- Vista Tarjetas / Tabla ---
            st.subheader("📋 Detalle de Obligaciones")
            
            # Toggle vista
            vista_deuda = st.radio("Vista:", ["🃏 Tarjetas", "📋 Tabla"], horizontal=True, index=0, key="vista_deudas")
            
            df_display = df.copy()
            df_display.insert(0, 'Fila', range(2, len(df) + 2))
            
            if vista_deuda == "🃏 Tarjetas":
                # Vista de Tarjetas para Deudas
                cols = st.columns(3)
                for idx, (_, row) in enumerate(df_display.iterrows()):
                    with cols[idx % 3]:
                        tipo = row.get('Tipo', 'YO_DEBO')
                        estado = row.get('Estado', 'PENDIENTE')
                        
                        # Color según tipo
                        if tipo == 'ME_DEBEN':
                            border_color = "#00ff88"  # Verde
                            tipo_label = "📥 Me Deben"
                            signo = "+"
                        else:
                            border_color = "#ff3355"  # Rojo
                            tipo_label = "📤 Yo Debo"
                            signo = "-"
                        
                        # Estado badge
                        estado_color = "#00ff88" if estado == "PAGADO" else "#ffaa00"
                        estado_label = "✅ Pagado" if estado == "PAGADO" else "⏳ Pendiente"
                        
                        st.markdown(f"""
                        <div style="
                            background: #111;
                            border: 2px solid {border_color};
                            border-radius: 12px;
                            padding: 16px;
                            margin-bottom: 12px;
                            box-shadow: 0 0 15px {border_color}33;
                            opacity: {'0.5' if estado == 'PAGADO' else '1'};
                        ">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <span style="background: {border_color}22; color: {border_color}; padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600;">
                                    {tipo_label}
                                </span>
                                <span style="background: {estado_color}22; color: {estado_color}; padding: 4px 8px; border-radius: 12px; font-size: 0.7rem;">
                                    {estado_label}
                                </span>
                            </div>
                            <h4 style="margin: 8px 0; color: #fff;">👤 {row.get('Persona', 'Sin persona')[:25]}</h4>
                            <p style="font-size: 1.3rem; font-weight: 700; color: {border_color}; margin: 4px 0;">
                                {signo}{formatear_moneda(row.get('MontoOriginal', 0), row.get('Divisa', 'COP'))}
                            </p>
                            <small style="color: #888;">{row.get('Concepto', '')[:40]}</small>
                            <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #222;">
                                <small style="color: #666;">📅 Vence: {row.get('FechaLimite', 'N/A')} | Fila {row.get('Fila', '')}</small>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.divider()
            
            cols_display = ['Fila', 'Tipo', 'Persona', 'Concepto', 'MontoOriginal', 'Divisa', 'Estado', 'FechaLimite']
            cols_existentes = [c for c in cols_display if c in df_display.columns]
            
            st.markdown("**Acciones:**")
            
            col_select, col_edit, col_status, col_delete = st.columns([2, 1, 1, 1])
            
            with col_select:
                filas_disponibles = df_display['Fila'].tolist()
                if filas_disponibles:
                    fila_seleccionada = st.selectbox(
                        "Fila #", 
                        options=filas_disponibles,
                        format_func=lambda x: f"Fila {x}: {df_display[df_display['Fila']==x]['Persona'].values[0] if len(df_display[df_display['Fila']==x]) > 0 else 'N/A'}",
                        key="selector_fila_deuda"
                    )
                else:
                    fila_seleccionada = None
            
            with col_edit:
                if st.button("✏️ Editar", use_container_width=True, key="btn_editar_deuda") and fila_seleccionada:
                    st.session_state['editar_fila_deuda'] = fila_seleccionada
                    st.session_state['datos_fila_deuda'] = df_display[df_display['Fila'] == fila_seleccionada].iloc[0].to_dict()
            
            with col_status:
                if st.button("✅ Pagado", use_container_width=True, key="btn_pagar_deuda") and fila_seleccionada:
                    try:
                        ws = connect_sheets("Deudas")
                        # Columna Estado es la 9 (índice base 1)
                        ws.update_cell(fila_seleccionada, 9, "PAGADO")
                        st.success("✅ Marcado como PAGADO")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            
            with col_delete:
                if st.button("🗑️ Eliminar", use_container_width=True, type="secondary", key="btn_eliminar_deuda") and fila_seleccionada:
                    st.session_state['eliminar_fila_deuda'] = fila_seleccionada
            
            # Modal de Edición
            if 'editar_fila_deuda' in st.session_state and st.session_state.get('editar_fila_deuda'):
                fila = st.session_state['editar_fila_deuda']
                datos = st.session_state.get('datos_fila_deuda', {})
                
                with st.form(f"form_editar_deuda_{fila}"):
                    st.markdown(f"### ✏️ Editando Deuda (Fila {fila})")
                    
                    new_persona = st.text_input("Persona / Entidad", value=datos.get('Persona', ''))
                    new_concepto = st.text_input("Concepto", value=datos.get('Concepto', ''))
                    
                    c1, c2 = st.columns(2)
                    new_divisa = c1.selectbox("Divisa", ["COP", "USD", "EUR"], 
                                              index=["COP", "USD", "EUR"].index(datos.get('Divisa', 'COP')) if datos.get('Divisa') in ["COP", "USD", "EUR"] else 0)
                    new_monto = c2.number_input("Monto", value=float(datos.get('MontoOriginal', 0)), min_value=0.0)
                    
                    new_estado = st.selectbox("Estado", ["PENDIENTE", "PAGADO"],
                        index=["PENDIENTE", "PAGADO"].index(datos.get('Estado', 'PENDIENTE')) if datos.get('Estado') in ["PENDIENTE", "PAGADO"] else 0
                    )
                    
                    col_save, col_cancel = st.columns(2)
                    if col_save.form_submit_button("💾 Guardar Cambios", use_container_width=True):
                        try:
                            ws = connect_sheets("Deudas")
                            ws.update_cell(fila, 4, new_persona)      # Persona
                            ws.update_cell(fila, 5, new_concepto)     # Concepto
                            ws.update_cell(fila, 6, new_monto)        # MontoOriginal
                            ws.update_cell(fila, 7, new_divisa)       # Divisa
                            ws.update_cell(fila, 9, new_estado)       # Estado
                            
                            st.success("✅ Deuda actualizada")
                            st.session_state.pop('editar_fila_deuda', None)
                            st.session_state.pop('datos_fila_deuda', None)
                            st.cache_data.clear()
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                    
                    if col_cancel.form_submit_button("❌ Cancelar", use_container_width=True):
                        st.session_state.pop('editar_fila_deuda', None)
                        st.session_state.pop('datos_fila_deuda', None)
                        st.rerun()
            
            # Modal de Eliminación
            if 'eliminar_fila_deuda' in st.session_state and st.session_state.get('eliminar_fila_deuda'):
                fila = st.session_state['eliminar_fila_deuda']
                persona_eliminar = df_display[df_display['Fila'] == fila]['Persona'].values[0] if len(df_display[df_display['Fila'] == fila]) > 0 else 'este registro'
                
                st.warning(f"⚠️ ¿Eliminar deuda con **{persona_eliminar}** (Fila {fila})?")
                
                col_confirm, col_cancel = st.columns(2)
                if col_confirm.button("🗑️ Confirmar", use_container_width=True, type="primary", key="confirm_del_deuda"):
                    try:
                        ws = connect_sheets("Deudas")
                        ws.delete_rows(fila)
                        st.success("✅ Eliminado")
                        st.session_state.pop('eliminar_fila_deuda', None)
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                
                if col_cancel.button("❌ Cancelar", use_container_width=True, key="cancel_del_deuda"):
                    st.session_state.pop('eliminar_fila_deuda', None)
                    st.rerun()
            
            # Tabla solo si está seleccionada
            if vista_deuda == "📋 Tabla":
                st.dataframe(df_display[cols_existentes], use_container_width=True, height=400)
                    
        else:
            st.info("ℹ️ No hay deudas registradas. Usa el botón superior.")
            
    except Exception as e:
        st.error(f"Error cargando Deudas: {e}")

# ============================================================
# RENDER INICIO - DASHBOARD PREMIUM
# ============================================================
def render_inicio():
    """Dashboard principal con vista estilo premium."""
    
    # Cargar configuración de presupuesto desde Google Sheets
    if 'presupuesto_cargado' not in st.session_state:
        try:
            sh_config = connect_sheets("Configuracion")
            records = sh_config.get_all_records()
            if records:
                config = records[0]  # Primera fila tiene la config
                st.session_state.presupuesto_mensual = float(config.get('PresupuestoMensual', 1000000))
                st.session_state.meta_ahorro = float(config.get('MetaAhorro', 200000))
            else:
                st.session_state.presupuesto_mensual = 1000000
                st.session_state.meta_ahorro = 200000
        except:
            st.session_state.presupuesto_mensual = 1000000
            st.session_state.meta_ahorro = 200000
        st.session_state.presupuesto_cargado = True
    
    try:
        # Cargar datos
        sh_gastos = connect_sheets(0)
        sh_ingresos = connect_sheets("Ingresos")
        sh_deudas = connect_sheets("Deudas")
        
        df_gastos = pd.DataFrame(sh_gastos.get_all_records())
        df_ingresos = pd.DataFrame(sh_ingresos.get_all_records())
        df_deudas = pd.DataFrame(sh_deudas.get_all_records())
        
        # Calcular totales
        total_ingresos = pd.to_numeric(df_ingresos['Monto'], errors='coerce').sum() if not df_ingresos.empty and 'Monto' in df_ingresos.columns else 0
        total_gastos = pd.to_numeric(df_gastos['Monto'], errors='coerce').sum() if not df_gastos.empty and 'Monto' in df_gastos.columns else 0
        disponible = total_ingresos - total_gastos
        
        # Ahorro (si existe hoja Bolsillos)
        try:
            sh_bolsillos = connect_sheets("Bolsillos")
            df_bolsillos = pd.DataFrame(sh_bolsillos.get_all_records())
            total_ahorrado = pd.to_numeric(df_bolsillos['Ahorrado'], errors='coerce').sum() if not df_bolsillos.empty and 'Ahorrado' in df_bolsillos.columns else 0
        except:
            total_ahorrado = 0
        
        patrimonio_total = disponible + total_ahorrado
        
        # ============================================================
        # TARJETA PATRIMONIO PRINCIPAL
        # ============================================================
        # Determinar estado de gasto
        presupuesto = st.session_state.presupuesto_mensual
        porcentaje_gastado = (total_gastos / presupuesto * 100) if presupuesto > 0 else 0
        
        if porcentaje_gastado > 100:
            estado_badge = '<span class="badge-alert danger">🔥 Excedido</span>'
        elif porcentaje_gastado > 80:
            estado_badge = '<span class="badge-alert warning">⚠️ Gastando Más</span>'
        else:
            estado_badge = '<span class="badge-alert success">✅ En Control</span>'
        
        # Formatear valores
        patrimonio_fmt = f"${patrimonio_total:,.0f}"
        disponible_fmt = f"${disponible:,.0f}"
        ahorrado_fmt = f"${total_ahorrado:,.0f}"
        restante_fmt = f"${presupuesto - total_gastos:,.0f}"
        ingresos_fmt = f"${total_ingresos:,.0f}"
        gastos_fmt = f"${total_gastos:,.0f}"
        
        st.markdown(f"""
        <div class="patrimonio-card animate-slide-up">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
                <div>
                    <p style="margin: 0; font-size: 0.85rem; opacity: 0.7; font-weight: 500;">Patrimonio Total 👁</p>
                    <h1 style="margin: 8px 0 0 0; font-size: 2.8rem; font-weight: 800; color: #000;">
                        {patrimonio_fmt}
                    </h1>
                </div>
                {estado_badge}
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
                <div style="background: rgba(0,0,0,0.1); padding: 16px; border-radius: 16px;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                        <span style="font-size: 1.2rem;">💳</span>
                        <span style="font-size: 0.8rem; opacity: 0.7;">Disponible</span>
                    </div>
                    <p style="margin: 0; font-size: 1.4rem; font-weight: 700;">{disponible_fmt}</p>
                </div>
                <div style="background: rgba(0,0,0,0.1); padding: 16px; border-radius: 16px;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                        <span style="font-size: 1.2rem;">🐷</span>
                        <span style="font-size: 0.8rem; opacity: 0.7;">Ahorrado</span>
                    </div>
                    <p style="margin: 0; font-size: 1.4rem; font-weight: 700; color: #22c55e;">{ahorrado_fmt}</p>
                </div>
            </div>
            
            <div style="display: flex; justify-content: space-between; margin-top: 20px; padding-top: 16px; border-top: 1px solid rgba(0,0,0,0.1);">
                <div>
                    <span style="font-size: 0.75rem; opacity: 0.6;">restante</span>
                    <p style="margin: 0; font-size: 1.1rem; font-weight: 600;">{restante_fmt}</p>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 0.75rem; opacity: 0.6;">Ingresos del Período</span>
                    <p style="margin: 0; font-size: 1.1rem; font-weight: 600; color: #22c55e;">↑ {ingresos_fmt}</p>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 0.75rem; opacity: 0.6;">Gastos del Período</span>
                    <p style="margin: 0; font-size: 1.1rem; font-weight: 600; color: #ef4444;">↓ {gastos_fmt}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # ============================================================
        # ACCIONES RÁPIDAS
        # ============================================================
        st.markdown("### Acciones Rápidas")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("➖\nGasto", key="quick_gasto", use_container_width=True):
                dialog_gasto()
        with col2:
            if st.button("➕\nIngreso", key="quick_ingreso", use_container_width=True):
                dialog_ingreso()
        with col3:
            if st.button("↔️\nTransfer", key="quick_transfer", use_container_width=True):
                dialog_transferencia()
        with col4:
            if st.button("🏦\nCuentas", key="quick_cuentas", use_container_width=True):
                st.session_state.navegacion_principal = "🏦 Cuentas"
                st.rerun()
        with col5:
            if st.button("📁\nCategorías", key="quick_cats", use_container_width=True):
                dialog_categorias()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # ============================================================
        # RESUMEN FINANCIERO RÁPIDO
        # ============================================================
        st.markdown("### Resumen Financiero Rápido")
        
        col_prom, col_pres = st.columns(2)
        
        # Calcular promedio diario
        dias_mes = datetime.now().day
        promedio_diario = total_gastos / dias_mes if dias_mes > 0 else 0
        meta_diaria = presupuesto / 30  # Asumiendo mes de 30 días
        
        with col_prom:
            st.markdown(f"""
            <div class="glass-card">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <div class="summary-icon green">📈</div>
                    <span style="color: #a0a0a0; font-size: 0.85rem;">Promedio Diario</span>
                </div>
                <h2 style="margin: 0; color: #fff; font-size: 1.8rem;">${promedio_diario:,.0f}</h2>
                <small style="color: #666;">{dias_mes} días transcurridos</small>
                <div style="margin-top: 12px; padding: 8px 12px; background: rgba(200,255,0,0.1); border-radius: 8px; display: inline-block;">
                    <span style="color: #c8ff00; font-size: 0.8rem;">Meta: ${meta_diaria:,.0f}/día</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_pres:
            restante = presupuesto - total_gastos
            porcentaje_usado = min(porcentaje_gastado, 100)
            
            # Determinar color de la barra
            if porcentaje_gastado > 90:
                bar_class = "danger"
            elif porcentaje_gastado > 70:
                bar_class = "warning"
            else:
                bar_class = ""
            
            st.markdown(f"""
            <div class="glass-card">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <div class="summary-icon blue">✅</div>
                    <span style="color: #a0a0a0; font-size: 0.85rem;">restante</span>
                </div>
                <h2 style="margin: 0; color: #fff; font-size: 1.8rem;">${restante:,.0f}</h2>
                <small style="color: #666;">Presupuesto</small>
                <div class="progress-container" style="margin-top: 12px;">
                    <div class="progress-bar {bar_class}" style="width: {porcentaje_usado}%;"></div>
                </div>
                <div style="margin-top: 8px;">
                    <span style="color: {'#22c55e' if porcentaje_gastado < 50 else '#f59e0b' if porcentaje_gastado < 80 else '#ef4444'}; font-size: 0.8rem;">
                        {porcentaje_gastado:.0f}% Usado
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # ============================================================
        # ÚLTIMOS MOVIMIENTOS
        # ============================================================
        st.markdown("### 📋 Últimos Movimientos")
        
        movimientos = []
        
        if not df_gastos.empty:
            for _, row in df_gastos.tail(5).iterrows():
                movimientos.append({
                    'Fecha': row.get('Fecha', ''),
                    'Tipo': '💸 Gasto',
                    'Concepto': row.get('Concepto', ''),
                    'Monto': f"-${row.get('Monto', 0):,.0f}",
                    'Divisa': row.get('Divisa', 'COP')
                })
        
        if not df_ingresos.empty:
            for _, row in df_ingresos.tail(5).iterrows():
                movimientos.append({
                    'Fecha': row.get('Fecha', ''),
                    'Tipo': '💰 Ingreso',
                    'Concepto': row.get('Concepto', ''),
                    'Monto': f"+${row.get('Monto', 0):,.0f}",
                    'Divisa': row.get('Divisa', 'COP')
                })
        
        if movimientos:
            df_mov = pd.DataFrame(movimientos)
            df_mov = df_mov.sort_values('Fecha', ascending=False).head(10)
            st.dataframe(df_mov, use_container_width=True, hide_index=True)
        else:
            st.info("No hay movimientos registrados aún.")
        
        # ============================================================
        # CONFIGURACIÓN DE PRESUPUESTO (Colapsado)
        # ============================================================
        with st.expander("⚙️ Configurar Presupuesto y Metas"):
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                nuevo_presupuesto = st.number_input(
                    "Presupuesto Mensual (COP)", 
                    min_value=0.0, 
                    value=float(st.session_state.presupuesto_mensual),
                    step=50000.0,
                    key="input_presupuesto"
                )
            with col_p2:
                nueva_meta = st.number_input(
                    "Meta de Ahorro Mensual (COP)", 
                    min_value=0.0, 
                    value=float(st.session_state.meta_ahorro),
                    step=10000.0,
                    key="input_meta_ahorro"
                )
            
            if st.button("💾 Guardar Configuración", key="save_config"):
                st.session_state.presupuesto_mensual = nuevo_presupuesto
                st.session_state.meta_ahorro = nueva_meta
                
                # Guardar en Google Sheets
                try:
                    try:
                        sh_config = connect_sheets("Configuracion")
                    except:
                        # Crear hoja si no existe
                        GOOGLE_SHEET_NAME = obtener_secreto("GOOGLE_SHEET_NAME")
                        gc = gspread.service_account(filename="credentials.json")
                        spreadsheet = gc.open(GOOGLE_SHEET_NAME)
                        sh_config = spreadsheet.add_worksheet(title="Configuracion", rows=10, cols=10)
                        sh_config.append_row(["PresupuestoMensual", "MetaAhorro", "FechaActualizacion"])
                    
                    # Buscar si ya existe configuración
                    all_data = sh_config.get_all_values()
                    if len(all_data) > 1:
                        # Actualizar fila existente
                        sh_config.update_cell(2, 1, nuevo_presupuesto)
                        sh_config.update_cell(2, 2, nueva_meta)
                        sh_config.update_cell(2, 3, str(datetime.now()))
                    else:
                        # Crear nueva fila
                        sh_config.append_row([nuevo_presupuesto, nueva_meta, str(datetime.now())])
                    
                    st.cache_data.clear()
                    st.success("✅ Configuración guardada en la nube")
                except Exception as e:
                    st.warning(f"Guardado localmente. Error al sincronizar: {e}")
                
                st.rerun()
                
    except Exception as e:
        st.error(f"Error cargando dashboard: {e}")
        import traceback
        st.code(traceback.format_exc())

# ============================================================
# RENDER CUENTAS - GESTIÓN DE CUENTAS BANCARIAS
# ============================================================
def render_cuentas():
    """Gestión de cuentas bancarias y billeteras."""
    
    # Header con imagen
    col_img, col_title = st.columns([1, 4])
    with col_img:
        try:
            st.image("assets/icon_wallet.png", width=120)
        except:
            pass
    with col_title:
        st.title("🏦 Gestión de Cuentas")
        st.caption("Administra tus cuentas bancarias y billeteras")
    
    # Botón para agregar
    col_btn, _ = st.columns([1, 4])
    if col_btn.button("➕ Añadir cuenta", use_container_width=True, type="primary"):
        dialog_cuenta()
    
    try:
        # Intentar cargar hoja Cuentas
        try:
            sh = connect_sheets("Cuentas")
            records = sh.get_all_records()
        except:
            # Si no existe, mostrar ejemplo y opción de crear
            st.info("📋 No existe la hoja 'Cuentas'. Crea cuentas para comenzar.")
            records = []
        
        if records:
            df = pd.DataFrame(records)
            
            # Calcular totales
            saldo_total = pd.to_numeric(df['Saldo'], errors='coerce').sum() if 'Saldo' in df.columns else 0
            
            # Contar por tipo
            tipos = df['Tipo'].value_counts().to_dict() if 'Tipo' in df.columns else {}
            
            # Tarjeta de resumen
            st.markdown(f"""
            <div class="patrimonio-card" style="margin-bottom: 24px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <p style="margin: 0; font-size: 0.85rem; opacity: 0.7;">Saldo Total</p>
                        <h1 style="margin: 8px 0 0 0; font-size: 2.5rem; font-weight: 800; color: #000;">
                            ${saldo_total:,.0f}
                        </h1>
                    </div>
                    <div style="text-align: right;">
                        <span style="background: rgba(0,0,0,0.15); padding: 6px 12px; border-radius: 20px; font-size: 0.8rem;">
                            {len(records)} cuentas
                        </span>
                    </div>
                </div>
                <div style="display: flex; gap: 16px; margin-top: 20px;">
                    <div>
                        <span style="font-size: 0.75rem; opacity: 0.6;">📊 Balance del Período</span>
                        <p style="margin: 0; font-weight: 600;">${saldo_total:,.0f}</p>
                    </div>
                    <div>
                        <span style="font-size: 0.75rem; opacity: 0.6;">📁 Portafolio</span>
                        <p style="margin: 0; font-weight: 600;">{len(tipos)} Tipos</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Filtros
            st.markdown("**Cuentas** - Gestiona tus cuentas")
            
            col_filter, _ = st.columns([2, 3])
            with col_filter:
                filtro_tipo = st.selectbox("Filtrar:", ["Todos"] + list(tipos.keys()), key="filtro_cuenta_tipo")
            
            # Aplicar filtro
            df_display = df.copy()
            if filtro_tipo != "Todos":
                df_display = df_display[df_display['Tipo'] == filtro_tipo]
            
            # Mostrar cuentas como tarjetas
            cols = st.columns(2)
            iconos = {
                "Efectivo": "💵", "Ahorros": "🐷", "Corriente": "🏦", 
                "Crédito": "💳", "Inversión": "📈", "Otro": "💰"
            }
            colores = {
                "Efectivo": "#22c55e", "Ahorros": "#c8ff00", "Corriente": "#00d4ff",
                "Crédito": "#ff3366", "Inversión": "#a855f7", "Otro": "#888"
            }
            
            for idx, (_, row) in enumerate(df_display.iterrows()):
                with cols[idx % 2]:
                    tipo = row.get('Tipo', 'Otro')
                    icono = iconos.get(tipo, '💰')
                    color = colores.get(tipo, '#888')
                    
                    st.markdown(f"""
                    <div class="glass-card" style="margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="display: flex; align-items: center; gap: 12px;">
                                <div style="width: 48px; height: 48px; background: {color}22; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem;">
                                    {icono}
                                </div>
                                <div>
                                    <h4 style="margin: 0; color: #fff;">{row.get('Nombre', 'Sin nombre')}</h4>
                                    <small style="color: #666;">{tipo}</small>
                                </div>
                            </div>
                            <div style="text-align: right;">
                                <p style="margin: 0; font-size: 1.3rem; font-weight: 700; color: {color};">
                                    ${row.get('Saldo', 0):,.0f}
                                </p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="glass-card" style="text-align: center; padding: 40px;">
                <p style="font-size: 3rem; margin: 0;">🏦</p>
                <h3 style="color: #fff; margin: 16px 0 8px 0;">Sin cuentas registradas</h3>
                <p style="color: #666;">Añade tu primera cuenta para comenzar a gestionar tus finanzas.</p>
            </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Error cargando cuentas: {e}")

@st.dialog("🏦 Añadir Nueva Cuenta")
def dialog_cuenta():
    with st.form("form_cuenta_modal"):
        nombre = st.text_input("Nombre de la cuenta", placeholder="Ej: Nubank, Efectivo...")
        
        c1, c2 = st.columns(2)
        tipo = c1.selectbox("Tipo", ["Efectivo", "Ahorros", "Corriente", "Crédito", "Inversión", "Otro"])
        saldo = c2.number_input("Saldo inicial", min_value=0.0, step=10000.0)
        
        divisa = st.selectbox("Divisa", ["COP", "USD", "EUR"])
        
        if st.form_submit_button("💾 Guardar", use_container_width=True):
            if nombre:
                try:
                    # Intentar conectar o crear hoja
                    try:
                        sh = connect_sheets("Cuentas")
                    except:
                        # Crear hoja si no existe
                        GOOGLE_SHEET_NAME = obtener_secreto("GOOGLE_SHEET_NAME")
                        gc = gspread.service_account(filename="credentials.json")
                        spreadsheet = gc.open(GOOGLE_SHEET_NAME)
                        sh = spreadsheet.add_worksheet(title="Cuentas", rows=100, cols=10)
                        sh.append_row(["ID", "Nombre", "Tipo", "Saldo", "Divisa", "Icono", "Color", "Activa"])
                    
                    # Agregar cuenta
                    id_cuenta = f"CTA_{int(pd.Timestamp.now().timestamp())}"
                    sh.append_row([id_cuenta, nombre, tipo, saldo, divisa, "", "", "SÍ"])
                    
                    st.toast(f"✅ Cuenta '{nombre}' creada")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Ingresa un nombre para la cuenta")

# ============================================================
# TRANSFERENCIAS ENTRE CUENTAS
# ============================================================
@st.dialog("↔️ Transferir entre Cuentas")
def dialog_transferencia():
    """Diálogo para transferir dinero entre cuentas."""
    
    # Cargar cuentas disponibles
    try:
        sh = connect_sheets("Cuentas")
        records = sh.get_all_records()
        cuentas = {r.get('Nombre', f"Cuenta {i}"): r for i, r in enumerate(records)}
    except:
        cuentas = {}
    
    if len(cuentas) < 2:
        st.warning("⚠️ Necesitas al menos 2 cuentas para hacer transferencias.")
        st.info("Ve a 🏦 Cuentas para crear más cuentas.")
        return
    
    with st.form("form_transferencia"):
        st.markdown("### Mover dinero entre cuentas")
        
        nombres_cuentas = list(cuentas.keys())
        
        c1, c2 = st.columns(2)
        cuenta_origen = c1.selectbox("📤 Desde", nombres_cuentas, key="trans_origen")
        cuenta_destino = c2.selectbox("📥 Hacia", nombres_cuentas, key="trans_destino")
        
        monto = st.number_input("💰 Monto a transferir", min_value=0.0, step=10000.0)
        concepto = st.text_input("📝 Concepto (opcional)", placeholder="Ej: Ahorro mensual...")
        
        if st.form_submit_button("✅ Realizar Transferencia", use_container_width=True, type="primary"):
            if cuenta_origen == cuenta_destino:
                st.error("❌ La cuenta de origen y destino deben ser diferentes")
            elif monto <= 0:
                st.warning("⚠️ El monto debe ser mayor a 0")
            else:
                try:
                    sh = connect_sheets("Cuentas")
                    all_data = sh.get_all_values()
                    headers = all_data[0]
                    
                    # Encontrar índices de columnas
                    nombre_idx = headers.index("Nombre")
                    saldo_idx = headers.index("Saldo")
                    
                    # Buscar y actualizar cuentas
                    for i, row in enumerate(all_data[1:], start=2):  # +2 porque empieza en fila 2
                        if row[nombre_idx] == cuenta_origen:
                            saldo_actual = float(row[saldo_idx]) if row[saldo_idx] else 0
                            nuevo_saldo = saldo_actual - monto
                            sh.update_cell(i, saldo_idx + 1, nuevo_saldo)  # +1 porque Sheets es 1-indexed
                        elif row[nombre_idx] == cuenta_destino:
                            saldo_actual = float(row[saldo_idx]) if row[saldo_idx] else 0
                            nuevo_saldo = saldo_actual + monto
                            sh.update_cell(i, saldo_idx + 1, nuevo_saldo)
                    
                    # Registrar transferencia en hoja Transferencias
                    try:
                        sh_trans = connect_sheets("Transferencias")
                    except:
                        GOOGLE_SHEET_NAME = obtener_secreto("GOOGLE_SHEET_NAME")
                        gc = gspread.service_account(filename="credentials.json")
                        spreadsheet = gc.open(GOOGLE_SHEET_NAME)
                        sh_trans = spreadsheet.add_worksheet(title="Transferencias", rows=100, cols=10)
                        sh_trans.append_row(["ID", "Fecha", "Origen", "Destino", "Monto", "Concepto"])
                    
                    id_trans = f"TRF_{int(pd.Timestamp.now().timestamp())}"
                    sh_trans.append_row([id_trans, str(datetime.now().date()), cuenta_origen, cuenta_destino, monto, concepto])
                    
                    st.toast(f"✅ Transferencia de ${monto:,.0f} realizada")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error: {e}")

# ============================================================
# GESTIÓN DE CATEGORÍAS
# ============================================================
@st.dialog("📁 Gestión de Categorías")
def dialog_categorias():
    """Diálogo para gestionar categorías personalizadas."""
    
    # Cargar categorías existentes
    try:
        sh = connect_sheets("Categorias")
        records = sh.get_all_records()
    except:
        records = []
    
    # Categorías por defecto
    categorias_default = [
        {"nombre": "Alimentación", "icono": "🍔", "color": "#22c55e"},
        {"nombre": "Transporte", "icono": "🚗", "color": "#3b82f6"},
        {"nombre": "Entretenimiento", "icono": "🎮", "color": "#a855f7"},
        {"nombre": "Salud", "icono": "💊", "color": "#ef4444"},
        {"nombre": "Educación", "icono": "📚", "color": "#f59e0b"},
        {"nombre": "Hogar", "icono": "🏠", "color": "#06b6d4"},
        {"nombre": "Ropa", "icono": "👕", "color": "#ec4899"},
        {"nombre": "Servicios", "icono": "📱", "color": "#8b5cf6"},
    ]
    
    if not records:
        records = categorias_default
    
    tab1, tab2 = st.tabs(["📋 Ver Categorías", "➕ Agregar Nueva"])
    
    with tab1:
        st.markdown("### Categorías Actuales")
        for cat in records:
            nombre = cat.get('nombre', cat.get('Nombre', 'Sin nombre'))
            icono = cat.get('icono', cat.get('Icono', '📁'))
            color = cat.get('color', cat.get('Color', '#888'))
            
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 12px; padding: 12px; 
                        background: {color}22; border-radius: 12px; margin-bottom: 8px;
                        border-left: 4px solid {color};">
                <span style="font-size: 1.5rem;">{icono}</span>
                <span style="font-weight: 600; color: #fff;">{nombre}</span>
            </div>
            """, unsafe_allow_html=True)
    
    with tab2:
        with st.form("form_nueva_categoria"):
            st.markdown("### Nueva Categoría")
            
            nombre_cat = st.text_input("Nombre", placeholder="Ej: Mascotas, Suscripciones...")
            
            c1, c2 = st.columns(2)
            icono_cat = c1.selectbox("Icono", ["📁", "🛒", "🎁", "💪", "🐕", "✈️", "💡", "🎬", "📦", "🔧"])
            color_cat = c2.color_picker("Color", "#c8ff00")
            
            if st.form_submit_button("💾 Guardar Categoría", use_container_width=True):
                if nombre_cat:
                    try:
                        try:
                            sh = connect_sheets("Categorias")
                        except:
                            GOOGLE_SHEET_NAME = obtener_secreto("GOOGLE_SHEET_NAME")
                            gc = gspread.service_account(filename="credentials.json")
                            spreadsheet = gc.open(GOOGLE_SHEET_NAME)
                            sh = spreadsheet.add_worksheet(title="Categorias", rows=100, cols=10)
                            sh.append_row(["ID", "Nombre", "Icono", "Color", "Tipo"])
                            # Agregar categorías por defecto
                            for cat_def in categorias_default:
                                sh.append_row([f"CAT_{categorias_default.index(cat_def)}", 
                                              cat_def['nombre'], cat_def['icono'], cat_def['color'], "Gasto"])
                        
                        id_cat = f"CAT_{int(pd.Timestamp.now().timestamp())}"
                        sh.append_row([id_cat, nombre_cat, icono_cat, color_cat, "Gasto"])
                        
                        st.toast(f"✅ Categoría '{nombre_cat}' creada")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Ingresa un nombre para la categoría")

# ============================================================
# RENDER BOLSILLOS - METAS DE AHORRO
# ============================================================
def render_bolsillos():
    """Gestión de bolsillos de ahorro con metas."""
    
    # Header con imagen
    col_img, col_title = st.columns([1, 4])
    with col_img:
        try:
            st.image("assets/icon_savings.png", width=120)
        except:
            pass
    with col_title:
        st.title("🐷 Bolsillos de Ahorro")
        st.caption("Ahorra para tus metas y sueños")
    
    # Botón para crear
    col_btn, _ = st.columns([1, 4])
    if col_btn.button("➕ Crear Bolsillo", use_container_width=True, type="primary"):
        dialog_bolsillo()
    
    try:
        # Intentar cargar hoja Bolsillos
        try:
            sh = connect_sheets("Bolsillos")
            records = sh.get_all_records()
        except:
            records = []
        
        # Calcular total ahorrado
        total_ahorrado = sum(pd.to_numeric([r.get('Ahorrado', 0) for r in records], errors='coerce')) if records else 0
        
        # Header con total
        st.markdown(f"""
        <div style="text-align: center; padding: 20px 0;">
            <p style="color: #666; font-size: 0.9rem; margin: 0;">Total Ahorrado</p>
            <h1 style="color: #c8ff00; font-size: 2.5rem; margin: 8px 0; font-weight: 800;">${total_ahorrado:,.0f}</h1>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"**Tus Bolsillos** - {len(records)} bolsillo(s)")
        
        if records:
            df = pd.DataFrame(records)
            
            # Mostrar bolsillos
            cols = st.columns(3)
            iconos_bolsillo = {"Casa": "🏠", "Viaje": "✈️", "Auto": "🚗", "Educación": "📚", "Emergencia": "🆘", "Otro": "💰"}
            
            for idx, (_, row) in enumerate(df.iterrows()):
                with cols[idx % 3]:
                    nombre = row.get('Nombre', 'Sin nombre')
                    meta = float(row.get('Meta', 0))
                    ahorrado = float(row.get('Ahorrado', 0))
                    progreso = (ahorrado / meta * 100) if meta > 0 else 0
                    icono = iconos_bolsillo.get(row.get('Icono', 'Otro'), '💰')
                    
                    # Color según progreso
                    if progreso >= 100:
                        color = "#22c55e"
                    elif progreso >= 50:
                        color = "#c8ff00"
                    else:
                        color = "#ff9500"
                    
                    st.markdown(f"""
                    <div class="glass-card" style="margin-bottom: 16px; text-align: center;">
                        <div style="width: 56px; height: 56px; background: {color}22; border-radius: 16px; display: flex; align-items: center; justify-content: center; font-size: 1.8rem; margin: 0 auto 12px auto;">
                            {icono}
                        </div>
                        <h4 style="margin: 0 0 4px 0; color: #fff;">{nombre}</h4>
                        <p style="margin: 0; font-size: 1.4rem; font-weight: 700; color: {color};">${ahorrado:,.0f}</p>
                        <small style="color: #666;">Ahorrado</small>
                        
                        <div class="progress-container" style="margin: 16px 0 8px 0;">
                            <div class="progress-bar" style="width: {min(progreso, 100)}%; background: linear-gradient(90deg, {color} 0%, {color}aa 100%);"></div>
                        </div>
                        <small style="color: #888;">{progreso:.0f}% de ${meta:,.0f}</small>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="glass-card" style="text-align: center; padding: 40px;">
                <p style="font-size: 3rem; margin: 0;">🐷</p>
                <h3 style="color: #fff; margin: 16px 0 8px 0;">Sin bolsillos de ahorro</h3>
                <p style="color: #666;">Crea tu primer bolsillo para empezar a ahorrar hacia tus metas.</p>
            </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Error cargando bolsillos: {e}")

@st.dialog("🐷 Crear Nuevo Bolsillo")
def dialog_bolsillo():
    with st.form("form_bolsillo_modal"):
        nombre = st.text_input("Nombre del bolsillo", placeholder="Ej: Casita, Viaje...")
        
        c1, c2 = st.columns(2)
        meta = c1.number_input("Meta de ahorro", min_value=0.0, step=50000.0)
        icono = c2.selectbox("Icono", ["Casa", "Viaje", "Auto", "Educación", "Emergencia", "Otro"])
        
        ahorrado_inicial = st.number_input("Ahorro inicial (opcional)", min_value=0.0, step=10000.0)
        
        if st.form_submit_button("💾 Crear Bolsillo", use_container_width=True):
            if nombre and meta > 0:
                try:
                    try:
                        sh = connect_sheets("Bolsillos")
                    except:
                        GOOGLE_SHEET_NAME = obtener_secreto("GOOGLE_SHEET_NAME")
                        gc = gspread.service_account(filename="credentials.json")
                        spreadsheet = gc.open(GOOGLE_SHEET_NAME)
                        sh = spreadsheet.add_worksheet(title="Bolsillos", rows=100, cols=10)
                        sh.append_row(["ID", "Nombre", "Meta", "Ahorrado", "Icono", "Color", "FechaCreacion"])
                    
                    id_bolsillo = f"BOL_{int(pd.Timestamp.now().timestamp())}"
                    sh.append_row([id_bolsillo, nombre, meta, ahorrado_inicial, icono, "#c8ff00", str(datetime.now().date())])
                    
                    st.toast(f"✅ Bolsillo '{nombre}' creado")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Ingresa nombre y meta de ahorro")

# ============================================================
# RENDER ASISTENTE IA - CHATBOT FINANCIERO
# ============================================================
def render_asistente_ia():
    """Asistente IA conversacional para finanzas."""
    
    # Header con imagen del robot
    col_img, col_title = st.columns([1, 4])
    with col_img:
        try:
            st.image("assets/icon_ai.png", width=120)
        except:
            pass
    with col_title:
        st.title("🤖 Asistente de Ge$torGasto$")
        st.caption("Tu consejero financiero con Inteligencia Artificial")
    
    # Inicializar historial de chat
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Obtener nombre de usuario
    nombre_usuario = obtener_secreto("ADMIN_USER", "Usuario")
    
    # Mensaje de bienvenida
    st.markdown(f"""
    <div style="margin-bottom: 24px;">
        <p style="color: #888; margin: 0;">Hola, {nombre_usuario}</p>
        <h2 style="color: #fff; margin: 8px 0 0 0; font-weight: 700;">¿Por dónde empezamos?</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Sugerencias rápidas
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Analizar mis gastos", use_container_width=True, key="sug_analizar"):
            st.session_state.pending_question = "Analiza mis gastos del último mes y dame recomendaciones"
    with col2:
        if st.button("➕ Añadir transacción", use_container_width=True, key="sug_add"):
            dialog_gasto()
    
    col3, col4 = st.columns(2)
    with col3:
        if st.button("📋 Revisar presupuesto", use_container_width=True, key="sug_pres"):
            st.session_state.pending_question = "¿Cómo voy con mi presupuesto este mes?"
    with col4:
        if st.button("💡 ¿Cómo puedo ahorrar más?", use_container_width=True, key="sug_ahorro"):
            st.session_state.pending_question = "Dame consejos personalizados para ahorrar más dinero"
    
    st.markdown("---")
    
    # Historial de chat
    for msg in st.session_state.chat_history:
        if msg['role'] == 'user':
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-end; margin-bottom: 12px;">
                <div style="background: #c8ff00; color: #000; padding: 12px 16px; border-radius: 16px 16px 4px 16px; max-width: 70%;">
                    {msg['content']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-start; margin-bottom: 12px;">
                <div style="background: #222; color: #fff; padding: 12px 16px; border-radius: 16px 16px 16px 4px; max-width: 70%;">
                    {msg['content']}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Procesar pregunta pendiente
    if 'pending_question' in st.session_state:
        pregunta = st.session_state.pop('pending_question')
        procesar_pregunta_ia(pregunta)
        st.rerun()
    
    # Input de chat
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_input, col_send = st.columns([5, 1])
    with col_input:
        user_input = st.text_input("Escribe tu pregunta...", key="chat_input", label_visibility="collapsed", placeholder="Añadir: cena $32")
    with col_send:
        if st.button("🎤", key="btn_send"):
            if user_input:
                procesar_pregunta_ia(user_input)
                st.rerun()

def procesar_pregunta_ia(pregunta):
    """Procesa una pregunta del usuario con IA."""
    # Agregar pregunta al historial
    st.session_state.chat_history.append({'role': 'user', 'content': pregunta})
    
    try:
        # Cargar datos para contexto completo
        sh_gastos = connect_sheets(0)
        df_gastos = pd.DataFrame(sh_gastos.get_all_records())
        
        sh_ingresos = connect_sheets("Ingresos")
        df_ingresos = pd.DataFrame(sh_ingresos.get_all_records())
        
        sh_deudas = connect_sheets("Deudas")
        df_deudas = pd.DataFrame(sh_deudas.get_all_records())
        
        total_gastos = pd.to_numeric(df_gastos['Monto'], errors='coerce').sum() if not df_gastos.empty and 'Monto' in df_gastos.columns else 0
        total_ingresos = pd.to_numeric(df_ingresos['Monto'], errors='coerce').sum() if not df_ingresos.empty and 'Monto' in df_ingresos.columns else 0
        me_deben = df_deudas[(df_deudas['Tipo'] == 'ME_DEBEN') & (df_deudas['Estado'] == 'PENDIENTE')]['MontoOriginal'].sum() if not df_deudas.empty and 'MontoOriginal' in df_deudas.columns else 0
        yo_debo = df_deudas[(df_deudas['Tipo'] == 'YO_DEBO') & (df_deudas['Estado'] == 'PENDIENTE')]['MontoOriginal'].sum() if not df_deudas.empty and 'MontoOriginal' in df_deudas.columns else 0
        
        # Configurar Gemini
        import google.generativeai as genai
        GEMINI_API_KEY = obtener_secreto("GEMINI_API_KEY")
        
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-flash-latest')
            
            # Crear prompt con contexto
            contexto = f"""
            Eres un asistente financiero personal amigable llamado Ge$torGasto$ AI.
            
            DATOS ACTUALES DEL USUARIO:
            - Ingresos Totales: ${total_ingresos:,.0f}
            - Gastos Totales: ${total_gastos:,.0f}
            - Saldo Neto: ${total_ingresos - total_gastos:,.0f}
            - Me deben (Cobros): ${me_deben:,.0f}
            - Yo debo (Deudas): ${yo_debo:,.0f}
            - Transacciones registradas: {len(df_gastos)}
            
            INSTRUCCIONES:
            - Responde siempre en español.
            - Sé breve (max 3-4 párrafos), amigable y profesional.
            - Usa emojis para hacer la conversación ligera.
            - Da consejos accionables basados en los números proporcionados.
            - Si el saldo neto es bajo, sugiere moderar gastos.
            - Si hay muchas deudas, sugiere priorizar el pago.
            
            PREGUNTA DEL USUARIO: {pregunta}
            """
            
            response = model.generate_content(contexto)
            respuesta = response.text
        else:
            respuesta = "⚠️ No tengo configurada la API de IA. Configura GEMINI_API_KEY para activar el asistente."
        
        st.session_state.chat_history.append({'role': 'assistant', 'content': respuesta})
        
    except Exception as e:
        st.session_state.chat_history.append({'role': 'assistant', 'content': f"⚠️ Error procesando: {str(e)}"})


    # ============================================================
    # RENDERIZADO DE MÓDULOS
    # ============================================================
    
    # ... (ingresos y deudas ya definidos arriba) ...

@st.dialog("💸 Registrar Nuevo Gasto")
def dialog_gasto():
    with st.form("formulario_gasto_modal"):
        fecha = st.date_input("📅 Fecha")
        concepto = st.text_input("📝 Concepto")
        
        c1, c2 = st.columns(2)
        divisa = c1.selectbox("Divisa", ["COP", "USD", "EUR"])
        monto = c2.number_input("Monto", min_value=0.0, step=100.0 if divisa == "COP" else 1.0)
        
        categoria = st.selectbox("📁 Categoría", [
            "Comida", "Transporte", "Ocio", "Servicios", 
            "Salud", "Ropa", "Educación", "Ahorro", "Otro"
        ])
        
        st.markdown("**🔄 Recurrencia**")
        recurrencia = st.selectbox("Frecuencia", [
            "Único", "Semanal", "Quincenal", "Mensual", 
            "Bimestral", "Trimestral", "Semestral", "Anual"
        ], index=0, label_visibility="collapsed")
        
        c_alert = st.checkbox("🔔 Alerta", value=True)
        
        submit = st.form_submit_button("💾 Registrar", use_container_width=True)
        
        if submit:
            # Validación completa
            es_valido, errores = validar_formulario_gasto(fecha, concepto, monto, divisa, categoria)
            
            if not es_valido:
                st.error("❌ Por favor corrige los siguientes errores:")
                for error in errores:
                    st.warning(error)
            else:
                try:
                    # Sanitizar texto antes de guardar
                    concepto_limpio = sanitizar_texto(concepto)
                    
                    # ANALISIS IA
                    score, justificacion, cat_sug, color = 3, "Manual", categoria, "#808080"
                    try:
                        from auditor import auditar_gasto
                        score, justificacion, cat_sug, color = auditar_gasto(concepto_limpio, monto, divisa)
                    except Exception as e:
                        pass  # Si falla IA, usar valores por defecto
                        
                    ws = connect_sheets(0)
                    ws.append_row([
                        str(fecha), concepto_limpio, monto, divisa, categoria,
                        "Manual", "Efectivo", "N/A", score, justificacion,
                        recurrencia, "SÍ" if c_alert else "NO"
                    ])
                    st.toast(f"✅ Gasto guardado: {concepto_limpio}")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error guardando: {e}")

def formatear_moneda(monto, divisa):
    if divisa == "COP":
        return f"${monto:,.0f} COP"
    elif divisa == "USD":
        return f"US${monto:,.2f}"
    elif divisa == "EUR":
        return f"€{monto:,.2f}"
    return f"{monto:,.2f} {divisa}"

def render_egresos():
    # ============================================================
    # BARRA DE ACCIONES PRINCIPAL
    # ============================================================
    col_add, col_audit, _ = st.columns([1, 1, 3])
    
    with col_add:
        if st.button("➕ Nuevo Gasto", use_container_width=True, type="primary"):
            dialog_gasto()
    
    with col_audit:
        if st.button("🤖 Auditar con IA", use_container_width=True):
            with st.spinner("🔍 Analizando gastos con Gemini..."):
                try:
                    from auditor import run_audit
                    stats = run_audit()
                    st.success(f"✅ Auditados: {stats['processed']} | Actualizados: {stats.get('updated', 0)}")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error en auditoría: {e}")
    
    # ============================================================
    # FILTROS (colapsados)
    # ============================================================
    with st.expander("� Filtros", expanded=False):
        f1, f2 = st.columns(2)
        filtro_mes = f1.date_input("📅 Rango", [])
        filtro_cat = f2.multiselect("📁 Categorías", ["Comida", "Transporte", "Ocio", "Servicios", "Salud", "Ropa", "Educación", "Ahorro", "Otro"])

    # ============================================================
    # CONTENIDO PRINCIPAL
    # ============================================================
    st.title("💸 Gestión de Egresos")
    
    @st.cache_data(ttl=60)
    def cargar_datos():
        try:
            worksheet = connect_sheets()
            datos = worksheet.get_all_records()
            return pd.DataFrame(datos)
        except Exception as e:
            st.error(f"Error cargando datos: {e}")
            return pd.DataFrame()

    df = cargar_datos()
    
    if not df.empty:
        # --- KPIs ---
        total_cop = df[df['Divisa']=='COP']['Monto'].sum() if 'Monto' in df.columns and 'Divisa' in df.columns else 0
        prom_score = pd.to_numeric(df['Score'], errors='coerce').fillna(0).mean() if 'Score' in df.columns else 0
        
        k1, k2, k3 = st.columns(3)
        k1.metric("💰 Total (COP)", f"${total_cop:,.0f}")
        k2.metric("📋 Registros", len(df))
        k3.metric("📊 Score IA", f"{prom_score:.1f}/5.0" if prom_score else "Sin auditar")

        # --- Gráficos ---
        t1, t2 = st.tabs(["📊 Categorías", "📅 Tendencia"])
        with t1:
            if 'Categoria' in df.columns:
                gastos_cat = df.groupby('Categoria')['Monto'].sum().reset_index()
                fig_pie = px.pie(gastos_cat, values='Monto', names='Categoria', 
                                 hole=0.4, title="Distribución por Categoría")
                fig_pie.update_layout(template="plotly_dark")
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with t2:
            if 'Fecha' in df.columns:
                df_trend = df.copy()
                df_trend['Fecha'] = pd.to_datetime(df_trend['Fecha'], errors='coerce')
                df_trend = df_trend.dropna(subset=['Fecha']).sort_values('Fecha')
                if not df_trend.empty:
                    fig_line = px.line(df_trend, x='Fecha', y='Monto', markers=True,
                                       title="Tendencia de Gastos")
                    fig_line.update_layout(template="plotly_dark")
                    st.plotly_chart(fig_line, use_container_width=True)
        
        st.divider()
        
        # ============================================================
        # VISTA TARJETAS / TABLA
        # ============================================================
        st.subheader("📝 Detalle de Gastos")
        
        # Toggle vista
        vista = st.radio("Vista:", ["🃏 Tarjetas", "📋 Tabla"], horizontal=True, index=0, key="vista_egresos")
        
        df_display = df.copy()
        df_display.insert(0, 'Fila', range(2, len(df) + 2))
        
        if vista == "🃏 Tarjetas":
            # Vista de Tarjetas
            cols = st.columns(3)
            for idx, (_, row) in enumerate(df_display.iterrows()):
                with cols[idx % 3]:
                    # Color según score
                    score = pd.to_numeric(row.get('Score', 0), errors='coerce') or 0
                    if score >= 4:
                        border_color = "#00ff88"  # Verde neón
                        score_emoji = "✅"
                    elif score >= 3:
                        border_color = "#00d4ff"  # Azul neón
                        score_emoji = "👍"
                    elif score >= 2:
                        border_color = "#ffaa00"  # Naranja
                        score_emoji = "⚠️"
                    else:
                        border_color = "#ff3355"  # Rojo neón
                        score_emoji = "❌"
                    
                    st.markdown(f"""
                    <div style="
                        background: #111;
                        border: 2px solid {border_color};
                        border-radius: 12px;
                        padding: 16px;
                        margin-bottom: 12px;
                        box-shadow: 0 0 15px {border_color}33;
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="background: #222; padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; color: #888;">
                                {row.get('Categoria', 'Sin categoría')}
                            </span>
                            <span style="font-size: 1.2rem;">{score_emoji} {score:.1f}</span>
                        </div>
                        <h4 style="margin: 8px 0; color: #fff;">{row.get('Concepto', 'Sin concepto')[:30]}</h4>
                        <p style="font-size: 1.4rem; font-weight: 700; color: {border_color}; margin: 4px 0;">
                            {formatear_moneda(row.get('Monto', 0), row.get('Divisa', 'COP'))}
                        </p>
                        <small style="color: #666;">📅 {row.get('Fecha', '')} | Fila {row.get('Fila', '')}</small>
                        <p style="color: #888; font-size: 0.8rem; margin-top: 8px; font-style: italic;">
                            {str(row.get('Justificacion', ''))[:60]}{'...' if len(str(row.get('Justificacion', ''))) > 60 else ''}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.divider()
        
        # Selector de fila para acciones (siempre visible)
        st.markdown("**Acciones:**")
        
        col_select, col_edit, col_delete = st.columns([2, 1, 1])
        
        with col_select:
            filas_disponibles = df_display['Fila'].tolist()
            fila_seleccionada = st.selectbox(
                "Fila #", 
                options=filas_disponibles,
                format_func=lambda x: f"Fila {x}: {df_display[df_display['Fila']==x]['Concepto'].values[0] if len(df_display[df_display['Fila']==x]) > 0 else 'N/A'}",
                key="selector_fila_egreso"
            )
        
        with col_edit:
            if st.button("✏️ Editar", use_container_width=True, key="btn_editar_egreso"):
                st.session_state['editar_fila_egreso'] = fila_seleccionada
                st.session_state['datos_fila_egreso'] = df_display[df_display['Fila'] == fila_seleccionada].iloc[0].to_dict()
        
        with col_delete:
            if st.button("🗑️ Eliminar", use_container_width=True, type="secondary", key="btn_eliminar_egreso"):
                st.session_state['eliminar_fila_egreso'] = fila_seleccionada
        
        # Modal de Edición
        if 'editar_fila_egreso' in st.session_state and st.session_state.get('editar_fila_egreso'):
            fila = st.session_state['editar_fila_egreso']
            datos = st.session_state.get('datos_fila_egreso', {})
            
            with st.form(f"form_editar_egreso_{fila}"):
                st.markdown(f"### ✏️ Editando Fila {fila}")
                
                new_fecha = st.date_input("Fecha", value=pd.to_datetime(datos.get('Fecha', datetime.now())).date())
                new_concepto = st.text_input("Concepto", value=datos.get('Concepto', ''))
                
                c1, c2 = st.columns(2)
                new_divisa = c1.selectbox("Divisa", ["COP", "USD", "EUR"], 
                                          index=["COP", "USD", "EUR"].index(datos.get('Divisa', 'COP')))
                new_monto = c2.number_input("Monto", value=float(datos.get('Monto', 0)), min_value=0.0)
                
                new_categoria = st.selectbox("Categoría", 
                    ["Comida", "Transporte", "Ocio", "Servicios", "Salud", "Ropa", "Educación", "Ahorro", "Otro"],
                    index=["Comida", "Transporte", "Ocio", "Servicios", "Salud", "Ropa", "Educación", "Ahorro", "Otro"].index(datos.get('Categoria', 'Otro')) if datos.get('Categoria') in ["Comida", "Transporte", "Ocio", "Servicios", "Salud", "Ropa", "Educación", "Ahorro", "Otro"] else 8
                )
                
                col_save, col_cancel = st.columns(2)
                if col_save.form_submit_button("💾 Guardar Cambios", use_container_width=True):
                    try:
                        ws = connect_sheets(0)
                        # Actualizar celdas individuales (más seguro que batch)
                        ws.update_cell(fila, 1, str(new_fecha))  # Fecha
                        ws.update_cell(fila, 2, new_concepto)     # Concepto
                        ws.update_cell(fila, 3, new_monto)        # Monto
                        ws.update_cell(fila, 4, new_divisa)       # Divisa
                        ws.update_cell(fila, 5, new_categoria)    # Categoria
                        
                        st.success("✅ Registro actualizado correctamente")
                        st.session_state.pop('editar_fila_egreso', None)
                        st.session_state.pop('datos_fila_egreso', None)
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error actualizando: {e}")
                
                if col_cancel.form_submit_button("❌ Cancelar", use_container_width=True):
                    st.session_state.pop('editar_fila_egreso', None)
                    st.session_state.pop('datos_fila_egreso', None)
                    st.rerun()
        
        # Modal de Eliminación
        if 'eliminar_fila_egreso' in st.session_state and st.session_state.get('eliminar_fila_egreso'):
            fila = st.session_state['eliminar_fila_egreso']
            concepto_eliminar = df_display[df_display['Fila'] == fila]['Concepto'].values[0] if len(df_display[df_display['Fila'] == fila]) > 0 else 'este registro'
            
            st.warning(f"⚠️ ¿Estás seguro de eliminar **{concepto_eliminar}** (Fila {fila})?")
            
            col_confirm, col_cancel = st.columns(2)
            if col_confirm.button("🗑️ Confirmar Eliminación", use_container_width=True, type="primary"):
                try:
                    ws = connect_sheets(0)
                    ws.delete_rows(fila)
                    st.success("✅ Registro eliminado")
                    st.session_state.pop('eliminar_fila_egreso', None)
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error eliminando: {e}")
            
            if col_cancel.button("❌ Cancelar", use_container_width=True):
                st.session_state.pop('eliminar_fila_egreso', None)
                st.rerun()
        
        # Mostrar tabla solo si está seleccionada
        if vista == "📋 Tabla":
            cols_display = ['Fila', 'Fecha', 'Concepto', 'Monto', 'Divisa', 'Categoria', 'Score', 'Justificacion']
            cols_existentes = [c for c in cols_display if c in df_display.columns]
            st.dataframe(df_display[cols_existentes], use_container_width=True, height=400)


        
        # ============================================================
        # NOTIFICACIONES DE PAGOS RECURRENTES
        # ============================================================
        def calcular_proxima_fecha(fecha_original, recurrencia):
            """Calcula la próxima fecha de pago según la recurrencia."""
            from dateutil.relativedelta import relativedelta
            
            intervalos = {
                "Semanal": relativedelta(weeks=1),
                "Quincenal": relativedelta(weeks=2),
                "Mensual": relativedelta(months=1),
                "Bimestral": relativedelta(months=2),
                "Trimestral": relativedelta(months=3),
                "Semestral": relativedelta(months=6),
                "Anual": relativedelta(years=1)
            }
            
            if recurrencia not in intervalos or recurrencia == "Único":
                return None
            
            intervalo = intervalos[recurrencia]
            proxima = fecha_original + intervalo
            
            # Avanzar hasta la próxima fecha futura
            hoy = datetime.now().date()
            while proxima.date() < hoy:
                proxima += intervalo
            
            return proxima

        # Verificar pagos próximos (si hay columna Recurrencia)
        if not df.empty and 'Recurrencia' in df.columns and 'Fecha' in df.columns:
            df_recurrentes = df[df['Recurrencia'].isin(['Semanal', 'Quincenal', 'Mensual', 'Bimestral', 'Trimestral', 'Semestral', 'Anual'])].copy()
            
            if not df_recurrentes.empty:
                try:
                    from dateutil.relativedelta import relativedelta
                    
                    pagos_hoy = []
                    pagos_proximos = []
                    hoy = datetime.now().date()
                    en_3_dias = hoy + timedelta(days=3)
                    
                    for _, row in df_recurrentes.iterrows():
                        try:
                            # Verificar si tiene alertas activadas (columna index 9 aprox, o por nombre si existe)
                            # Si no existe la columna Alerta, asumimos que SÍ quiere alerta por defecto
                            if 'Alerta' in df.columns and str(row.get('Alerta', '')).upper() == 'NO':
                                continue
                                
                            fecha_orig = pd.to_datetime(row['Fecha'])
                            proxima = calcular_proxima_fecha(fecha_orig, row['Recurrencia'])
                            
                            if proxima:
                                fecha_pago = proxima.date()
                                pago_info = {
                                    'concepto': row.get('Concepto', 'Pago'),
                                    'monto': row.get('Monto', 0),
                                    'divisa': row.get('Divisa', 'COP'),
                                    'fecha': proxima.strftime('%d/%m/%Y'),
                                    'recurrencia': row['Recurrencia'],
                                    'dias_restantes': (fecha_pago - hoy).days
                                }
                                
                                if fecha_pago == hoy:
                                    pagos_hoy.append(pago_info)
                                elif hoy < fecha_pago <= en_3_dias:
                                    pagos_proximos.append(pago_info)
                        except:
                            continue
                    
                    # CSS para animación llamativa
                    st.markdown("""
                    <style>
                    @keyframes pulse {
                        0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
                        70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
                        100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
                    }
                    .pago-urgente {
                        animation: pulse 1.5s infinite;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # PAGOS DE HOY - MUY LLAMATIVO
                    if pagos_hoy:
                        st.markdown(f"""
                        <div class="pago-urgente" style="
                            background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%);
                            border: 2px solid #ef4444;
                            border-radius: 12px;
                            padding: 20px;
                            margin-bottom: 16px;
                            text-align: center;
                        ">
                            <h3 style="color: #fca5a5; margin: 0 0 10px 0;">⚠️ ¡PAGO HOY! ⚠️</h3>
                            <p style="color: #ffffff; font-size: 1.1rem; margin: 0;">
                                Tienes <strong>{len(pagos_hoy)}</strong> pago(s) programado(s) para HOY
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for pago in pagos_hoy:
                            st.markdown(f"""
                            <div style="
                                background-color: #450a0a;
                                border-left: 4px solid #ef4444;
                                padding: 14px;
                                border-radius: 8px;
                                margin-bottom: 10px;
                            ">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <strong style="color: #ffffff; font-size: 1.1rem;">🔴 {pago['concepto']}</strong>
                                    <span style="color: #fca5a5; font-size: 1.2rem; font-weight: bold;">
                                        {formatear_moneda(pago['monto'], pago['divisa'])}
                                    </span>
                                </div>
                                <small style="color: #f87171;">📅 Vence HOY - {pago['recurrencia']}</small>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # PAGOS EN 3 DÍAS - Advertencia
                    if pagos_proximos:
                        st.warning(f"🔔 **{len(pagos_proximos)} pago(s) en los próximos 3 días:**")
                        for pago in pagos_proximos[:5]:
                            dias = pago['dias_restantes']
                            st.markdown(f"""
                            <div style="
                                background-color: #422006;
                                border-left: 3px solid #f59e0b;
                                padding: 12px;
                                border-radius: 6px;
                                margin-bottom: 8px;
                            ">
                                <strong style="color: #ffffff;">{pago['concepto']}</strong> - 
                                <span style="color: #fcd34d;">{formatear_moneda(pago['monto'], pago['divisa'])}</span>
                                <br><small style="color: #fbbf24;">📅 En {dias} día(s) - {pago['fecha']} ({pago['recurrencia']})</small>
                            </div>
                            """, unsafe_allow_html=True)
                            
                except ImportError:
                    pass  # dateutil no instalado
    
    else:
        st.info("No hay gastos registrados. Usa el botón superior.")

# ============================================================
# ENRUTAMIENTO FINAL
# ============================================================
if modulo == "🏠 Inicio":
    render_inicio()
elif modulo == "💸 Egresos":
    render_egresos()
elif modulo == "💰 Ingresos":
    render_ingresos()
elif modulo == "🏦 Cuentas":
    render_cuentas()
elif modulo == "🐷 Bolsillos":
    render_bolsillos()
elif modulo == "🤝 Deudas":
    render_deudas()
elif modulo == "🤖 Asistente IA":
    render_asistente_ia()
