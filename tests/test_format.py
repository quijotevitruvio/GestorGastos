#!/usr/bin/env python3
"""
============================================================
Tests para funciones de formato y utilidades
============================================================

Ejecutar: pytest tests/test_format.py -v
"""

import sys
import os

# Agregar directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from utils import clean_json_string


class TestCleanJsonString:
    """Tests para la función clean_json_string."""
    
    def test_json_limpio(self):
        """JSON sin markdown debe devolverse igual."""
        json_str = '{"score": 5, "justificacion": "Necesario"}'
        resultado = clean_json_string(json_str)
        assert resultado == json_str
    
    def test_json_con_markdown(self):
        """JSON dentro de bloque markdown debe extraerse."""
        json_str = '```json\n{"score": 5}\n```'
        resultado = clean_json_string(json_str)
        assert '{"score": 5}' in resultado
        assert '```' not in resultado
    
    def test_json_con_texto_extra(self):
        """JSON con texto extra debe extraer solo el JSON."""
        json_str = 'Aquí está el resultado: {"score": 3}'
        resultado = clean_json_string(json_str)
        assert '{"score": 3}' in resultado


class TestCategorizacion:
    """Tests para la lógica de categorización de gastos."""
    
    def test_gasto_vital(self):
        """Score >= 4 es Vital/Necesario."""
        def categorizar(score):
            if score >= 4: return "Vital/Necesario"
            if score == 3: return "Opcional"
            return "Innecesario"
        
        assert categorizar(5) == "Vital/Necesario"
        assert categorizar(4) == "Vital/Necesario"
    
    def test_gasto_opcional(self):
        """Score == 3 es Opcional."""
        def categorizar(score):
            if score >= 4: return "Vital/Necesario"
            if score == 3: return "Opcional"
            return "Innecesario"
        
        assert categorizar(3) == "Opcional"
    
    def test_gasto_innecesario(self):
        """Score <= 2 es Innecesario (Hormiga)."""
        def categorizar(score):
            if score >= 4: return "Vital/Necesario"
            if score == 3: return "Opcional"
            return "Innecesario"
        
        assert categorizar(2) == "Innecesario"
        assert categorizar(1) == "Innecesario"
        assert categorizar(0) == "Innecesario"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
