
import pandas as pd
from datetime import datetime
from utils import connect_sheets_utility

def add_expense(fecha, concepto, monto, divisa, categoria, medio_pago="Efectivo", lugar="N/A", recurrencia="Único", alerta="SÍ", score=0, justificacion="Manual"):
    """
    Registra un nuevo gasto en la hoja de cálculo.
    """
    try:
        sh = connect_sheets_utility(0) # 0 es la hoja de gastos principal
        sh.append_row([
            str(fecha), concepto, monto, divisa, categoria,
            lugar, medio_pago, "N/A", score, justificacion,
            recurrencia, alerta
        ])
        return {"success": True, "message": f"Gasto '{concepto}' registrado exitosamente."}
    except Exception as e:
        return {"success": False, "message": f"Error registrando gasto: {str(e)}"}

def add_income(fecha, concepto, monto, divisa, fuente, recurrencia="Único", comentario=""):
    """
    Registra un nuevo ingreso en la hoja de Ingresos.
    """
    try:
        sh = connect_sheets_utility("Ingresos")
        sh.append_row([
            str(fecha), concepto, monto, divisa, fuente, recurrencia, comentario
        ])
        return {"success": True, "message": f"Ingreso '{concepto}' registrado exitosamente."}
    except Exception as e:
        return {"success": False, "message": f"Error registrando ingreso: {str(e)}"}

def add_debt(tipo_operacion, persona, concepto, monto, divisa, fecha_limite, comentario="", alerta=True):
    """
    Registra una nueva deuda o préstamo.
    tipo_operacion: 'ME_DEBEN' o 'YO_DEBO'
    """
    try:
        # Normalizar tipo
        tipo_db = "ME_DEBEN" if "Me Deben" in tipo_operacion or tipo_operacion == "ME_DEBEN" else "YO_DEBO"
        id_unico = f"{tipo_db[:2]}_{int(pd.Timestamp.now().timestamp())}"
        
        sh = connect_sheets_utility("Deudas")
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
        return {"success": True, "message": "Registro de deuda exitoso."}
    except Exception as e:
        return {"success": False, "message": f"Error registrando deuda: {str(e)}"}

def add_account(nombre, tipo, saldo, divisa="COP"):
    """
    Registra una nueva cuenta.
    """
    try:
        sh = connect_sheets_utility("Cuentas")
        id_cuenta = f"CTA_{int(pd.Timestamp.now().timestamp())}"
        sh.append_row([id_cuenta, nombre, tipo, saldo, divisa, "", "", "SÍ"])
        return {"success": True, "message": f"Cuenta '{nombre}' creada exitosamente."}
    except Exception as e:
        return {"success": False, "message": f"Error creando cuenta: {str(e)}"}

def get_budgets():
    """Obtiene los presupuestos configurados."""
    try:
        sh = connect_sheets_utility("Presupuestos")
        return sh.get_all_records()
    except Exception:
        return []

def set_budget(categoria, monto, periodo="Mensual"):
    """Crea o actualiza un presupuesto para una categoría."""
    try:
        sh = connect_sheets_utility("Presupuestos")
        data = sh.get_all_records()
        df = pd.DataFrame(data)
        
        # Si ya existe, actualizar
        cell = None
        if not df.empty and 'Categoria' in df.columns:
             try:
                cell = sh.find(categoria)
             except gspread.exceptions.CellNotFound:
                pass
        
        if cell:
            sh.update_cell(cell.row, 2, monto) # Col 2 = Monto
            sh.update_cell(cell.row, 3, periodo)
            return {"success": True, "message": f"Presupuesto de {categoria} actualizado."}
        else:
            sh.append_row([categoria, monto, periodo])
            return {"success": True, "message": f"Presupuesto de {categoria} creado."}
            
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

def get_budget_status():
    """Calcula el progreso de gastos vs presupuestos para el mes actual."""
    try:
        # 1. Obtener Presupuestos
        budgets = get_budgets()
        if not budgets: return []
        
        # 2. Obtener Gastos del Mes
        sh_gastos = connect_sheets_utility(0)
        all_gastos = sh_gastos.get_all_records()
        df_gastos = pd.DataFrame(all_gastos)
        
        hoy = datetime.now()
        mes_actual = hoy.month
        anio_actual = hoy.year
        
        # Filtrar gastos mes actual
        if not df_gastos.empty and 'Fecha' in df_gastos.columns:
             df_gastos['Fecha'] = pd.to_datetime(df_gastos['Fecha'], errors='coerce')
             df_gastos = df_gastos[
                 (df_gastos['Fecha'].dt.month == mes_actual) & 
                 (df_gastos['Fecha'].dt.year == anio_actual)
             ]
        
        status = []
        for b in budgets:
            cat = b['Categoria']
            limite = float(b['Monto_Limite'])
            
            # Sumar gastos de esa categoría
            gastado = 0
            if not df_gastos.empty:
                gastado = df_gastos[df_gastos['Categoria'] == cat]['Monto'].sum()
            
            porcentaje = (gastado / limite) * 100 if limite > 0 else 100
            
            status.append({
                "categoria": cat,
                "limite": limite,
                "gastado": gastado,
                "porcentaje": porcentaje,
                "restante": limite - gastado
            })
            
        return status
    except Exception as e:
        print(f"Error calculating budget status: {e}")
        return []

def get_subscriptions():
    """Obtiene todas las suscripciones."""
    try:
        sh = connect_sheets_utility("Suscripciones")
        return sh.get_all_records()
    except Exception:
        return []

def add_subscription(servicio, monto, divisa, periodo, fecha_cobro, estado="Activo"):
    """Registra una nueva suscripción."""
    try:
        sh = connect_sheets_utility("Suscripciones")
        sh.append_row([servicio, monto, divisa, periodo, fecha_cobro, estado])
        return {"success": True, "message": f"Suscripción a {servicio} añadida."}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

def delete_subscription(row_index):
    """Elimina una suscripción por índice de fila (1-based en gspread, pero cuidado con header)."""
    try:
        sh = connect_sheets_utility("Suscripciones")
        sh.delete_rows(row_index)
        return {"success": True, "message": "Suscripción eliminada."}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

def get_monthly_fixed_cost():
    """Calcula el costo mensual aproximado de suscripciones activas."""
    try:
        subs = get_subscriptions()
        total_cop = 0
        for s in subs:
            if s.get('Estado') == 'Activo':
                monto = float(str(s['Monto']).replace(',', '').replace('$', ''))
                # Conversión simple (hardcoded por ahora, idealmente usar una API o valor almacenado)
                if s['Divisa'] == 'USD': monto *= 4000
                elif s['Divisa'] == 'EUR': monto *= 4300
                
                if s['Periodo'] == 'Anual': monto /= 12
                
                total_cop += monto
        return total_cop
    except Exception:
        return 0
