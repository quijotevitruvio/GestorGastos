import json
import re
from colorama import Fore, Style

def clean_json_string(json_string):
    """
    Intenta limpiar la respuesta de Gemini para obtener un JSON válido.
    Elimina bloques de markdown ```json ... ``` si existen.
    """
    try:
        # Buscar patrón de bloque de código
        match = re.search(r"```json\s*(\{.*?\})\s*```", json_string, re.DOTALL)
        if match:
            return match.group(1)
        
        # Si no hay bloques, intentar buscar llaves
        match = re.search(r"(\{.*?\})", json_string, re.DOTALL)
        if match:
            return match.group(0)
            
        return json_string
    except Exception:
        return json_string

def print_result(concepto, monto, result):
    """
    Imprime el resultado en consola con colores.
    """
    score = result.get("score", 0)
    color_hex = result.get("color", "#ffffff")
    
    # Mapeo simple de hex a colorama (aproximado para consola)
    console_color = Fore.WHITE
    if score >= 5: console_color = Fore.GREEN
    elif score == 4: console_color = Fore.GREEN
    elif score == 3: console_color = Fore.YELLOW
    elif score == 2: console_color = Fore.YELLOW # Naranja suele ser similar a amarillo en ansi básico
    elif score <= 1: console_color = Fore.RED

    print(f"\n{Style.BRIGHT}Análisis para: {concepto} (${monto}){Style.RESET_ALL}")
    print(f"Puntuación: {console_color}{score}/5{Style.RESET_ALL}")
    print(f"Justificación: {result.get('justificacion')}")
    print(f"Sugerencia: {result.get('categoria_sugerida')}")
    print("-" * 40)
