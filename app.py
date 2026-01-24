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

# CSS Minimalista - Estética Neón Limpia
st.markdown("""
<style>
    /* ========== NEON MINIMAL THEME ========== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    :root {
        --bg: #0a0a0a;
        --surface: #111;
        --border: #222;
        --neon-blue: #00d4ff;
        --neon-green: #00ff88;
        --neon-pink: #ff00aa;
        --neon-red: #ff3355;
        --text: #fff;
        --text-dim: #888;
    }
    
    /* Base */
    .stApp { 
        background: var(--bg) !important; 
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] { 
        background: var(--bg) !important;
        border-right: 1px solid var(--border) !important;
    }
    
    /* Métricas - Tarjetas simples con borde neón */
    [data-testid="stMetric"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 20px !important;
    }
    
    [data-testid="stMetric"]:hover {
        border-color: var(--neon-blue) !important;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.2) !important;
    }
    
    [data-testid="stMetricValue"] {
        color: var(--text) !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--text-dim) !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
    }
    
    /* Botones - Neón brillante */
    .stButton > button {
        background: transparent !important;
        color: var(--neon-blue) !important;
        border: 2px solid var(--neon-blue) !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    
    .stButton > button:hover {
        background: var(--neon-blue) !important;
        color: #000 !important;
        box-shadow: 0 0 25px rgba(0, 212, 255, 0.5) !important;
    }
    
    /* Inputs */
    input, textarea, select {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text) !important;
    }
    
    input:focus, textarea:focus {
        border-color: var(--neon-blue) !important;
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.3) !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab"] {
        color: var(--text-dim) !important;
        border-radius: 8px !important;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: var(--neon-blue) !important;
        border-bottom: 2px solid var(--neon-blue) !important;
    }
    
    /* Tablas */
    .stDataFrame {
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--neon-blue); }
    
    /* Headers con glow sutil */
    h1, h2, h3 { 
        color: var(--text) !important;
        font-weight: 700 !important;
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
            
            # --- Tabla Interactiva ---
            st.subheader("Historial")
            
            df_display = df.copy()
            df_display.insert(0, 'Fila', range(2, len(df) + 2))
            
            cols_display = ['Fila', 'Fecha', 'Concepto', 'Monto', 'Divisa', 'Fuente', 'Recurrencia']
            cols_existentes = [c for c in cols_display if c in df_display.columns]
            
            st.markdown("**Selecciona una fila para editar o eliminar:**")
            
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
            
            # Tabla
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
            
            # --- Tabla Interactiva ---
            st.subheader("📋 Detalle de Obligaciones")
            
            # Preparar datos para mostrar
            df_display = df.copy()
            # Obtener índices de fila originales
            df_display.insert(0, 'Fila', range(2, len(df) + 2))
            
            cols_display = ['Fila', 'Tipo', 'Persona', 'Concepto', 'MontoOriginal', 'Divisa', 'Estado', 'FechaLimite']
            cols_existentes = [c for c in cols_display if c in df_display.columns]
            
            st.markdown("**Selecciona una fila para acciones:**")
            
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
            
            # Tabla
            st.dataframe(df_display[cols_existentes], use_container_width=True, height=400)
                    
        else:
            st.info("ℹ️ No hay deudas registradas. Usa el botón superior.")
            
    except Exception as e:
        st.error(f"Error cargando Deudas: {e}")
    
def render_balance():
    st.title("📊 Balance Global")
    
    try:
        # ============================================================
        # CARGAR DATOS DE TODOS LOS MÓDULOS
        # ============================================================
        sh_gastos = connect_sheets(0)
        sh_ingresos = connect_sheets("Ingresos")
        sh_deudas = connect_sheets("Deudas")
        
        df_gastos = pd.DataFrame(sh_gastos.get_all_records())
        df_ingresos = pd.DataFrame(sh_ingresos.get_all_records())
        df_deudas = pd.DataFrame(sh_deudas.get_all_records())
        
        # ============================================================
        # CALCULAR TOTALES
        # ============================================================
        total_ingresos = pd.to_numeric(df_ingresos['Monto'], errors='coerce').sum() if not df_ingresos.empty and 'Monto' in df_ingresos.columns else 0
        total_gastos = pd.to_numeric(df_gastos['Monto'], errors='coerce').sum() if not df_gastos.empty and 'Monto' in df_gastos.columns else 0
        ahorro_neto = total_ingresos - total_gastos
        
        # Deudas
        me_deben = df_deudas[(df_deudas['Tipo'] == 'ME_DEBEN') & (df_deudas['Estado'] == 'PENDIENTE')]['MontoOriginal'].sum() if not df_deudas.empty and 'MontoOriginal' in df_deudas.columns else 0
        yo_debo = df_deudas[(df_deudas['Tipo'] == 'YO_DEBO') & (df_deudas['Estado'] == 'PENDIENTE')]['MontoOriginal'].sum() if not df_deudas.empty and 'MontoOriginal' in df_deudas.columns else 0
        
        # Tasa de ahorro
        tasa_ahorro = (ahorro_neto / total_ingresos * 100) if total_ingresos > 0 else 0
        
        # Score promedio de gastos
        score_promedio = pd.to_numeric(df_gastos['Score'], errors='coerce').mean() if not df_gastos.empty and 'Score' in df_gastos.columns else 0
        
        # ============================================================
        # KPIs PRINCIPALES
        # ============================================================
        k1, k2, k3, k4 = st.columns(4)
        
        k1.metric("💰 Ingresos", f"${total_ingresos:,.0f}")
        k2.metric("💸 Gastos", f"${total_gastos:,.0f}")
        k3.metric("🐷 Ahorro Neto", f"${ahorro_neto:,.0f}", 
                 delta=f"{tasa_ahorro:.1f}% tasa",
                 delta_color="normal" if ahorro_neto >= 0 else "inverse")
        k4.metric("📊 Score IA", f"{score_promedio:.1f}/5.0" if score_promedio else "N/A")
        
        # Segunda fila de KPIs (Deudas)
        k5, k6, k7, k8 = st.columns(4)
        k5.metric("🟢 Me Deben", f"${me_deben:,.0f}")
        k6.metric("🔴 Yo Debo", f"${yo_debo:,.0f}")
        k7.metric("📈 Balance Deuda", f"${me_deben - yo_debo:,.0f}",
                 delta="A favor" if me_deben >= yo_debo else "En contra",
                 delta_color="normal" if me_deben >= yo_debo else "inverse")
        k8.metric("📋 Total Registros", len(df_gastos) + len(df_ingresos) + len(df_deudas))
        
        st.divider()
        
        # ============================================================
        # GRÁFICOS PROFESIONALES
        # ============================================================
        tab_flujo, tab_categorias, tab_tendencia = st.tabs(["💵 Flujo de Caja", "📊 Categorías", "📈 Tendencia"])
        
        with tab_flujo:
            col_bar, col_gauge = st.columns(2)
            
            with col_bar:
                # Gráfico de barras Ingresos vs Egresos
                fig_bar = px.bar(
                    x=["Ingresos", "Gastos"],
                    y=[total_ingresos, total_gastos],
                    color=["Ingresos", "Gastos"],
                    color_discrete_map={"Ingresos": "#22c55e", "Gastos": "#ef4444"},
                    title="Ingresos vs Gastos"
                )
                fig_bar.update_layout(template="plotly_dark", showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with col_gauge:
                # Gauge de tasa de ahorro
                import plotly.graph_objects as go
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=tasa_ahorro,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Tasa de Ahorro (%)"},
                    delta={'reference': 20},  # Meta: 20% de ahorro
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "#3b82f6"},
                        'steps': [
                            {'range': [0, 10], 'color': "#ef4444"},
                            {'range': [10, 20], 'color': "#f59e0b"},
                            {'range': [20, 100], 'color': "#22c55e"}
                        ],
                        'threshold': {
                            'line': {'color': "white", 'width': 4},
                            'thickness': 0.75,
                            'value': 20
                        }
                    }
                ))
                fig_gauge.update_layout(template="plotly_dark", height=300)
                st.plotly_chart(fig_gauge, use_container_width=True)
        
        with tab_categorias:
            if not df_gastos.empty and 'Categoria' in df_gastos.columns:
                gastos_cat = df_gastos.groupby('Categoria')['Monto'].sum().reset_index()
                gastos_cat = gastos_cat.sort_values('Monto', ascending=False)
                
                col_pie, col_bars = st.columns(2)
                
                with col_pie:
                    fig_pie = px.pie(gastos_cat, values='Monto', names='Categoria', 
                                     hole=0.4, title="Distribución de Gastos")
                    fig_pie.update_layout(template="plotly_dark")
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col_bars:
                    fig_hbar = px.bar(gastos_cat.head(5), x='Monto', y='Categoria', 
                                      orientation='h', title="Top 5 Categorías",
                                      color='Monto', color_continuous_scale='Reds')
                    fig_hbar.update_layout(template="plotly_dark", showlegend=False)
                    st.plotly_chart(fig_hbar, use_container_width=True)
            else:
                st.info("No hay datos de gastos para mostrar.")
        
        with tab_tendencia:
            # Combinar ingresos y gastos por fecha
            df_trend = pd.DataFrame()
            
            if not df_gastos.empty and 'Fecha' in df_gastos.columns:
                df_g = df_gastos.copy()
                df_g['Fecha'] = pd.to_datetime(df_g['Fecha'], errors='coerce')
                df_g = df_g.dropna(subset=['Fecha'])
                df_g = df_g.groupby(df_g['Fecha'].dt.to_period('M')).agg({'Monto': 'sum'}).reset_index()
                df_g['Fecha'] = df_g['Fecha'].astype(str)
                df_g['Tipo'] = 'Gastos'
                df_trend = pd.concat([df_trend, df_g])
            
            if not df_ingresos.empty and 'Fecha' in df_ingresos.columns:
                df_i = df_ingresos.copy()
                df_i['Fecha'] = pd.to_datetime(df_i['Fecha'], errors='coerce')
                df_i = df_i.dropna(subset=['Fecha'])
                df_i = df_i.groupby(df_i['Fecha'].dt.to_period('M')).agg({'Monto': 'sum'}).reset_index()
                df_i['Fecha'] = df_i['Fecha'].astype(str)
                df_i['Tipo'] = 'Ingresos'
                df_trend = pd.concat([df_trend, df_i])
            
            if not df_trend.empty:
                fig_line = px.line(df_trend, x='Fecha', y='Monto', color='Tipo',
                                   markers=True, title="Tendencia Mensual",
                                   color_discrete_map={'Ingresos': '#22c55e', 'Gastos': '#ef4444'})
                fig_line.update_layout(template="plotly_dark")
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("No hay suficientes datos para mostrar tendencia.")
        
        st.divider()
        
        # ============================================================
        # ÚLTIMOS MOVIMIENTOS
        # ============================================================
        st.subheader("📋 Últimos Movimientos")
        
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
            st.info("No hay movimientos registrados.")
                
    except Exception as e:
        st.error(f"Error calculando balance: {e}")
        import traceback
        st.code(traceback.format_exc())

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
    col_layout, _ = st.columns([1, 4])
    if col_layout.button("➕ Registrar Nuevo Gasto", use_container_width=True, type="primary"):
        dialog_gasto()
    
    # ============================================================
    # PANEL DE CONTROL (FILTROS)
    # ============================================================
    with st.expander("🔍 Filtros y Herramientas", expanded=False):
        f1, f2, f3 = st.columns(3)
        filtro_mes = f1.date_input("📅 Rango", [])
        filtro_cat = f2.multiselect("📁 Categorías", ["Comida", "Transporte", "Ocio", "Servicios", "Salud", "Ropa", "Educación", "Ahorro", "Otro"])
        
        if f3.button("🚀 Auditar Todo (IA)", use_container_width=True):
            with st.spinner("Analizando..."):
                try:
                    from auditor import run_audit
                    stats = run_audit()
                    st.success(f"Analizados: {stats['processed']}")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Error: {e}")

    # ============================================================
    # CONTENIDO PRINCIPAL: DASHBOARD (Full Width)
    # ============================================================
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
        
        # --- Tabla Interactiva con Selección --- 
        st.subheader("📝 Detalle de Gastos")
        
        # Agregar índice de fila para referencia
        df_display = df.copy()
        df_display.insert(0, 'Fila', range(2, len(df) + 2))  # +2 porque Sheet es 1-indexed + header
        
        # Columnas a mostrar
        cols_display = ['Fila', 'Fecha', 'Concepto', 'Monto', 'Divisa', 'Categoria', 'Score', 'Justificacion']
        cols_existentes = [c for c in cols_display if c in df_display.columns]
        
        # Selector de fila para acciones
        st.markdown("**Selecciona una fila para editar o eliminar:**")
        
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
        
        # Mostrar tabla de solo lectura
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
if modulo == "📊 Balance":
    render_balance()
elif modulo == "💰 Ingresos":
    render_ingresos()
elif modulo == "💸 Egresos":
    render_egresos()
elif modulo == "🤝 Deudas":
    render_deudas()
