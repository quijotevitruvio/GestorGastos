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
st.set_page_config(page_title="Ge$torGasto$", page_icon="💰", layout="wide")

# CSS para mejorar la apariencia
st.markdown("""
<style>
    .stMetric {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #dee2e6;
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

def verificar_login():
    """Muestra el formulario de login si el usuario no está autenticado."""
    if st.session_state["authenticated"]:
        return True
    
    st.title("🔒 Acceso Restringido")
    
    with st.form("formulario_login"):
        usuario = st.text_input("Usuario")
        contraseña = st.text_input("Contraseña", type="password")
        enviado = st.form_submit_button("Entrar")
        
        if enviado:
            if usuario == USUARIO_ADMIN and contraseña == CONTRASEÑA_ADMIN:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
                
    return False

if not verificar_login():
    st.stop()

# ============================================================
# SIDEBAR: CONTROLES PRINCIPALES
# ============================================================
st.sidebar.header("⚙️ Panel de Control")

# Botón cerrar sesión
if st.sidebar.button("🔒 Cerrar Sesión"):
    st.session_state["authenticated"] = False
    st.rerun()

# Botón de Auditoría IA
if st.sidebar.button("🚀 Ejecutar Auditoría IA"):
    with st.spinner("Analizando con Gemini..."):
        try:
            from auditor import run_audit
            estadisticas = run_audit()
            if estadisticas["processed"] > 0:
                st.sidebar.success(f"✅ {estadisticas['processed']} gastos analizados.")
                st.cache_data.clear()
            else:
                st.sidebar.info("👍 Todo al día. No hay gastos pendientes.")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

st.sidebar.divider()

# ============================================================
# FORMULARIO PARA REGISTRAR NUEVOS GASTOS
# ============================================================
with st.sidebar.expander("➕ Registrar Nuevo Gasto", expanded=False):
    with st.form("formulario_gasto"):
        fecha = st.date_input("Fecha")
        concepto = st.text_input("Concepto")
        
        col1, col2 = st.columns([1, 2])
        divisa = col1.selectbox("Divisa", ["COP", "USD", "EUR"])
        monto = col2.number_input("Monto", min_value=0.0, step=100.0 if divisa == "COP" else 1.0)
        
        categoria = st.selectbox("Categoría", [
            "Comida", "Transporte", "Ocio", "Servicios", 
            "Salud", "Ropa", "Educación", "Ahorro", "Otro"
        ])
        lugar = st.text_input("Lugar (Opcional)")
        medio_pago = st.selectbox("Medio de Pago", [
            "Efectivo", "Tarjeta Débito", "Tarjeta Crédito", "Transferencia/Nequi"
        ])
        banco = st.text_input("Banco (Opcional)")
        
        enviado = st.form_submit_button("💾 Guardar Gasto")
        
        if enviado:
            if concepto and monto > 0:
                try:
                    worksheet = connect_sheets()
                    nueva_fila = [str(fecha), concepto, monto, divisa, categoria, lugar, medio_pago, banco]
                    worksheet.append_row(nueva_fila)
                    st.success("¡Gasto guardado!")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Ingresa concepto y monto.")

# ============================================================
# TÍTULO PRINCIPAL
# ============================================================
st.title("💰 Ge$torGasto$ - Auditor Financiero IA")

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
    # TABLA DE DETALLE
    # ============================================================
    st.subheader("📋 Detalle de Gastos")
    
    def colorear_filas(fila):
        try:
            valor = float(fila['ScoreNum'])
            if valor >= 4: 
                return ['background-color: #d4edda'] * len(fila)
            if valor <= 2: 
                return ['background-color: #f8d7da'] * len(fila)
            return [''] * len(fila)
        except:
            return [''] * len(fila)
    
    columnas_mostrar = ['Fecha', 'Concepto', 'Monto', 'Divisa', 'MontoConvertido', 
                        'Categoria', 'MedioPago', 'Score', 'Justificacion']
    columnas_existentes = [c for c in columnas_mostrar if c in df_filtrado.columns]
    
    st.dataframe(
        df_filtrado[columnas_existentes].style.apply(colorear_filas, axis=1),
        use_container_width=True
    )

else:
    st.warning("No hay datos. Asegúrate de que tu Google Sheet tenga contenido.")
