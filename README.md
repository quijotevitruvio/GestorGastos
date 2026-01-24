# Auditor Financiero Personal con IA

Este proyecto integra Google Sheets con la IA de Gemini para auditar tus gastos personales automáticamente.

## Requisitos Previos

1.  **Python 3.8+** instalado.
2.  Una cuenta de **Google Cloud Platform (GCP)** activa.
3.  Una **API Key de Google Gemini**.

## Configuración Paso a Paso

### 1. Google Cloud y Credenciales

1.  Ve a [Google Cloud Console](https://console.cloud.google.com/).
2.  Crea un nuevo proyecto.
3.  Habilita las siguientes APIs:
    *   **Google Sheets API**
    *   **Google Drive API**
4.  Ve a "Credenciales" > "Crear Credenciales" > "Cuenta de servicio".
5.  Dale un nombre y crea la cuenta.
6.  Entra a la cuenta de servicio creada, ve a la pestaña "Claves" (Keys) y crea una nueva clave **JSON**.
7.  Descarga el archivo y renómbralo a `credentials.json` en esta carpeta.
8.  **IMPORTANTE**: Copia el "correo electrónico" de la cuenta de servicio (ej: `tu-bot@tu-proyecto.iam.gserviceaccount.com`) y **compártele tu Google Sheet** con permisos de **Editor**.

### 2. Configuración del Entorno

1.  Copia el archivo de ejemplo:
    ```bash
    cp .env.example .env
    ```
2.  Edita `.env` y agrega:
    *   `GEMINI_API_KEY`: Consíguela en [Google AI Studio](https://aistudio.google.com/).
    *   `GOOGLE_SHEET_NAME`: El nombre exacto de tu hoja de cálculo en Drive.

### 3. Preparar Google Sheet

### 3. Preparar Google Sheet

Asegúrate de que tu Hoja 1 tenga la siguiente estructura de columnas (orden lógico):

| Fecha | Concepto | Monto | Categoria | Lugar | MedioPago | Banco | Score | Justificacion | CategoriaSugerida | Color |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2024-01-20 | Starbucks | 15000 | Comida | Mall Plaza | T. Crédito | Nu | | | | |

*El sistema analizará estas columnas para darte el mejor feedback financiero.*

### 4. Instalación de Dependencias

```bash
pip install -r requirements.txt
```

### 5. Ejecución

```bash
python auditor.py
```

El script leerá las filas que no tengan "Score", las enviará a Gemini, y rellenará las columnas faltantes automáticamente.
