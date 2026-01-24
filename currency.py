"""
============================================================
Ge$torGasto$ - Módulo de Conversión de Divisas
============================================================

Este módulo maneja la conversión entre divisas (COP, USD, EUR)
usando una API gratuita de tasas de cambio.

API utilizada: https://api.exchangerate-api.com (gratuita, sin key)
"""

import requests
import streamlit as st
from datetime import datetime, timedelta

# ============================================================
# CONSTANTES
# ============================================================

# URL de la API gratuita de tasas de cambio
API_URL = "https://api.exchangerate-api.com/v4/latest/USD"

# Tasas de respaldo en caso de que la API falle
# (Actualizadas manualmente como fallback)
TASAS_RESPALDO = {
    "USD": 1.0,
    "COP": 4200.0,  # Aproximado COP por USD
    "EUR": 0.92     # Aproximado EUR por USD
}

# ============================================================
# FUNCIONES
# ============================================================

@st.cache_data(ttl=3600)  # Cache de 1 hora para no sobrecargar API
def obtener_tasas():
    """
    Obtiene las tasas de cambio actuales desde la API.
    
    Las tasas están basadas en USD (1 USD = X de otra divisa).
    
    Returns:
        dict: Diccionario con tasas {"USD": 1.0, "COP": 4200, "EUR": 0.92, ...}
        
    Ejemplo:
        tasas = obtener_tasas()
        # tasas["COP"] = 4150.25 (cuántos COP por 1 USD)
    """
    try:
        respuesta = requests.get(API_URL, timeout=5)
        respuesta.raise_for_status()
        datos = respuesta.json()
        
        # La API devuelve: {"base": "USD", "rates": {"COP": 4150, ...}}
        tasas = datos.get("rates", {})
        tasas["USD"] = 1.0  # Asegurar que USD esté presente
        
        return tasas
        
    except Exception as e:
        # Si falla la API, usar tasas de respaldo
        print(f"⚠️ Error obteniendo tasas: {e}. Usando tasas de respaldo.")
        return TASAS_RESPALDO


def convertir(monto, de_divisa, a_divisa, tasas=None):
    """
    Convierte un monto de una divisa a otra.
    
    Args:
        monto: Cantidad a convertir
        de_divisa: Código de divisa origen ("COP", "USD", "EUR")
        a_divisa: Código de divisa destino
        tasas: Diccionario de tasas (opcional, si no se pasa se obtienen)
        
    Returns:
        float: Monto convertido
        
    Ejemplo:
        # Convertir 100 USD a COP
        cop = convertir(100, "USD", "COP")  # ~420,000 COP
        
        # Convertir 1,000,000 COP a USD
        usd = convertir(1000000, "COP", "USD")  # ~238 USD
    """
    if de_divisa == a_divisa:
        return monto
    
    if tasas is None:
        tasas = obtener_tasas()
    
    # Obtener tasas (basadas en USD)
    tasa_origen = tasas.get(de_divisa, 1.0)
    tasa_destino = tasas.get(a_divisa, 1.0)
    
    # Convertir: primero a USD, luego a divisa destino
    # monto_usd = monto / tasa_origen
    # monto_final = monto_usd * tasa_destino
    monto_convertido = (monto / tasa_origen) * tasa_destino
    
    return monto_convertido


def convertir_columna(df, columna_monto, columna_divisa, divisa_destino):
    """
    Convierte todos los montos de un DataFrame a una divisa específica.
    
    Args:
        df: DataFrame de pandas
        columna_monto: Nombre de la columna con montos
        columna_divisa: Nombre de la columna con códigos de divisa
        divisa_destino: Código de divisa a la que convertir todo
        
    Returns:
        Series: Columna con montos convertidos
        
    Ejemplo:
        df['MontoConvertido'] = convertir_columna(df, 'MontoNum', 'Divisa', 'COP')
    """
    tasas = obtener_tasas()
    
    def convertir_fila(row):
        monto = row[columna_monto]
        divisa_origen = row.get(columna_divisa, divisa_destino)
        return convertir(monto, divisa_origen, divisa_destino, tasas)
    
    return df.apply(convertir_fila, axis=1)


def obtener_simbolo(divisa):
    """
    Devuelve el símbolo de una divisa.
    
    Args:
        divisa: Código de divisa ("COP", "USD", "EUR")
        
    Returns:
        str: Símbolo de la divisa
    """
    simbolos = {
        "COP": "$",
        "USD": "US$",
        "EUR": "€"
    }
    return simbolos.get(divisa, "$")


def formatear_moneda(valor, divisa="COP"):
    """
    Formatea un valor numérico como moneda.
    
    Args:
        valor: Número a formatear
        divisa: Código de divisa
        
    Returns:
        str: Valor formateado (ej: "$ 150,000 COP")
    """
    simbolo = obtener_simbolo(divisa)
    
    if divisa == "COP":
        return f"{simbolo} {valor:,.0f} COP"
    else:
        return f"{simbolo} {valor:,.2f} {divisa}"
