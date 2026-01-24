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
import os                    # Variables de entorno
from datetime import datetime, timedelta
from dotenv import load_dotenv  # Cargar variables desde .env
from currency import convertir_columna, formatear_moneda, obtener_tasas  # Conversión de divisas

# ============================================================
# CONFIGURACIÓN INICIAL
# ============================================================
load_dotenv()
st.set_page_config(page_title="Ge$torGasto$", page_icon="assets/logo.jpg", layout="wide")

# CSS para UX limpia - tema oscuro con buena legibilidad
st.markdown("""
<style>
    /* ============================================
       TEMA "CONTROL CENTER" - PREMIUM UX
       Inspirado en interfaces Smart Home Dark Mode
       ============================================ */
    
    /* Fuentes y Variables */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    :root {
        /* Paleta Principal - Deep Dark Blue/Black */
        --bg-app: #050505;          /* Fondo casi negro */
        --bg-panel: #0a0a0a;        /* Sidebar un poco más claro */
        --card-bg: #141414;         /* Tarjetas base */
        --card-hover: #1f1f1f;
        
        /* Acentos - Electric Blue & Neon Green */
        --primary: #3b82f6;         /* Azul eléctrico */
        --primary-glow: rgba(59, 130, 246, 0.4);
        --success: #10b981;         /* Verde neón */
        --danger: #ef4444;          /* Rojo alerta */
        
        /* Texto */
        --text-main: #ffffff;
        --text-dim: #9ca3af;
        
        /* Bordes y Efectos */
        --border-subtle: #262626;
        --radius-lg: 20px;
        --radius-md: 14px;
        --radius-sm: 8px;
    }
    
    /* Configuración General */
    .stApp {
        background-color: var(--bg-app) !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Texto */
    .stApp, p, span, label, div {
        color: var(--text-main) !important;
        letter-spacing: -0.01em !important;
    }
    
    h1, h2, h3 {
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }
    
    /* ============================================
       COMPONENTES TIPO "WIDGET"
       ============================================ */
       
    /* Métricas KPI - Estilo "Glass Card" Uniforme */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, var(--card-bg), #0f0f0f) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-lg) !important;
        padding: 24px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        
        /* Uniformidad de tamaño */
        min-height: 160px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
    }
    
    [data-testid="stMetric"]:hover {
        border-color: #404040 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4) !important;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        background: linear-gradient(90deg, #fff, #cbd5e1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--text-dim) !important;
        font-size: 0.9rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    
    /* Botones - Estilo "Pill" Moderno */
    .stButton > button {
        background: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 100px !important; /* Pill shape */
        padding: 12px 24px !important;
        font-weight: 600 !important;
        box-shadow: 0 0 15px var(--primary-glow) !important; /* Glow effect */
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        width: 100% !important;
    }
    
    .stButton > button:hover {
        background: #2563eb !important;
        box-shadow: 0 0 25px var(--primary-glow) !important;
        transform: scale(1.02) !important;
    }
    
    /* Sidebar - Panel de Control Oscuro */
    [data-testid="stSidebar"] {
        background-color: var(--bg-panel) !important;
        border-right: 1px solid var(--border-subtle) !important;
    }
    
    /* Inputs - Minimalistas */
    input, textarea, select, .stDateInput > div > div, .stNumberInput > div > div {
        background-color: #171717 !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-md) !important;
        color: white !important;
        height: 50px !important;
        transition: border-color 0.2s !important;
    }
    
    input:focus, textarea:focus, select:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 1px var(--primary) !important;
    }
    
    .stSelectbox > div > div, .stMultiSelect > div > div {
        background-color: #171717 !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-md) !important;
    }
    
    /* Tabs - Estilo Navegación */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background-color: transparent !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border-radius: 100px !important;
        padding: 8px 16px !important;
        color: var(--text-dim) !important;
        border: 1px solid transparent !important;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #262626 !important;
        color: white !important;
        border: 1px solid #404040 !important;
    }
    
    /* Progress Bars - Slim & Glowing */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--primary), #60a5fa) !important;
        height: 8px !important;
        border-radius: 100px !important;
        box-shadow: 0 0 10px var(--primary-glow) !important;
    }
    
    /* Dataframes/Tablas - Estilo Dashboard */
    .stDataFrame {
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-lg) !important;
        overflow: hidden !important;
    }
    
    /* Alertas y Notificaciones */
    .stAlert {
        background-color: #1a1a1a !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-md) !important;
    }
    
    /* Scrollbars */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: var(--bg-app);
    }
    ::-webkit-scrollbar-thumb {
        background: #333;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
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
def connect_sheets():
    """
    Conecta con Google Sheets usando credenciales disponibles.
    Soporta: archivo local, variable de entorno, y st.secrets
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
        return sh.sheet1 
    except gspread.exceptions.SpreadsheetNotFound:
        raise ValueError(f"No se encontró la hoja: {GOOGLE_SHEET_NAME}")

# ============================================================
# SISTEMA DE AUTENTICACIÓN
# ============================================================
USUARIO_ADMIN = obtener_secreto("ADMIN_USER")
CONTRASEÑA_ADMIN = obtener_secreto("ADMIN_PASSWORD")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

import extra_streamlit_components as stx

def verificar_login():
    """Muestra el formulario de login si el usuario no está autenticado."""
    
    # 1. Inicializar Cookie Manager
    cookie_manager = stx.CookieManager()
    
    # 2. Verificar si ya está autenticado en sesión actual
    if st.session_state.get("authenticated", False):
        return True
    
    # 3. Verificar si hay cookie de "recordarme"
    # Nota: get_all() a veces tarda un poco en cargar en la primera ejecución
    cookies = cookie_manager.get_all()
    if cookies.get("gestor_gastos_auth") == "true":
        st.session_state["authenticated"] = True
        return True
    
    # 4. Mostrar formulario de login
    st.title("🔒 Acceso Restringido")
    
    with st.form("formulario_login"):
        usuario = st.text_input("Usuario")
        contraseña = st.text_input("Contraseña", type="password")
        recordarme = st.checkbox("💾 Recordarme en este dispositivo")
        enviado = st.form_submit_button("Entrar")
        
        if enviado:
            if usuario == USUARIO_ADMIN and contraseña == CONTRASEÑA_ADMIN:
                st.session_state["authenticated"] = True
                
                # Si marcó "Recordarme", guardar cookie por 30 días
                if recordarme:
                    cookie_manager.set("gestor_gastos_auth", "true", key="set_auth_cookie", expires_at=datetime.now() + timedelta(days=30))
                
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
                
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
    <h2 style="color: #4ade80; margin: 0;">💰 Ge$torGasto$</h2>
    <p style="color: #9ca3af; font-size: 0.85rem; margin: 5px 0 0 0;">Auditor Financiero con IA</p>
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
    if st.button("�", help="Cerrar sesión"):
        st.session_state["authenticated"] = False
        st.rerun()

# Botón de Auditoría IA
if st.sidebar.button("🚀 Ejecutar Auditoría IA", use_container_width=True):
    with st.spinner("Analizando con Gemini..."):
        try:
            from auditor import run_audit
            estadisticas = run_audit()
            if estadisticas["processed"] > 0:
                st.sidebar.success(f"✅ {estadisticas['processed']} gastos analizados.")
                st.cache_data.clear()
            else:
                st.sidebar.info("👍 Todo al día.")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

st.sidebar.divider()

# ============================================================
# FORMULARIO PARA REGISTRAR NUEVOS GASTOS
# ============================================================
with st.sidebar.expander("➕ Registrar Nuevo Gasto", expanded=False):
    with st.form("formulario_gasto"):
        fecha = st.date_input("📅 Fecha")
        concepto = st.text_input("📝 Concepto")
        
        col1, col2 = st.columns([1, 2])
        divisa = col1.selectbox("Divisa", ["COP", "USD", "EUR"])
        monto = col2.number_input("Monto", min_value=0.0, step=100.0 if divisa == "COP" else 1.0)
        
        categoria = st.selectbox("📁 Categoría", [
            "Comida", "Transporte", "Ocio", "Servicios", 
            "Salud", "Ropa", "Educación", "Ahorro", "Otro"
        ])
        
        # SECCIÓN DE RECURRENCIA Y RECORDATORIO - VISUALMENTE DESTACADA
        st.markdown("---")
        st.markdown("**🔄 Repetición y Alertas**")
        col_rec1, col_rec2 = st.columns(2)
        
        with col_rec1:
            # Recurrencia del gasto
            recurrencia = st.selectbox("Frecuencia", [
                "Único", "Semanal", "Quincenal", "Mensual", "Bimestral", 
                "Trimestral", "Semestral", "Anual"
            ], help="¿Cada cuánto se repite este gasto?")
            
        with col_rec2:
            # Opción explícita de alerta
            recordatorio = st.checkbox("🔔 Crear alerta de pago", value=(recurrencia != "Único"))
            
        st.markdown("---")
        
        medio_pago = st.selectbox("💳 Medio de Pago", [
            "Tarjeta Débito", "Tarjeta Crédito", "Efectivo", "Transferencia"
        ], index=0)  # Tarjeta Débito por defecto
        
        lugar = st.text_input("📍 Lugar (Opcional)")
        banco = st.text_input("🏦 Banco (Opcional)")
        
        enviado = st.form_submit_button("💾 Guardar", use_container_width=True)
        
        if enviado:
            if concepto and monto > 0:
                try:
                    worksheet = connect_sheets()
                    # Convertir bool a string para sheets
                    alerta_str = "SÍ" if recordatorio else "NO"
                    
                    # Agregar recurrencia y alerta a los datos
                    nueva_fila = [
                        str(fecha), concepto, monto, divisa, categoria, lugar, 
                        medio_pago, banco, recurrencia, alerta_str
                    ]
                    worksheet.append_row(nueva_fila)
                    st.success("¡Guardado!")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Completa concepto y monto.")

# ============================================================
# SECCIÓN DE DEUDAS
# ============================================================
st.sidebar.divider()
with st.sidebar.expander("💸 Gestión de Deudas", expanded=False):
    
    # Tabs para Me Deben / Debo
    tab_me_deben, tab_yo_debo = st.tabs(["📥 Me Deben", "📤 Yo Debo"])
    
    with tab_me_deben:
        st.markdown("**Registrar quién te debe:**")
        with st.form("form_me_deben"):
            deudor = st.text_input("👤 Nombre de quien te debe")
            monto_deuda = st.number_input("💵 Monto", min_value=0.0, step=1000.0, key="monto_deben")
            divisa_deuda = st.selectbox("Divisa", ["COP", "USD", "EUR"], key="divisa_deben")
            concepto_deuda = st.text_input("📝 Por qué concepto", key="concepto_deben")
            fecha_prestamo = st.date_input("📅 Fecha del préstamo", key="fecha_deben")
            fecha_limite = st.date_input("⏰ Fecha límite de pago", key="limite_deben")
            recordar = st.checkbox("🔔 Crear recordatorio", value=True, key="recordar_deben")
            
            if st.form_submit_button("💾 Guardar Deuda", use_container_width=True):
                if deudor and monto_deuda > 0:
                    try:
                        worksheet = connect_sheets()
                        # Agregar como fila especial con tipo "ME_DEBEN"
                        nueva_fila = [
                            str(fecha_prestamo), f"DEUDA: {deudor} me debe", monto_deuda, 
                            divisa_deuda, "Deuda - Me Deben", concepto_deuda, "Préstamo", 
                            deudor, "Único" if not recordar else "Mensual"
                        ]
                        worksheet.append_row(nueva_fila)
                        st.success(f"✅ Registrado: {deudor} te debe {monto_deuda} {divisa_deuda}")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Completa nombre y monto.")
    
    with tab_yo_debo:
        st.markdown("**Registrar a quién le debes:**")
        with st.form("form_yo_debo"):
            acreedor = st.text_input("👤 Nombre de a quién le debes")
            monto_debo = st.number_input("💵 Monto", min_value=0.0, step=1000.0, key="monto_debo")
            divisa_debo = st.selectbox("Divisa", ["COP", "USD", "EUR"], key="divisa_debo")
            concepto_debo = st.text_input("📝 Por qué concepto", key="concepto_debo")
            fecha_deuda = st.date_input("📅 Fecha de la deuda", key="fecha_debo")
            fecha_pago = st.date_input("⏰ Fecha límite de pago", key="pago_debo")
            recordar_debo = st.checkbox("🔔 Crear recordatorio", value=True, key="recordar_debo")
            
            if st.form_submit_button("💾 Guardar Deuda", use_container_width=True):
                if acreedor and monto_debo > 0:
                    try:
                        worksheet = connect_sheets()
                        # Agregar como fila especial con tipo "YO_DEBO"
                        nueva_fila = [
                            str(fecha_deuda), f"DEUDA: Debo a {acreedor}", monto_debo, 
                            divisa_debo, "Deuda - Yo Debo", concepto_debo, "Préstamo", 
                            acreedor, "Único" if not recordar_debo else "Mensual"
                        ]
                        worksheet.append_row(nueva_fila)
                        st.success(f"✅ Registrado: Debes {monto_debo} {divisa_debo} a {acreedor}")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Completa nombre y monto.")

# ============================================================
# CARGA DE DATOS
# ============================================================
@st.cache_data(ttl=60)
def cargar_datos():
    """Carga registros desde Google Sheets."""
    try:
        worksheet = connect_sheets()
        datos = worksheet.get_all_records()
        return pd.DataFrame(datos)
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame()

df = cargar_datos()

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

# ============================================================
# VISUALIZACIÓN (Solo si hay datos)
# ============================================================
if not df.empty:
    
    # --- PREPARACIÓN DE DATOS ---
    try:
        df['MontoNum'] = df['Monto'].astype(str).str.replace(r'[$,]', '', regex=True).astype(float)
    except:
        df['MontoNum'] = 0
    
    df['ScoreNum'] = pd.to_numeric(df['Score'], errors='coerce').fillna(0)
    
    if 'Fecha' in df.columns:
        df['FechaDt'] = pd.to_datetime(df['Fecha'], errors='coerce')
    
    # ============================================================
    # SECCIÓN DE FILTROS
    # ============================================================
    st.sidebar.divider()
    st.sidebar.header("🔍 Filtros")
    
    # Filtro por divisa base para conversión
    divisa_base = st.sidebar.selectbox(
        "💱 Divisa para totales",
        ["COP", "USD", "EUR"],
        help="Convierte todos los montos a esta divisa para calcular totales"
    )
    
    # Filtro por rango de fechas
    if 'FechaDt' in df.columns and not df['FechaDt'].isna().all():
        fecha_min = df['FechaDt'].min().date()
        fecha_max = df['FechaDt'].max().date()
        rango_fechas = st.sidebar.date_input(
            "📅 Rango de fechas",
            value=(fecha_min, fecha_max),
            min_value=fecha_min,
            max_value=fecha_max
        )
    else:
        rango_fechas = None
    
    # Filtro por categorías
    if 'Categoria' in df.columns:
        categorias_disponibles = df['Categoria'].unique().tolist()
        categorias_seleccionadas = st.sidebar.multiselect(
            "📁 Categorías",
            categorias_disponibles,
            default=categorias_disponibles
        )
    else:
        categorias_seleccionadas = []
    
    # Filtro por divisas
    if 'Divisa' in df.columns:
        divisas_disponibles = df['Divisa'].unique().tolist()
        divisas_seleccionadas = st.sidebar.multiselect(
            "💵 Divisas",
            divisas_disponibles,
            default=divisas_disponibles
        )
    else:
        divisas_seleccionadas = []
    
    # Filtro por Score
    rango_score = st.sidebar.slider(
        "⭐ Rango de Score",
        min_value=0, max_value=5,
        value=(0, 5),
        help="1-2: Hormiga, 3: Opcional, 4-5: Necesario"
    )
    
    # --- APLICAR FILTROS ---
    df_filtrado = df.copy()
    
    # Filtro de fechas
    if rango_fechas and len(rango_fechas) == 2 and 'FechaDt' in df_filtrado.columns:
        fecha_inicio, fecha_fin = rango_fechas
        df_filtrado = df_filtrado[
            (df_filtrado['FechaDt'].dt.date >= fecha_inicio) & 
            (df_filtrado['FechaDt'].dt.date <= fecha_fin)
        ]
    
    # Filtro de categorías
    if categorias_seleccionadas and 'Categoria' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Categoria'].isin(categorias_seleccionadas)]
    
    # Filtro de divisas
    if divisas_seleccionadas and 'Divisa' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Divisa'].isin(divisas_seleccionadas)]
    
    # Filtro de score
    df_filtrado = df_filtrado[
        (df_filtrado['ScoreNum'] >= rango_score[0]) & 
        (df_filtrado['ScoreNum'] <= rango_score[1])
    ]
    
    # --- CONVERSIÓN DE DIVISAS ---
    if 'Divisa' in df_filtrado.columns and not df_filtrado.empty:
        df_filtrado['MontoConvertido'] = convertir_columna(
            df_filtrado, 'MontoNum', 'Divisa', divisa_base
        )
    else:
        df_filtrado['MontoConvertido'] = df_filtrado['MontoNum']
    
    # ============================================================
    # KPIs CON CONVERSIÓN
    # ============================================================
    st.subheader(f"📊 Resumen (en {divisa_base})")
    
    gasto_total = df_filtrado['MontoConvertido'].sum()
    gasto_hormiga = df_filtrado[df_filtrado['ScoreNum'] <= 2]['MontoConvertido'].sum()
    salud_promedio = df_filtrado['ScoreNum'].mean() if len(df_filtrado) > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💵 Gasto Total", formatear_moneda(gasto_total, divisa_base))
    col2.metric("🐜 Gasto Hormiga", formatear_moneda(gasto_hormiga, divisa_base), 
                delta=f"-{gasto_hormiga:,.0f}", delta_color="inverse")
    col3.metric("❤️ Salud Financiera", f"{salud_promedio:.1f}/5.0")
    col4.metric("📝 Registros", f"{len(df_filtrado)}/{len(df)}")
    
    # ============================================================
    # DASHBOARD DE PRESUPUESTO
    # ============================================================
    st.subheader("💰 Presupuesto por Categoría")
    
    PRESUPUESTOS_DEFAULT = {
        "Comida": 800000,
        "Transporte": 300000,
        "Ocio": 200000,
        "Servicios": 400000,
        "Salud": 150000,
        "Ropa": 150000,
        "Educación": 200000,
        "Ahorro": 500000,
        "Otro": 100000
    }
    
    if 'Categoria' in df_filtrado.columns:
        gasto_por_categoria = df_filtrado.groupby('Categoria')['MontoConvertido'].sum()
        
        cols = st.columns(3)
        for idx, (categoria, presupuesto) in enumerate(PRESUPUESTOS_DEFAULT.items()):
            gasto_actual = gasto_por_categoria.get(categoria, 0)
            porcentaje = min((gasto_actual / presupuesto) * 100, 100) if presupuesto > 0 else 0
            
            with cols[idx % 3]:
                if porcentaje >= 90:
                    color = "🔴"
                elif porcentaje >= 70:
                    color = "🟡"
                else:
                    color = "🟢"
                
                st.markdown(f"**{color} {categoria}**")
                st.progress(porcentaje / 100)
                st.caption(f"{formatear_moneda(gasto_actual, divisa_base)} / {formatear_moneda(presupuesto, divisa_base)}")
    
    # ============================================================
    # GRÁFICOS
    # ============================================================
    st.subheader("📈 Análisis Visual")
    col_grafico1, col_grafico2 = st.columns(2)
    
    with col_grafico1:
        st.markdown("**Gastos por Categoría**")
        if 'Categoria' in df_filtrado.columns and len(df_filtrado) > 0:
            fig_pastel = px.pie(df_filtrado, values='MontoConvertido', names='Categoria', hole=0.4)
            st.plotly_chart(fig_pastel, use_container_width=True)
    
    with col_grafico2:
        st.markdown("**Necesidad vs Deseo**")
        
        def categorizar_gasto(score):
            if score >= 4: return "Vital/Necesario"
            if score == 3: return "Opcional"
            return "Innecesario"
        
        if len(df_filtrado) > 0:
            df_filtrado['TipoGasto'] = df_filtrado['ScoreNum'].apply(categorizar_gasto)
            
            fig_barras = px.bar(
                df_filtrado, x='TipoGasto', y='MontoConvertido', color='TipoGasto',
                color_discrete_map={
                    "Vital/Necesario": "#2ecc71",
                    "Opcional": "#f1c40f",
                    "Innecesario": "#e74c3c"
                },
                labels={'MontoConvertido': f'Monto ({divisa_base})', 'TipoGasto': 'Tipo'}
            )
            st.plotly_chart(fig_barras, use_container_width=True)
    
    # --- TENDENCIA ---
    st.markdown("**Tendencia de Gastos**")
    if 'FechaDt' in df_filtrado.columns:
        df_tendencia = df_filtrado.dropna(subset=['FechaDt']).sort_values('FechaDt')
        
        if not df_tendencia.empty:
            fig_linea = px.line(
                df_tendencia, x='FechaDt', y='MontoConvertido', 
                markers=True, labels={'FechaDt': 'Fecha', 'MontoConvertido': f'Monto ({divisa_base})'}
            )
            st.plotly_chart(fig_linea, use_container_width=True)
        else:
            st.info("No hay fechas válidas para mostrar tendencia.")
    
    # ============================================================
    # TABLA DE DETALLE - Estilo mejorado
    # ============================================================
    st.subheader("📋 Detalle de Gastos")
    
    # Selector de vista - Tarjetas por defecto
    vista = st.radio("Vista:", ["🃏 Tarjetas", "📊 Tabla"], horizontal=True, label_visibility="collapsed")
    
    columnas_mostrar = ['Fecha', 'Concepto', 'Monto', 'Divisa', 
                        'Categoria', 'MedioPago', 'Score', 'Justificacion']
    columnas_existentes = [c for c in columnas_mostrar if c in df_filtrado.columns]
    
    if vista == "📊 Tabla":
        # Vista de tabla mejorada con colores para tema oscuro
        def colorear_filas(fila):
            try:
                valor = float(fila.get('Score', 0))
                if valor >= 4: 
                    return ['background-color: #166534; color: #ffffff'] * len(fila)  # Verde oscuro
                if valor <= 2: 
                    return ['background-color: #991b1b; color: #ffffff'] * len(fila)  # Rojo oscuro
                return ['background-color: #1f2937; color: #ffffff'] * len(fila)  # Gris oscuro
            except:
                return ['background-color: #1f2937; color: #ffffff'] * len(fila)
        
        st.dataframe(
            df_filtrado[columnas_existentes].style.apply(colorear_filas, axis=1),
            use_container_width=True,
            height=400
        )
    else:
        # Vista de tarjetas
        for idx, row in df_filtrado.iterrows():
            score = float(row.get('Score', 0)) if row.get('Score') else 0
            
            # Color según score
            if score >= 4:
                color_borde = "#22c55e"  # Verde
                emoji_score = "✅"
            elif score <= 2:
                color_borde = "#ef4444"  # Rojo
                emoji_score = "⚠️"
            else:
                color_borde = "#f59e0b"  # Amarillo
                emoji_score = "➖"
            
            # Card HTML
            st.markdown(f"""
            <div style="
                background-color: #1f2937;
                border-left: 4px solid {color_borde};
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 12px;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 1.1rem; font-weight: 600; color: #ffffff;">
                        {row.get('Concepto', 'Sin concepto')}
                    </span>
                    <span style="font-size: 1.2rem; font-weight: 700; color: {color_borde};">
                        {formatear_moneda(row.get('Monto', 0), row.get('Divisa', 'COP'))}
                    </span>
                </div>
                <div style="display: flex; gap: 16px; flex-wrap: wrap; color: #9ca3af; font-size: 0.85rem;">
                    <span>📅 {row.get('Fecha', '-')}</span>
                    <span>📁 {row.get('Categoria', '-')}</span>
                    <span>💳 {row.get('MedioPago', '-')}</span>
                    <span>{emoji_score} Score: {score:.0f}/5</span>
                </div>
                <div style="margin-top: 10px; color: #d1d5db; font-size: 0.9rem; font-style: italic;">
                    💬 {row.get('Justificacion', 'Sin análisis aún')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Limitar a 20 tarjetas para rendimiento
            if idx >= 19:
                st.info(f"Mostrando 20 de {len(df_filtrado)} registros. Usa filtros para ver más.")
                break
    
    # ============================================================
    # BOTÓN DE EXPORTAR
    # ============================================================
    st.divider()
    col_export1, col_export2, col_export3 = st.columns([2, 1, 2])
    with col_export2:
        csv = df_filtrado[columnas_existentes].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar CSV",
            data=csv,
            file_name=f"gastos_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

else:
    st.warning("No hay datos. Asegúrate de que tu Google Sheet tenga contenido.")
