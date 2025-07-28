import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials
from gspread_dataframe import set_with_dataframe, get_as_dataframe
from datetime import datetime

# Configuración de conexión
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
CLIENT = gspread.authorize(CREDS)

# IDs de las hojas
DESTINO_SHEET_ID = "1puCLMavPb7cDNEyBU33aJkaUK4O48AZUA7Mi5yp3fUg"
LOG_SHEET_ID = "1YTGCDwIuYNqZpt6qvdUSYSoK5vbPHShvf2b4qOnF-58"

def cargar_archivo_a_gsheet(archivo):
    """Carga un archivo a Google Sheets como nueva hoja"""
    try:
        # Obtener nombre sin extensión
        nombre_hoja = archivo.name.split('.')[0]
        
        # Leer archivo
        df = pd.read_csv(archivo) if archivo.name.endswith('.csv') else pd.read_excel(archivo)
        
        # Validar datos básicos
        if df.empty:
            return False, "El archivo está vacío"
            
        # Conectar con Google Sheets
        spreadsheet = CLIENT.open_by_key(DESTINO_SHEET_ID)
        
        # Eliminar hoja si existe
        try:
            worksheet = spreadsheet.worksheet(nombre_hoja)
            spreadsheet.del_worksheet(worksheet)
            st.info(f"Hoja existente '{nombre_hoja}' fue reemplazada")
        except gspread.WorksheetNotFound:
            pass
        
        # Crear nueva hoja y cargar datos
        worksheet = spreadsheet.add_worksheet(
            title=nombre_hoja,
            rows=df.shape[0] + 1,
            cols=df.shape[1]
        )
        set_with_dataframe(worksheet, df)
        
        # Registrar en log
        registrar_log(archivo.name, df.shape[0])
        
        return True, f"✅ Archivo cargado en hoja '{nombre_hoja}'"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

def cargar_google_sheet(sheet_id):
    """Carga datos desde una hoja Google Sheets existente"""
    try:
        # Obtener nombre de la hoja fuente
        spreadsheet = CLIENT.open_by_key(sheet_id)
        nombre_hoja = spreadsheet.sheet1.title
        
        # Leer datos
        worksheet = spreadsheet.sheet1
        df = get_as_dataframe(worksheet)
        
        if df.empty:
            return False, "La hoja de Google está vacía"
            
        # Cargar a destino
        destino = CLIENT.open_by_key(DESTINO_SHEET_ID)
        
        # Eliminar hoja si existe
        try:
            ws = destino.worksheet(nombre_hoja)
            destino.del_worksheet(ws)
        except gspread.WorksheetNotFound:
            pass
            
        # Crear nueva hoja
        new_ws = destino.add_worksheet(
            title=nombre_hoja,
            rows=df.shape[0] + 1,
            cols=df.shape[1]
        )
        set_with_dataframe(new_ws, df)
        
        # Registrar en log
        registrar_log(f"Google Sheet: {sheet_id}", df.shape[0])
        
        return True, f"✅ Datos de {nombre_hoja} cargados correctamente"
    except Exception as e:
        return False, f"❌ Error al cargar Google Sheet: {str(e)}"

def registrar_log(nombre_archivo, registros):
    """Registra la operación en la hoja de logs"""
    try:
        log_sheet = CLIENT.open_by_key(LOG_SHEET_ID).worksheet("Logs")
        log_sheet.append_row([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            nombre_archivo,
            str(registros),
            "Alimentar.py"
        ])
    except Exception as e:
        st.error(f"No se pudo registrar el log: {str(e)}")

def procesar_entradas(sheets_ids=None, archivos_locales=None):
    """Procesa múltiples entradas (archivos locales y Google Sheets)"""
    resultados = []
    
    # Procesar Google Sheets IDs
    if sheets_ids:
        for sheet_id in sheets_ids:
            success, mensaje = cargar_google_sheet(sheet_id)
            resultados.append((f"Google Sheet: {sheet_id}", mensaje))
    
    # Procesar archivos locales
    if archivos_locales:
        for archivo in archivos_locales:
            success, mensaje = cargar_archivo_a_gsheet(archivo)
            resultados.append((archivo.name, mensaje))
    
    return resultados

def cargar_archivos_locales(archivos, preview=False):
    """Carga archivos locales para previsualización o procesamiento completo"""
    previews = []
    
    for archivo in archivos:
        try:
            nombre = archivo.name
            df = pd.read_csv(archivo) if nombre.endswith('.csv') else pd.read_excel(archivo)
            previews.append((nombre, df.head(5)))  # Mostrar solo 5 filas para preview
            
            if not preview:
                # Lógica de procesamiento completo
                cargar_archivo_a_gsheet(archivo)
        except Exception as e:
            previews.append((nombre, f"Error al cargar: {str(e)}"))
    
    return previews