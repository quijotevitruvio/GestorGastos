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
        # Fallback si no encuentra la hoja específica, intenta crearla o devolver sheet1
        st.error(f"No se encontró la pestaña '{target_sheet}'. Asegúrate de ejecutar init_finance_sheets.py")
        return sh.sheet1
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
    ["📊 Balance", "💰 Ingresos", "💸 Egresos", "🤝 Deudas"],
    index=2, # Default: Egresos
    key="navegacion_principal"
)

st.sidebar.markdown("---")

# ============================================================
# FUNCIONES DE MÓDULOS (NUEVAS)
# ============================================================

def render_ingresos():
    st.title("💰 Gestión de Ingresos")
    
    # Layout Config: 3 parts content, 1 part form (Right Panel)
    col_main, col_panel = st.columns([3, 1])
    
    # --- Right Panel: Registrar Ingreso ---
    with col_panel:
        st.markdown("### 📝 Nuevo Ingreso")
        with st.form("form_ingresos"):
            fecha = st.date_input("Fecha", key="ing_fecha")
            concepto = st.text_input("Concepto", placeholder="Ej: Nómina")
            
            c1, c2 = st.columns(2)
            divisa = c1.selectbox("Divisa", ["COP", "USD", "EUR"], key="ing_divisa")
            monto = c2.number_input("Monto", min_value=0.0, step=10000.0, key="ing_monto")
            
            fuente = st.selectbox("Fuente", ["Nómina", "Negocio", "Inversión", "Regalo", "Otros"])
            recurrencia = st.selectbox("Frecuencia", ["Único", "Mensual", "Quincenal", "Anual"], index=1)
            comentario = st.text_area("Notas", height=1)
            
            if st.form_submit_button("💾 Guardar Ingreso", use_container_width=True):
                if monto > 0 and concepto:
                    try:
                        sh = connect_sheets("Ingresos")
                        sh.append_row([
                            str(fecha), concepto, monto, divisa, fuente, recurrencia, comentario
                        ])
                        st.toast("✅ ¡Ingreso registrado exitosamente!")
                        st.cache_data.clear() # Limpiar caché para refrescar tabla
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error guardando: {e}")
                else:
                    st.warning("Completa concepto y monto.")

    # --- Main Content: Ver Datos ---
    with col_main:
        try:
            # Cargar datos
            sh = connect_sheets("Ingresos")
            records = sh.get_all_records()
            
            if records:
                df = pd.DataFrame(records)
                
                # KPI Rápido
                k1, k2 = st.columns(2)
                
                with k1:
                    total_cop = df[df['Divisa'] == 'COP']['Monto'].sum()
                    st.metric("Total Ingresos (COP)", f"${total_cop:,.0f}")
                    
                with k2:
                    df['Fecha'] = pd.to_datetime(df['Fecha'])
                    hoy = datetime.now()
                    mes_actual = df[
                        (df['Fecha'].dt.month == hoy.month) & 
                        (df['Fecha'].dt.year == hoy.year)
                    ]
                    total_mes_cop = mes_actual[mes_actual['Divisa'] == 'COP']['Monto'].sum()
                    st.metric(f"Ingresos {hoy.strftime('%B')}", f"${total_mes_cop:,.0f}")

                st.subheader("Historial")
                st.dataframe(
                    df.style.format({"Monto": "${:,.2f}"}), 
                    use_container_width=True,
                    height=400,
                    column_config={
                        "Fecha": st.column_config.DateColumn("Fecha", format="YYYY-MM-DD"),
                    }
                )
            else:
                st.info("ℹ️ No hay ingresos registrados. Usa el panel derecho 👉")
                
        except Exception as e:
            st.error(f"Error cargando hoja de Ingresos: {e}")
def render_deudas():
    st.title("🤝 Control de Deudas")
    
    # Layout: Content (Left) | Panel (Right)
    col_main, col_panel = st.columns([3, 1])
    
    # --- Right Panel: Formulario ---
    with col_panel:
        st.markdown("### 📝 Nueva Obligación")
        tipo_operacion = st.selectbox("Tipo", ["📥 Me Deben", "📤 Yo Debo"], key="deuda_tipo")
        
        with st.form("form_deudas_nuevo"):
            persona = st.text_input("Persona / Entidad", placeholder="¿Quién?")
            concepto = st.text_input("Concepto", placeholder="¿Por qué?")
            
            c1, c2 = st.columns(2)
            divisa = c1.selectbox("Divisa", ["COP", "USD", "EUR"], key="dd_div")
            monto = c2.number_input("Monto", min_value=0.0, step=10000.0)
            
            fecha_limite = st.date_input("Vence", key="dd_limite")
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

    # --- Main Content: Dashboard ---
    with col_main:
        try:
            sh = connect_sheets("Deudas")
            records = sh.get_all_records()
            
            if records:
                df = pd.DataFrame(records)
                
                # --- KPIs ---
                k1, k2 = st.columns(2)
                
                activos = df[(df['Tipo'] == 'ME_DEBEN') & (df['Estado'] == 'PENDIENTE')]['MontoOriginal'].sum()
                pasivos = df[(df['Tipo'] == 'YO_DEBO') & (df['Estado'] == 'PENDIENTE')]['MontoOriginal'].sum()
                 
                with k1:
                    st.metric("🟢 Me Deben", f"${activos:,.0f}", delta="Activos")
                with k2:
                    st.metric("🔴 Yo Debo", f"${pasivos:,.0f}", delta="-Pasivos", delta_color="inverse")
                    
                st.divider()
                
                # --- Tablas ---
                tab_activos, tab_pasivos = st.tabs(["📥 Me Deben", "📤 Yo Debo"])
                
                with tab_activos:
                    df_activos = df[df['Tipo'] == 'ME_DEBEN']
                    if not df_activos.empty:
                        st.dataframe(
                            df_activos[['Persona', 'MontoOriginal', 'FechaLimite', 'Estado']],
                            use_container_width=True
                        )
                    else:
                        st.info("No tienes cuentas por cobrar.")
                        
                with tab_pasivos:
                    df_pasivos = df[df['Tipo'] == 'YO_DEBO']
                    if not df_pasivos.empty:
                        st.dataframe(
                            df_pasivos[['Persona', 'MontoOriginal', 'FechaLimite', 'Estado']],
                            use_container_width=True
                        )
                    else:
                        st.success("¡Estás libre de deudas!")
                        
            else:
                st.info("ℹ️ No hay deudas registradas.")
                
        except Exception as e:
            st.error(f"Error cargando Deudas: {e}")
    
def render_balance():
    st.title("📊 Balance Global")
    
    col_main, col_chart = st.columns([1, 1])
    
    try:
        # Cargar datos
        sh_gastos = connect_sheets(0) # Egresos (default)
        sh_ingresos = connect_sheets("Ingresos")
        
        df_gastos = pd.DataFrame(sh_gastos.get_all_records())
        df_ingresos = pd.DataFrame(sh_ingresos.get_all_records())
        
        # Calcular Totales (Simplificado: Sin conversión de divisa avanzada por ahora)
        # TODO: Implementar conversión real usando la herramienta de divisas
        
        total_ingresos = 0
        if not df_ingresos.empty:
            # Sumar solo columnas numéricas de 'Monto'
            # Filtrar por COP idealmente, o sumar crudo si el usuario maneja una sola moneda principal
            # Asumimos mezcla de monedas se suma directo por ahora (v1)
            total_ingresos = pd.to_numeric(df_ingresos['Monto'], errors='coerce').sum()
            
        total_gastos = 0
        if not df_gastos.empty:
            total_gastos = pd.to_numeric(df_gastos['Monto'], errors='coerce').sum()
            
        ahorro_neto = total_ingresos - total_gastos
        
        # KPIs Principales
        with col_main:
            st.subheader("Resumen Financiero")
            st.metric("💰 Ingresos Totales", f"${total_ingresos:,.0f}")
            st.metric("💸 Egresos Totales", f"${total_gastos:,.0f}")
            st.divider()
            st.metric("🐷 Ahorro Neto", f"${ahorro_neto:,.0f}", 
                     delta="Superávit" if ahorro_neto >= 0 else "Déficit",
                     delta_color="normal" if ahorro_neto >= 0 else "inverse")
                     
        # Gráficos
        with col_chart:
            st.subheader("Flujo de Caja")
            if total_ingresos > 0 or total_gastos > 0:
                chart_data = pd.DataFrame({
                    "Categoría": ["Ingresos", "Egresos"],
                    "Monto": [total_ingresos, total_gastos]
                })
                
                # Gráfico de barras simple
                st.bar_chart(chart_data.set_index("Categoría"), color=["#22c55e", "#ef4444"]) # Verde y Rojo (si soporta lista)
                # Streamlit bar_chart a veces ignora color list si no es dataframe column.
                # Pero la visualización por defecto está bien.
            else:
                st.info("Sin datos suficientes para graficar.")
                
        # Tabla combinada reciente (Opcional)
        st.divider()
        st.subheader("Últimos Movimientos")
        # Aquí podríamos unir los dataframes por fecha y mostrar los últimos 10
        
    except Exception as e:
        st.error(f"Error calculando balance: {e}")

    # ============================================================
    # RENDERIZADO DE MÓDULOS
    # ============================================================
    
    # ... (ingresos y deudas ya definidos arriba) ...

def render_egresos():
    # st.sidebar.markdown("👇 **Panel de Egresos**") # Ya no es necesario con el nuevo layout
    
    # Layout Principal: 3 partes Contenido, 1 parte Panel (Formulario + Filtros)
    col_main, col_panel = st.columns([3, 1])
    
    # ============================================================
    # PANEL DERECHO: FORMULARIO Y FILTROS
    # ============================================================
    with col_panel:
        st.markdown("### 📝 Nuevo Gasto")
        with st.form("formulario_gasto"):
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
                # Lógica de guardado (simplificada para brevedad, usando funciones existentes)
                if concepto and monto > 0:
                    try:
                        # ANALISIS IA
                        score, justificacion, cat_sug, color = 3, "Manual", categoria, "#808080"
                        if concepto:
                            try:
                                from auditor import auditar_gasto
                                score, justificacion, cat_sug, color = auditar_gasto(concepto, monto, divisa)
                            except: pass
                            
                        ws = connect_sheets(0)
                        ws.append_row([
                            str(fecha), concepto, monto, divisa, categoria,
                            "Manual", "Efectivo", "N/A", score, justificacion,
                            recurrencia, "SÍ" if c_alert else "NO"
                        ])
                        st.toast(f"✅ Gasto guardado: {concepto}")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Completa campos básicos.")

        st.divider()
        st.markdown("### 🔍 Filtros")
        
        # Filtros en el panel derecho
        filtro_mes = st.date_input("📅 Rango", [])
        filtro_cat = st.multiselect("📁 Categorías", ["Comida", "Transporte", "Ocio", "Servicios", "Salud", "Ropa", "Educación", "Ahorro", "Otro"])
        
        # Botón Auditoría (Movido aquí)
        if st.button("🚀 Auditar Todo (IA)", use_container_width=True):
            with st.spinner("Analizando..."):
                try:
                    from auditor import run_audit
                    stats = run_audit()
                    st.success(f"Analizados: {stats['processed']}")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Error: {e}")

    # ============================================================
    # CONTENIDO PRINCIPAL: DASHBOARD
    # ============================================================
    with col_main:
        st.title("💸 Gestión de Egresos")
        
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
        
        if not df.empty:
            # --- KPIs ---
            # Calcular totales y conversiones (Lógica existente resumida)
            total_cop = 0
            if 'Monto' in df.columns:
                total_cop = df[df['Divisa']=='COP']['Monto'].sum()
            
            k1, k2, k3 = st.columns(3)
            k1.metric("Total Gastado (COP)", f"${total_cop:,.0f}")
            k2.metric("Registros", len(df))
            
            if 'Score' in df.columns:
                 prom_score = pd.to_numeric(df['Score'], errors='coerce').fillna(0).mean()
                 k3.metric("Score Promedio", f"{prom_score:.1f}/5.0")

            # --- Gráficos ---
            t1, t2 = st.tabs(["📊 Categorías", "📅 Tendencia"])
            with t1:
                if 'Categoria' in df.columns:
                    gastos_cat = df.groupby('Categoria')['Monto'].sum().reset_index() # Simplificado
                    st.bar_chart(gastos_cat.set_index('Categoria'))
            
            with t2:
                if 'Fecha' in df.columns:
                    st.line_chart(df.set_index('Fecha')['Monto']) # Simplificado visual
            
            st.divider()
            
            # --- Tabla --- 
            st.subheader("📝 Detalle de Gastos")
            st.dataframe(df, use_container_width=True)
            
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
                                    background-color: #fee2e2; 
                                    border-left: 5px solid #ef4444; 
                                    padding: 10px; 
                                    margin-bottom: 8px; 
                                    border-radius: 4px;
                                ">
                                    <strong>{pago['concepto']}</strong>: {pago['divisa']} {pago['monto']:,.0f}
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # PAGOS PRÓXIMOS
                        if pagos_proximos:
                            st.subheader("🔔 Próximos Pagos")
                            for pago in pagos_proximos:
                                st.info(f"**{pago['concepto']}**: {pago['divisa']} {pago['monto']:,.0f} el {pago['fecha']} (en {pago['dias_restantes']} días)")
                    except Exception as e:
                        st.error(f"Error en notificaciones: {e}")
            
        else:
            st.info("No hay gastos registrados. Usa el panel derecho para comenzar.")

# ============================================================
# ENRUTAMIENTO FINAL
# ============================================================
if modulo == "📊 Balance":
    render_balance()
elif modulo == "💰 Ingresos":
    render_ingresos()
elif modulo == "💸 Egresos":
    render_egresos()

