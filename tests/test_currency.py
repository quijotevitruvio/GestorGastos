#!/usr/bin/env python3
"""
============================================================
Tests para el módulo de conversión de divisas
============================================================

Ejecutar: pytest tests/test_currency.py -v
"""

import sys
import os

# Agregar directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from currency import convertir, formatear_moneda, obtener_simbolo


class TestFormatearMoneda:
    """Tests para la función formatear_moneda."""
    
    def test_formato_cop(self):
        """COP debe mostrar sin decimales."""
        resultado = formatear_moneda(150000, "COP")
        assert "150,000" in resultado
        assert "COP" in resultado
        assert "$" in resultado
    
    def test_formato_usd(self):
        """USD debe mostrar con 2 decimales y símbolo US$."""
        resultado = formatear_moneda(150.50, "USD")
        assert "150.50" in resultado
        assert "USD" in resultado
        assert "US$" in resultado
    
    def test_formato_eur(self):
        """EUR debe mostrar con 2 decimales y símbolo €."""
        resultado = formatear_moneda(100.00, "EUR")
        assert "100.00" in resultado
        assert "EUR" in resultado
        assert "€" in resultado


class TestObtenerSimbolo:
    """Tests para la función obtener_simbolo."""
    
    def test_simbolo_cop(self):
        assert obtener_simbolo("COP") == "$"
    
    def test_simbolo_usd(self):
        assert obtener_simbolo("USD") == "US$"
    
    def test_simbolo_eur(self):
        assert obtener_simbolo("EUR") == "€"
    
    def test_simbolo_desconocido(self):
        """Divisa desconocida debe devolver $."""
        assert obtener_simbolo("XYZ") == "$"


class TestConvertir:
    """Tests para la función convertir."""
    
    def test_misma_divisa(self):
        """Convertir a la misma divisa no cambia el monto."""
        resultado = convertir(100, "USD", "USD")
        assert resultado == 100
    
    def test_conversion_usd_a_cop(self):
        """USD a COP debe multiplicar el monto."""
        # Usando tasas de prueba
        tasas = {"USD": 1.0, "COP": 4200.0, "EUR": 0.92}
        resultado = convertir(100, "USD", "COP", tasas)
        assert resultado == 420000.0
    
    def test_conversion_cop_a_usd(self):
        """COP a USD debe dividir el monto."""
        tasas = {"USD": 1.0, "COP": 4200.0, "EUR": 0.92}
        resultado = convertir(420000, "COP", "USD", tasas)
        assert resultado == pytest.approx(100.0, rel=0.01)
    
    def test_conversion_eur_a_cop(self):
        """EUR a COP debe pasar por USD."""
        tasas = {"USD": 1.0, "COP": 4200.0, "EUR": 0.92}
        resultado = convertir(100, "EUR", "COP", tasas)
        # 100 EUR / 0.92 = 108.7 USD * 4200 = ~456,521 COP
        assert resultado > 400000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
