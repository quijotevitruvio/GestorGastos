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
# IMPORTACIÓN DE LIBRERÍAS (BIBLIOTECAS)
# ============================================================
import streamlit as st       # Interfaz principal de la aplicación
import pandas as pd          # Procesamiento y análisis de datos tabulares
import plotly.express as px  # Creación de gráficas interactivas
import gspread               # Sincronización con hojas de cálculo de Google
import json                  # Manejo de formatos de datos JSON
import base64                # Codificación de recursos (como imágenes)
import time                  # Manejo de tiempos y pausas
import hashlib               # Hashing de contraseñas (SHA-256)
import os                    # Gestión de archivos y variables del sistema
from datetime import datetime, timedelta # Manejo de fechas y periodos de tiempo
from dotenv import load_dotenv  # Carga de variables sensibles desde el archivo .env
from currency import convertir_columna, formatear_moneda, obtener_tasas  # Conversión de divisas
from validators import (  # Validación de datos
    sanitizar_texto, validar_monto, validar_fecha, validar_concepto,
    validar_formulario_gasto, validar_formulario_ingreso, validar_formulario_deuda
)
from utils import obtener_secreto, connect_sheets_utility, clean_json_string, CHAT_SYSTEM_PROMPT
import actions

# ============================================================
# CONFIGURACIÓN INICIAL DE LA APP
# ============================================================
load_dotenv()
st.set_page_config(page_title="Ge$torGasto$", page_icon="assets/logo.jpg", layout="wide")

# CSS Premium - Estética Moderna con Glassmorphism
# CSS Premium - Estética Moderna con Glassmorphism
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

try:
    local_css("style.css")
except Exception as e:
    st.error(f"Error cargando estilos: {e}")


# ============================================================
# FUNCIONES DE SEGURIDAD (SECRETOS)
# ============================================================
# Esta parte permite que la app funcione tanto en tu PC (usando .env)
# como en la nube (usando la configuración de Streamlit Cloud).


# ============================================================
# FUNCIONES DE SEGURIDAD (SECRETOS)
# ============================================================
# Función 'obtener_secreto' importada de utils.py

# ============================================================
# CONEXIÓN CON GOOGLE SHEETS
# ============================================================
# ============================================================
# CONEXIÓN CON GOOGLE SHEETS
# ============================================================
@st.cache_resource(ttl=3600)
@st.cache_resource(ttl=3600)
def connect_sheets_cached(target_sheet=0):
    """Interfaz con caché para la utilidad de conexión."""
    return connect_sheets_utility(target_sheet)

def connect_sheets(target_sheet=0):
    """Wrapper compatible."""
    return connect_sheets_cached(target_sheet)

@st.cache_data(ttl=60)
def get_data(sheet_name=0):
    """Obtiene los registros de una hoja usando caché de datos."""
    ws = connect_sheets(sheet_name)
    return ws.get_all_records()

# ============================================================
# ============================================================
# SISTEMA DE SEGURIDAD Y ACCESO (LOGIN)
# ============================================================
# Cargamos las credenciales maestras desde los secretos
USUARIO_ADMIN = obtener_secreto("ADMIN_USER")
CONTRASEÑA_ADMIN = obtener_secreto("ADMIN_PASSWORD")

# Inicializamos el estado de la sesión si es la primera vez que entramos
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Librería para manejar "cookies" y recordar la sesión del usuario
import extra_streamlit_components as stx

def get_base64_bin_file(bin_file):
    """Convierte un archivo binario (como una imagen) en texto Base64 para usarlo en el diseño."""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def verificar_login():
    """Controla la pantalla de acceso con Registro y Login Seguro."""
    
    # 1. Inicializar Cookie Manager
    cookie_manager = stx.CookieManager()
    
    # 2. Verificar cookie de sesión existente
    if not st.session_state.get("authenticated", False):
        cookies = cookie_manager.get_all()
        if cookies.get("gestor_gastos_auth") == "true":
            # Si hay cookie, intentamos recuperar el rol (idealmente la cookie sería un token seguro)
            # Por simplicidad, asumimos rol USER si no hay más data, o ADMIN si coincide con secretos
            st.session_state["authenticated"] = True
            st.session_state["rol"] = "USER" # Default seguro
            return True

    if st.session_state.get("authenticated", False):
        return True
    
    # 3. Mostrar Login / Registro
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
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div style='height: 5vh'></div>", unsafe_allow_html=True)
        
        # Tabs para Login / Registro
        tab_login, tab_registro = st.tabs(["🔑 Iniciar Sesión", "📝 Solicitar Acceso"])
        
        with tab_login:
            with st.container():
                st.markdown("""
                    <div style='text-align: center; margin-bottom: 2rem;'>
                        <h1 style='color: #c8ff00; font-size: 3rem; margin: 0;'>Ge$torGasto$</h1>
                        <p>Control Financiero Inteligente</p>
                    </div>
                """, unsafe_allow_html=True)
                
                with st.form("form_login"):
                    usuario = st.text_input("Usuario")
                    password = st.text_input("Contraseña", type="password")
                    recordarme = st.checkbox("Recordarme")
                    
                    if st.form_submit_button("Entrar", use_container_width=True):
                        try:
                            # Autenticación Dual: Secretos (Admin Maestro) o Google Sheets
                            auth_success = False
                            rol_detectado = "USER"
                            
                            # 1. Check Secretos (Admin Backup)
                            if usuario == USUARIO_ADMIN and password == CONTRASEÑA_ADMIN:
                                auth_success = True
                                rol_detectado = "ADMIN"
                            else:
                                # 2. Check Google Sheets
                                pass_hash = hashlib.sha256(password.encode()).hexdigest()
                                df_users = pd.DataFrame(get_data("Usuarios"))
                                
                                user_row = df_users[df_users['Usuario'] == usuario]
                                if not user_row.empty:
                                    stored_hash = user_row.iloc[0]['Password_Hash']
                                    estado = user_row.iloc[0]['Estado']
                                    rol = user_row.iloc[0]['Rol']
                                    
                                    if str(stored_hash) == pass_hash:
                                        if estado == "ACTIVO":
                                            auth_success = True
                                            rol_detectado = rol
                                        else:
                                            st.warning("⚠️ Tu cuenta está PENDIENTE de aprobación.")
                                    else:
                                        st.error("❌ Contraseña incorrecta")
                                else:
                                    st.error("❌ Usuario no encontrado")
                            
                            if auth_success:
                                st.session_state["authenticated"] = True
                                st.session_state["rol"] = rol_detectado
                                if recordarme:
                                    cookie_manager.set("gestor_gastos_auth", "true", expires_at=datetime.now() + timedelta(days=30))
                                st.rerun()
                                
                        except Exception as e:
                            st.error(f"Error de conexión: {e}")

        with tab_registro:
            st.markdown("### 🆕 Crear Nueva Cuenta")
            st.info("ℹ️ Tu cuenta deberá ser aprobada por un administrador.")
            
            with st.form("form_registro"):
                new_user = st.text_input("Elige un Usuario")
                new_pass = st.text_input("Contraseña", type="password")
                confirm_pass = st.text_input("Confirmar Contraseña", type="password")
                
                if st.form_submit_button("Solicitar Acceso", use_container_width=True):
                    if new_pass != confirm_pass:
                        st.error("❌ Las contraseñas no coinciden")
                    elif len(new_pass) < 6:
                        st.error("⚠️ La contraseña debe tener al menos 6 caracteres")
                    elif not new_user:
                        st.error("⚠️ El usuario es obligatorio")
                    else:
                        try:
                            sh_users = connect_sheets("Usuarios")
                            todos_usuarios = sh_users.col_values(1) # Columna de usuarios
                            
                            if new_user in todos_usuarios:
                                st.error("❌ Este usuario ya existe")
                            else:
                                # Crear usuario pendiente
                                pass_hash_new = hashlib.sha256(new_pass.encode()).hexdigest()
                                sh_users.append_row([
                                    new_user, 
                                    pass_hash_new, 
                                    "USER", 
                                    "PENDIENTE", 
                                    str(datetime.now())
                                ])
                                st.success("✅ ¡Solicitud enviada! Avisa al administrador para que te apruebe.")
                                st.balloons()
                        except Exception as e:
                            st.error(f"Error al registrar: {e}")

    return False

if not verificar_login():
    st.stop()

# ============================================================
# INTERFAZ PRINCIPAL - SIDEBAR (BARRA LATERAL)
# ============================================================
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <p style="color: #c8ff00; font-size: 0.8rem; margin: 0; letter-spacing: 2px;">EDICIÓN PREMIUM</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### NAVEGACIÓN PRINCIPAL")
    
    # Definir opciones de menú según rol
    opciones_menu = ["🏠 Inicio", "📒 Movimientos", "💼 Mi Patrimonio", "🤖 Asistente IA"]
    
    # Mostrar Panel Admin SOLO si es admin
    if st.session_state.get("rol") == "ADMIN":
        opciones_menu.append("👮 Panel Admin")
    
    # Menú de navegación
    modulo = st.radio(
        "Ir a:",
        opciones_menu,
        label_visibility="collapsed",
        key="navegacion_principal"
    )

    st.markdown("---")
    
    # Espaciador para empujar el botón de logout al fondo (en pantallas altas)
    st.markdown("<div style='margin-top: 5vh;'></div>", unsafe_allow_html=True)
    
    # Botón de cierre de sesión (al final)
    if st.button("🚪 Cerrar Sesión Segura", key="boton_logout", use_container_width=True):
        st.session_state["authenticated"] = False
        cookie_manager.delete("gestor_gastos_auth")
        st.rerun()

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
        monto = c2.number_input("Monto", value=None, min_value=0.0, step=100.0, format="%.2f", key="ing_monto")
        
        fuente = st.selectbox("Fuente", ["Nómina", "Negocio", "Inversión", "Regalo", "Otros"])
        recurrencia = st.selectbox("Frecuencia", ["Único", "Mensual", "Quincenal", "Anual"], index=1)
        comentario = st.text_area("Notas", height=2)
        
        if st.form_submit_button("💾 Guardar Ingreso", use_container_width=True):
            if monto and monto > 0 and concepto:
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
    st.subheader("💰 Gestión de Ingresos")
    
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
    # --- Ver Datos (Full Width) ---
    try:
        records = get_data("Ingresos")
        
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
                    new_monto = c2.number_input("Monto", value=float(datos.get('Monto', 0)), min_value=0.0, step=100.0, format="%.2f")
                    
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
        monto = c2.number_input("Monto", value=None, min_value=0.0, step=100.0, format="%.2f")
        
        fecha_limite = st.date_input("Vence", key="modal_dd_limite")
        comentario = st.text_area("Notas", height=1)
        alerta = st.checkbox("🔔 Alerta", value=True)
        
        if st.form_submit_button("💾 Guardar", use_container_width=True):
            if persona and monto and monto > 0:
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
    st.subheader("🤝 Control de Deudas")
    
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
    # --- Main Content: Dashboard (Full Width) ---
    try:
        records = get_data("Deudas")
        
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
                    new_monto = c2.number_input("Monto", value=float(datos.get('MontoOriginal', 0)), min_value=0.0, step=100.0, format="%.2f")
                    
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
        
        # Construir HTML del Dashboard (Sin saltos de línea para evitar errores de renderizado)
        html_dashboard = f"""
        <div class="patrimonio-card animate-slide-up">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
                <div>
                    <p style="margin: 0; font-size: 0.85rem; opacity: 0.7; font-weight: 500;">Patrimonio Total 👁</p>
                    <h1 style="margin: 8px 0 0 0; font-size: 2.8rem; font-weight: 800; color: #000;">{patrimonio_fmt}</h1>
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
                    <span style="font-size: 0.75rem; opacity: 0.6;">Ingresos</span>
                    <p style="margin: 0; font-size: 1.1rem; font-weight: 600; color: #22c55e;">↑ {ingresos_fmt}</p>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 0.75rem; opacity: 0.6;">Gastos</span>
                    <p style="margin: 0; font-size: 1.1rem; font-weight: 600; color: #ef4444;">↓ {gastos_fmt}</p>
                </div>
            </div>
        </div>
        """.replace('\n', '').replace('    ', '')
        
        st.markdown(html_dashboard, unsafe_allow_html=True)
        
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
        st.subheader("🏦 Gestión de Cuentas")
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
        saldo = c2.number_input("Saldo inicial", value=None, min_value=0.0, step=10000.0, format="%.2f")
        
        divisa = st.selectbox("Divisa", ["COP", "USD", "EUR"])
        
        if st.form_submit_button("💾 Guardar", use_container_width=True):
            if nombre and saldo is not None:
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
        records = get_data("Cuentas")
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
        
        monto = st.number_input("💰 Monto a transferir", value=None, min_value=0.0, step=10000.0, format="%.2f")
        concepto = st.text_input("📝 Concepto (opcional)", placeholder="Ej: Ahorro mensual...")
        
        if st.form_submit_button("✅ Realizar Transferencia", use_container_width=True, type="primary"):
            if cuenta_origen == cuenta_destino:
                st.error("❌ La cuenta de origen y destino deben ser diferentes")
            elif not monto or monto <= 0:
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
        st.subheader("🐷 Bolsillos de Ahorro")
        st.caption("Ahorra para tus metas y sueños")
    
    # Botón para crear
    col_btn, _ = st.columns([1, 4])
    if col_btn.button("➕ Crear Bolsillo", use_container_width=True, type="primary"):
        dialog_bolsillo()
    
    try:
        # Intentar cargar hoja Bolsillos
        try:
            records = get_data("Bolsillos")
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
        meta = c1.number_input("Meta de ahorro", value=None, min_value=0.0, step=50000.0, format="%.2f")
        icono = c2.selectbox("Icono", ["Casa", "Viaje", "Auto", "Educación", "Emergencia", "Otro"])
        
        ahorrado_inicial = st.number_input("Ahorro inicial (opcional)", value=None, min_value=0.0, step=10000.0, format="%.2f")
        
        if st.form_submit_button("💾 Crear Bolsillo", use_container_width=True):
            if nombre and meta and meta > 0:
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
                    sh.append_row([id_bolsillo, nombre, meta, ahorrado_inicial if ahorrado_inicial else 0, icono, "#c8ff00", str(datetime.now().date())])
                    
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
    
    # Header & Personalidad
    c1, c2 = st.columns([1, 4])
    with c1:
        try: st.image("assets/icon_ai.png", width=80)
        except: st.write("🤖")
    with c2:
        st.subheader("Asistente Financiero")
        # Selector de Personalidad
        modos = list(utils.PERSONALITY_PROMPTS.keys())
        if "ai_mood" not in st.session_state: st.session_state.ai_mood = "Neutro"
        
        c_mood, c_info = st.columns([2, 3])
        with c_mood:
            st.session_state.ai_mood = st.selectbox("Temperamento:", modos, index=modos.index(st.session_state.ai_mood), key="sb_mood", label_visibility="collapsed")
        with c_info:
            st.caption(f"Modo: *{st.session_state.ai_mood}*")

    st.divider()

    # Inicializar historial
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Renderizar historial
    for msg in st.session_state.chat_history:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

    # --- ZONA DE CONFIRMACIÓN DE ACCIÓN ---
    if st.session_state.get('pending_action'):
        action = st.session_state.pending_action
        intent = action.get('intent')
        data = action.get('data', {})
        
        with st.status(f"🤔 Confirmar {intent.upper()}", expanded=True):
            st.json(data)
            
            c_conf, c_canc = st.columns(2)
            if c_conf.button("✅ Confirmar", use_container_width=True, type="primary"):
                try:
                    res = {'success': False, 'message': 'Error desconocido'}
                    if intent == 'gasto':
                        res = actions.add_expense(
                            fecha=datetime.now().date(),
                            concepto=data.get('concepto'),
                            monto=data.get('monto'),
                            divisa=data.get('divisa', 'COP'),
                            categoria=data.get('categoria', 'Otros'),
                            medio_pago=data.get('medio_pago', 'Efectivo'),
                            banco=data.get('banco', 'N/A'),
                            lugar=data.get('lugar', 'N/A')
                        )
                    elif intent == 'ingreso':
                        res = actions.add_income(
                            fecha=datetime.now().date(),
                            concepto=data.get('concepto'),
                            monto=data.get('monto'),
                            divisa=data.get('divisa', 'COP'),
                            fuente=data.get('fuente', 'Otros')
                        )
                    elif intent == 'deuda':
                        res = actions.add_debt(
                            tipo_operacion=data.get('tipo', 'YO_DEBO'),
                            persona=data.get('persona'),
                            concepto=data.get('concepto', 'Préstamo'),
                            monto=data.get('monto'),
                            divisa=data.get('divisa', 'COP'),
                            fecha_limite=datetime.now().date() + timedelta(days=30)
                        )
                    
                    if res['success']:
                        st.session_state.chat_history.append({'role': 'assistant', 'content': f"✅ {res['message']}"})
                        st.toast(res['message'])
                        st.cache_data.clear()
                    else:
                        st.session_state.chat_history.append({'role': 'assistant', 'content': f"❌ {res['message']}"})
                
                except Exception as e:
                    st.session_state.chat_history.append({'role': 'assistant', 'content': f"❌ Error: {str(e)}"})

                st.session_state.pending_action = None
                st.rerun()

            if c_canc.button("❌ Cancelar", use_container_width=True):
                st.session_state.chat_history.append({'role': 'assistant', 'content': "❌ Cancelado."})
                st.session_state.pending_action = None
                st.rerun()

    # Input de chat
    if prompt := st.chat_input("Escribe tu movimiento..."):
        procesar_pregunta_ia(prompt, st.session_state.ai_mood)
        st.rerun()

def procesar_pregunta_ia(pregunta, modo="Neutro"):
    """Procesa una pregunta del usuario con IA."""
    st.session_state.chat_history.append({'role': 'user', 'content': pregunta})
    
    try:
        import google.generativeai as genai
        GEMINI_API_KEY = obtener_secreto("GEMINI_API_KEY")
        
        if not GEMINI_API_KEY:
             st.session_state.chat_history.append({'role': 'assistant', 'content': "⚠️ No encuentro la GEMINI_API_KEY. Configurala en .env o secrets."})
             return

        genai.configure(api_key=GEMINI_API_KEY)
        # Usamos un modelo disponible confirmado
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Contexto financiero actual
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        
        # Inyectar instrucción de personalidad
        p_instruction = utils.PERSONALITY_PROMPTS.get(modo, utils.PERSONALITY_PROMPTS["Neutro"])
        full_prompt = CHAT_SYSTEM_PROMPT.format(
            fecha_actual=fecha_actual,
            personality_instruction=p_instruction
        )
        # Enviar historial reciente para contexto
        historial_texto = json.dumps([m for m in st.session_state.chat_history[-6:] if m['role'] != 'system'])
        full_prompt += f"\n\nHISTORIAL:\n{historial_texto}\n\nUSUARIO: {pregunta}"
        
        response = model.generate_content(full_prompt)
        text_response = response.text
        
        # Procesar JSON
        json_str = clean_json_string(text_response)
        try:
            result = json.loads(json_str)
            intent = result.get('intent')
            response_text = result.get('response')
            missing = result.get('missing_info', [])
            
            if intent in ['gasto', 'ingreso', 'deuda'] and not missing:
                # LISTO PARA CONFIRMAR
                st.session_state.pending_action = result
                st.session_state.chat_history.append({'role': 'assistant', 'content': response_text})
            else:
                # CONSULTA, ERROR O FALTAN DATOS
                st.session_state.chat_history.append({'role': 'assistant', 'content': response_text})
                
        except json.JSONDecodeError:
            # Fallback si no devuelve JSON
            st.session_state.chat_history.append({'role': 'assistant', 'content': text_response})

    except Exception as e:
        st.session_state.chat_history.append({'role': 'assistant', 'content': f"⚠️ Error: {str(e)}"})

    # ... (ingresos y deudas ya definidos arriba) ...

@st.dialog("💸 Registrar Nuevo Gasto")
def dialog_gasto():
    with st.form("formulario_gasto_modal"):
        fecha = st.date_input("📅 Fecha")
        concepto = st.text_input("📝 Concepto")
        
        c1, c2 = st.columns(2)
        divisa = c1.selectbox("Divisa", ["COP", "USD", "EUR"])
        monto = c2.number_input("Monto", value=None, min_value=0.0, step=100.0, format="%.2f")
        
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
            # Si monto es None, validación fallará en funciones que esperan número, así que validamos aquí primero
            if not monto:
                st.warning("El monto es obligatorio")
            else:
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
    st.subheader("💸 Gestión de Egresos")
    
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
                new_monto = c2.number_input("Monto", value=float(datos.get('Monto', 0)), min_value=0.0, step=100.0, format="%.2f")
                
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
# FUNCIONES DE RENDERIZADO UNIFICADAS (NUEVO DISEÑO)
# ============================================================

def render_movimientos():
    """Vista unificada de Ingresos y Gastos."""
    st.title("📒 Movimientos Financieros")
    
    tab_gastos, tab_ingresos = st.tabs(["📉 Gastos", "📈 Ingresos"])
    
    with tab_gastos:
        render_egresos()
        
    with tab_ingresos:
        render_ingresos()

def render_patrimonio():
    """Vista unificada de Cuentas, Ahorros y Deudas."""
    st.title("💼 Mi Patrimonio")
    
    # Cálculos rápidos de Patrimonio Neto
    try:
        sh_cuentas = connect_sheets("Cuentas")
        df_cuentas = pd.DataFrame(sh_cuentas.get_all_records())
        total_activos = pd.to_numeric(df_cuentas['Saldo'], errors='coerce').sum() if not df_cuentas.empty else 0
        
        sh_bolsillos = connect_sheets("Bolsillos")
        df_bolsillos = pd.DataFrame(sh_bolsillos.get_all_records())
        total_ahorros = pd.to_numeric(df_bolsillos['Ahorrado'], errors='coerce').sum() if not df_bolsillos.empty else 0
        
        sh_deudas = connect_sheets("Deudas")
        df_deudas = pd.DataFrame(sh_deudas.get_all_records())
        total_pasivos = df_deudas[(df_deudas['Tipo'] == 'YO_DEBO') & (df_deudas['Estado'] == 'PENDIENTE')]['MontoOriginal'].sum() if not df_deudas.empty and 'MontoOriginal' in df_deudas.columns else 0
        
        patrimonio_neto = (total_activos + total_ahorros) - total_pasivos
        
        st.markdown(f"""
        <div class="patrimonio-card" style="margin-bottom: 24px;">
            <p style="margin: 0; opacity: 0.8; font-size: 0.9rem;">Patrimonio Neto Real</p>
            <h1 style="margin: 4px 0 16px 0; font-size: 2.8rem; font-weight: 800;">${patrimonio_neto:,.0f}</h1>
            
            <div style="display: flex; gap: 20px;">
                <div>
                    <span style="color: #22c55e; font-weight: 600;">+ ${(total_activos + total_ahorros):,.0f}</span>
                    <br><small style="opacity: 0.6;">Activos (Cuentas + Ahorro)</small>
                </div>
                <div>
                    <span style="color: #ef4444; font-weight: 600;">- ${total_pasivos:,.0f}</span>
                    <br><small style="opacity: 0.6;">Pasivos (Deudas)</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Error calculando patrimonio: {e}")

    # Layout Principal
    col_izq, col_der = st.columns([1, 1])
    
    with col_izq:
        with st.expander("🏦 Cuentas Bancarias y Efectivo", expanded=True):
            render_cuentas()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.expander("💎 Bolsillos de Ahorro", expanded=True):
            render_bolsillos()
            
    with col_der:
        with st.expander("🤝 Gestión de Deudas", expanded=True):
            render_deudas()



# ============================================================
# GESTIÓN DE PRESUPUESTOS
# ============================================================
def render_presupuestos():
    st.title("📊 Control de Presupuestos")
    st.caption("Define límites mensuales para tus gastos y monitorea tu progreso.")
    
    # 1. VISUALIZACIÓN DE PROGRESO
    st.subheader("Estado del Mes")
    
    with st.spinner("Calculando gastos vs presupuestos..."):
        status = actions.get_budget_status()
    
    if not status:
        st.info("No hay presupuestos definidos o no se pudieron calcular.")
    else:
        for item in status:
            cat = item['categoria']
            limite = item['limite']
            gastado = item['gastado']
            pct = item['porcentaje'] / 100
            pct_visual = min(pct, 1.0)
            
            # Color basado en porcentaje
            color_bar = "#22c55e" # Verde
            if pct > 0.75: color_bar = "#f59e0b" # Naranja
            if pct > 0.90: color_bar = "#ef4444" # Rojo
            
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"**{cat}**")
                st.progress(pct_visual)
            with c2:
                st.write(f"${gastado:,.0f} / ${limite:,.0f}")
                if pct > 1.0:
                    st.caption(f"⚠️ +${(gastado-limite):,.0f}")
            
            st.write("") # Espacio
            
    st.divider()
    
    # 2. CONFIGURACIÓN DE LÍMITES
    with st.expander("⚙️ Configurar Nuevos Límites"):
        with st.form("form_set_budget"):
            st.write("Establecer o actualizar presupuesto mensual:")
            cats = ["Comida", "Transporte", "Ocio", "Servicios", "Salud", "Ropa", "Educación", "Ahorro", "Otro"]
            
            col_cat, col_monto = st.columns(2)
            s_cat = col_cat.selectbox("Categoría", cats)
            s_monto = col_monto.number_input("Límite Mensual ($)", min_value=0.0, step=50000.0)
            
            if st.form_submit_button("Guardar Presupuesto", use_container_width=True):
                res = actions.set_budget(s_cat, s_monto)
                if res['success']:
                    st.success(res['message'])
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(res['message'])


# ============================================================
# GESTIÓN DE SUSCRIPCIONES
# ============================================================
@st.dialog("📅 Nueva Suscripción")
def dialog_suscripcion():
    with st.form("form_suscripcion"):
        servicio = st.text_input("Servicio", placeholder="Netflix, Spotify, Gym...")
        
        c1, c2 = st.columns(2)
        monto = c1.number_input("Monto", min_value=0.0, step=1000.0)
        divisa = c2.selectbox("Divisa", ["COP", "USD", "EUR"])
        
        c3, c4 = st.columns(2)
        periodo = c3.selectbox("Frecuencia", ["Mensual", "Anual"])
        dia_cobro = c4.number_input("Día de Cobro", 1, 31, 1)
        
        if st.form_submit_button("Guardar Suscripción", use_container_width=True):
            res = actions.add_subscription(servicio, monto, divisa, periodo, dia_cobro)
            if res['success']:
                st.success(res['message'])
                time.sleep(1)
                st.rerun()
            else:
                st.error(res['message'])

def render_suscripciones():
    st.title("📅 Suscripciones Recurrentes")
    
    # KPI Principal
    costo_mensual = actions.get_monthly_fixed_cost()
    st.metric("Costo Fijo Mensual (Aprox)", f"${costo_mensual:,.0f} COP")
    
    # Listado
    st.subheader("Tus Servicios Activos")
    
    subs = actions.get_subscriptions()
    if not subs:
        st.info("No tienes suscripciones registradas.")
    else:
        df = pd.DataFrame(subs)
        # Mostrar como Dataframe interactivo o Tarjetas
        # Vamos a usar tarjetas para poder borrar más fácil
        for i, sub in df.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1])
                with c1:
                    st.write(f"**{sub['Servicio']}**")
                    st.caption(f"{sub['Periodo']} - Día {sub['Fecha_Cobro']}")
                with c2:
                    st.write(f"{sub['Divisa']} {sub['Monto']}")
                with c3:
                    if st.button("🗑️", key=f"del_sub_{i}"):
                        # gspread es 1-based y row 1 es header, asi que index + 2
                        res = actions.delete_subscription(i + 2)
                        st.toast(res['message'])
                        time.sleep(1)
                        st.rerun()

    st.divider()
    if st.button("➕ Agregar Suscripción", use_container_width=True):
        dialog_suscripcion()

# ============================================================
# PANEL DE ADMINISTRACIÓN (SOLO ADMINS)
# ============================================================
def render_admin_panel():
    """Panel exclusivo para aprobar usuarios."""
    st.title("👮 Panel de Administración")
    
    if st.session_state.get("rol") != "ADMIN":
        st.error("⛔ Acceso Denegado. Se requiere rol de Administrador.")
        return

    try:
        # 2. Check Google Sheets
        sh_users = connect_sheets("Usuarios")
        df_users = pd.DataFrame(get_data("Usuarios"))
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("👥 Usuarios Pendientes")
            pendientes = df_users[df_users['Estado'] == 'PENDIENTE'] or pd.DataFrame() # Handle if empty/error
            # Fix: pendientes could be empty Series or DataFrame.
            # If df_users is empty, this fails.
            if df_users.empty:
                 pendientes = pd.DataFrame()
            else:
                 pendientes = df_users[df_users['Estado'] == 'PENDIENTE']
        
        if pendientes.empty:
            st.info("✅ No hay solicitudes pendientes.")
        else:
            for index, row in pendientes.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div style="background: #222; padding: 16px; border-radius: 12px; border: 1px solid #444; margin-bottom: 10px;">
                        <h3 style="margin: 0; color: #fff;">👤 {row['Usuario']}</h3>
                        <small>Fecha: {row['Fecha_Registro']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2, c3 = st.columns([1.5, 1, 1])
                    with c1:
                        nuevo_rol = st.selectbox("Rol Asignado", ["USER", "ADMIN"], key=f"rol_{row['Usuario']}")
                    with c2:
                        if st.button(f"✅ Aprobar", key=f"apr_{row['Usuario']}", type="primary"):
                            cell = sh_users.find(row['Usuario'])
                            sh_users.update_cell(cell.row, 3, nuevo_rol) # Columna 3 es Rol
                            sh_users.update_cell(cell.row, 4, "ACTIVO") # Columna 4 es Estado
                            st.toast(f"Usuario {row['Usuario']} aprobado como {nuevo_rol}.")
                            time.sleep(1)
                            st.rerun()
                    with c3:
                        if st.button(f"❌ Rechazar", key=f"rej_{row['Usuario']}"):
                            cell = sh_users.find(row['Usuario'])
                            sh_users.delete_rows(cell.row)
                            st.toast(f"Usuario {row['Usuario']} rechazado.")
                            time.sleep(1)
                            st.rerun()

        with col2:
            st.subheader("📊 Estadísticas")
            if not df_users.empty:
                st.metric("Total Usuarios", len(df_users))
                st.metric("Activos", len(df_users[df_users['Estado'] == 'ACTIVO']))
                st.metric("Pendientes", len(pendientes))
            
    except Exception as e:
        st.error(f"Error cargando usuarios: {e}")



# ============================================================
# SIMULADOR DE ESCENARIOS
# ============================================================
def render_simulador():
    st.title("🔮 Simulador Financiero")
    st.caption("Proyecta tu futuro financiero y juega con '¿Qué pasaría si...?'")
    
    tab1, tab2 = st.tabs(["🚀 Meta de Ahorro", "🔥 Libertad Financiera"])
    
    with tab1:
        st.subheader("Calculadora de Metas")
        c1, c2 = st.columns(2)
        meta = c1.number_input("¿Cuánto quieres ahorrar?", value=10000000.0, step=500000.0)
        ahorro_actual = c2.number_input("Ahorro Actual", value=0.0, step=100000.0)
        
        c3, c4 = st.columns(2)
        ahorro_mensual = c3.number_input("Ahorro Mensual Posible", value=500000.0, step=50000.0)
        tasa_anual = c4.slider("Rentabilidad Anual Esperada (%)", 0.0, 15.0, 10.0)
        
        if ahorro_mensual > 0:
            # Cálculo simple de interés compuesto mensual
            r_mensual = (tasa_anual / 100) / 12
            meses = 0
            saldo = ahorro_actual
            data_proy = []
            
            while saldo < meta and meses < 360: # Max 30 años
                saldo = saldo * (1 + r_mensual) + ahorro_mensual
                meses += 1
                if meses % 6 == 0: # Guardar datos cada 6 meses para gráfica no muy densa
                    data_proy.append({"Mes": meses, "Saldo": saldo})
            
            # Resultado
            anios = meses / 12
            st.success(f"🎉 Alcanzarás tu meta de **${meta:,.0f}** en **{meses} meses** ({anios:.1f} años).")
            
            if data_proy:
                df_proy = pd.DataFrame(data_proy)
                st.line_chart(df_proy, x="Mes", y="Saldo")
        else:
            st.warning("Debes ahorrar algo mensualmente para proyectar.")
            
    with tab2:
        st.subheader("¿Cuándo podrás vivir de tus rentas?")
        st.write("Regla del 4%: Necesitas 25 veces tus gastos anuales.")
        
        gasto_mensual = st.number_input("Gasto Mensual Promedio", value=2000000.0, step=100000.0)
        
        numero_fire = gasto_mensual * 12 * 25
        st.metric("Tu Número de Libertad (FIRE)", f"${numero_fire:,.0f} COP")
        
        st.progress(min(ahorro_actual / numero_fire, 1.0) if numero_fire > 0 else 0)
        st.caption(f"Tienes cubierto el {(ahorro_actual / numero_fire * 100 if numero_fire > 0 else 0):.2f}% de tu libertad.")

# ============================================================
# ENRUTADOR PRINCIPAL (LÓGICA DE NAVEGACIÓN)
# ============================================================
# Mapeo unificado simplificado (7 Secciones + Admin)
mapeo_modulos = {
    "🏠 Inicio": render_inicio,
    "📒 Movimientos": render_movimientos,
    "📊 Presupuestos": render_presupuestos,
    "📅 Suscripciones": render_suscripciones,
    "🔮 Simulador": render_simulador,
    "💼 Mi Patrimonio": render_patrimonio,
    "🤖 Asistente IA": render_asistente_ia,
    "👮 Panel Admin": render_admin_panel # Solo visible si es admin
}

# Filtrar menú si no es admin (Seguridad extra, aunque sidebar ya lo oculta)
if st.session_state.get("rol") != "ADMIN" and modulo == "👮 Panel Admin":
    modulo = "🏠 Inicio"  # Redirigir a inicio si intenta acceder a admin

# Ejecutar el módulo seleccionado
if modulo in mapeo_modulos:
    mapeo_modulos[modulo]()
