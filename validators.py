#!/usr/bin/env python3
"""
============================================================
Ge$torGasto$ - Módulo de Validación de Datos
============================================================

Funciones para validar y sanitizar entradas de usuario antes
de enviarlas a Google Sheets.
"""

import re
from datetime import datetime, date
from typing import Tuple, Optional


def sanitizar_texto(texto: str, max_length: int = 200) -> str:
    """
    Limpia y sanitiza texto de entrada.
    
    Args:
        texto: Texto a sanitizar
        max_length: Longitud máxima permitida
        
    Returns:
        Texto limpio y truncado si es necesario
    """
    if not texto:
        return ""
    
    # Eliminar espacios extra
    texto = texto.strip()
    texto = re.sub(r'\s+', ' ', texto)
    
    # Eliminar caracteres potencialmente peligrosos para hojas de cálculo
    # (fórmulas que comienzan con =, +, -, @)
    if texto and texto[0] in '=+-@':
        texto = "'" + texto  # Prefijo con apóstrofe para escapar
    
    # Truncar si es muy largo
    if len(texto) > max_length:
        texto = texto[:max_length-3] + "..."
    
    return texto


def validar_monto(monto: float, divisa: str = "COP") -> Tuple[bool, str]:
    """
    Valida que el monto sea razonable según la divisa.
    
    Args:
        monto: Cantidad a validar
        divisa: Código de divisa (COP, USD, EUR)
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    if monto is None:
        return False, "El monto es requerido"
    
    if monto <= 0:
        return False, "El monto debe ser mayor a cero"
    
    # Límites por divisa
    limites = {
        "COP": {"min": 100, "max": 500_000_000},      # 100 COP a 500M COP
        "USD": {"min": 0.01, "max": 10_000_000},       # 0.01 USD a 10M USD
        "EUR": {"min": 0.01, "max": 10_000_000},       # 0.01 EUR a 10M EUR
    }
    
    limite = limites.get(divisa, limites["USD"])
    
    if monto < limite["min"]:
        return False, f"El monto mínimo para {divisa} es {limite['min']:,.2f}"
    
    if monto > limite["max"]:
        return False, f"El monto parece muy alto. ¿Seguro que es {monto:,.2f} {divisa}?"
    
    return True, ""


def validar_fecha(fecha, tipo: str = "gasto") -> Tuple[bool, str]:
    """
    Valida que la fecha sea coherente según el tipo de registro.
    
    Args:
        fecha: Fecha a validar (date o datetime)
        tipo: Tipo de registro ("gasto", "ingreso", "deuda")
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    if fecha is None:
        return False, "La fecha es requerida"
    
    # Convertir a date si es datetime
    if isinstance(fecha, datetime):
        fecha = fecha.date()
    elif not isinstance(fecha, date):
        try:
            fecha = datetime.strptime(str(fecha), "%Y-%m-%d").date()
        except:
            return False, "Formato de fecha inválido"
    
    hoy = date.today()
    
    # Para gastos e ingresos: no más de 1 año en el pasado, no en el futuro
    if tipo in ["gasto", "ingreso"]:
        if fecha > hoy:
            return False, "La fecha no puede ser futura para gastos/ingresos"
        
        from dateutil.relativedelta import relativedelta
        hace_un_año = hoy - relativedelta(years=1)
        if fecha < hace_un_año:
            return False, "La fecha es muy antigua (más de 1 año)"
    
    # Para deudas: la fecha límite puede ser futura
    elif tipo == "deuda":
        from dateutil.relativedelta import relativedelta
        hace_5_años = hoy - relativedelta(years=5)
        en_10_años = hoy + relativedelta(years=10)
        
        if fecha < hace_5_años:
            return False, "La fecha es muy antigua para una deuda"
        if fecha > en_10_años:
            return False, "La fecha límite es muy lejana"
    
    return True, ""


def validar_concepto(concepto: str, min_length: int = 3) -> Tuple[bool, str]:
    """
    Valida que el concepto sea descriptivo.
    
    Args:
        concepto: Texto del concepto
        min_length: Longitud mínima requerida
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    if not concepto:
        return False, "El concepto es requerido"
    
    concepto = concepto.strip()
    
    if len(concepto) < min_length:
        return False, f"El concepto debe tener al menos {min_length} caracteres"
    
    # Verificar que no sea solo números o caracteres especiales
    if re.match(r'^[\d\s\W]+$', concepto):
        return False, "El concepto debe incluir texto descriptivo"
    
    return True, ""


def validar_persona(persona: str) -> Tuple[bool, str]:
    """
    Valida el nombre de una persona/entidad para deudas.
    
    Args:
        persona: Nombre a validar
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    if not persona:
        return False, "El nombre de la persona/entidad es requerido"
    
    persona = persona.strip()
    
    if len(persona) < 2:
        return False, "El nombre es muy corto"
    
    if len(persona) > 100:
        return False, "El nombre es muy largo"
    
    return True, ""


def validar_formulario_gasto(fecha, concepto: str, monto: float, divisa: str, categoria: str) -> Tuple[bool, list]:
    """
    Valida todos los campos de un formulario de gasto.
    
    Returns:
        Tupla (todo_válido, lista_errores)
    """
    errores = []
    
    # Validar fecha
    valido, error = validar_fecha(fecha, "gasto")
    if not valido:
        errores.append(f"📅 Fecha: {error}")
    
    # Validar concepto
    valido, error = validar_concepto(concepto)
    if not valido:
        errores.append(f"📝 Concepto: {error}")
    
    # Validar monto
    valido, error = validar_monto(monto, divisa)
    if not valido:
        errores.append(f"💰 Monto: {error}")
    
    # Validar categoría
    categorias_validas = ["Comida", "Transporte", "Ocio", "Servicios", "Salud", "Ropa", "Educación", "Ahorro", "Otro"]
    if categoria not in categorias_validas:
        errores.append(f"📁 Categoría: '{categoria}' no es válida")
    
    return len(errores) == 0, errores


def validar_formulario_ingreso(fecha, concepto: str, monto: float, divisa: str, fuente: str) -> Tuple[bool, list]:
    """
    Valida todos los campos de un formulario de ingreso.
    
    Returns:
        Tupla (todo_válido, lista_errores)
    """
    errores = []
    
    valido, error = validar_fecha(fecha, "ingreso")
    if not valido:
        errores.append(f"📅 Fecha: {error}")
    
    valido, error = validar_concepto(concepto, min_length=2)
    if not valido:
        errores.append(f"📝 Concepto: {error}")
    
    valido, error = validar_monto(monto, divisa)
    if not valido:
        errores.append(f"💰 Monto: {error}")
    
    fuentes_validas = ["Nómina", "Negocio", "Inversión", "Regalo", "Otros"]
    if fuente not in fuentes_validas:
        errores.append(f"📁 Fuente: '{fuente}' no es válida")
    
    return len(errores) == 0, errores


def validar_formulario_deuda(persona: str, concepto: str, monto: float, divisa: str, fecha_limite) -> Tuple[bool, list]:
    """
    Valida todos los campos de un formulario de deuda.
    
    Returns:
        Tupla (todo_válido, lista_errores)
    """
    errores = []
    
    valido, error = validar_persona(persona)
    if not valido:
        errores.append(f"👤 Persona: {error}")
    
    valido, error = validar_concepto(concepto, min_length=2)
    if not valido:
        errores.append(f"📝 Concepto: {error}")
    
    valido, error = validar_monto(monto, divisa)
    if not valido:
        errores.append(f"💰 Monto: {error}")
    
    valido, error = validar_fecha(fecha_limite, "deuda")
    if not valido:
        errores.append(f"📅 Fecha límite: {error}")
    
    return len(errores) == 0, errores
