import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe

# Configuración
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
CLIENT = gspread.authorize(CREDS)

# IDs de las hojas
BASE_MADRE_ID = "1YTGCDwIuYNqZpt6qvdUSYSoK5vbPHShvf2b4qOnF-58"
DESTINO_SHEET_ID = "1puCLMavPb7cDNEyBU33aJkaUK4O48AZUA7Mi5yp3fUg"

# Estructura CRM
COLUMNA_CRM = [
    "Base", "BUNDLE", "PLAN INT", "OFRECER", "Factura Actual", "Nueva factura catalogo",
    "Ajuste Permanente CM", "Incremento + Impuesto", "SUSCRIPTOR", "Cuenta", "NOMBRE_CLIENTE",
    "CICLO", "Numero 1", "Numero 2", "Numero 3", "Numero 4", "Fijo 1", "Fijo 2", "Agente",
    "Fecha", "Hora", "Gestion", "Razon", "Comentario", "Incremento", "Mejor contacto",
    "CEDULA", "INCREMEN TOTAL", "plan_tel_actual", "factura_tel_actual", "factura_total_vieja", "factura_total_nueva"
]

MAPEO_COLUMNAS = {
    "bundle": "BUNDLE",
    "plan_int_actual": "PLAN INT",
    "plan_int_nuevo": "OFRECER",
    "factura_int_actual": "Factura Actual",
    "factura_int_nuevo": "Nueva factura catalogo",
    "descuento_int_nuevo": "Ajuste Permanente CM",
    "plan_tv_actual": "Incremento + Impuesto",
    "suscriptor": "SUSCRIPTOR",
    "cuenta": "Cuenta",
    "factura_tv_actual": "NOMBRE_CLIENTE",
    "ciclo": "CICLO",
    "plan_tv_nuevo": "Numero 1",
    "descuento_tv_nuevo": "Numero 2",
    "factura_tv_nuevo": "Numero 3",
    "vix": "Numero 4",
    "hbo": "Fijo 1",
    "universal": "Fijo 2",
    "star": "Incremento",
    "combo": "Mejor contacto",
    "disney": "CEDULA",
    "paramount": "INCREMEN TOTAL",
    "plan_tel_actual": "plan_tel_actual",
    "factura_tel_actual": "factura_tel_actual",
    "factura_total_vieja": "factura_total_vieja",
    "factura_total_nueva": "factura_total_nueva"
}

def obtener_bases_existentes():
    """Obtiene las bases ya registradas en Base_Madre"""
    try:
        sheet = CLIENT.open_by_key(BASE_MADRE_ID).worksheet("Base_Madre")
        df = get_as_dataframe(sheet)
        return df['Base'].dropna().unique().tolist()
    except Exception as e:
        print(f"Error al obtener bases existentes: {e}")
        return []

def obtener_hojas_destino():
    """Obtiene los nombres de las hojas en el archivo de destino"""
    try:
        spreadsheet = CLIENT.open_by_key(DESTINO_SHEET_ID)
        return [ws.title for ws in spreadsheet.worksheets()]
    except Exception as e:
        print(f"Error al obtener hojas destino: {e}")
        return []

def obtener_bases_faltantes():
    """Compara las bases y devuelve las que faltan en Base_Madre"""
    bases_madre = obtener_bases_existentes()
    hojas_destino = obtener_hojas_destino()
    
    # Asumimos que el nombre de la hoja es igual al nombre de la base
    return list(set(hojas_destino) - set(bases_madre))

def transformar_a_crm(df, nombre_base):
    """Transforma un DataFrame a la estructura CRM"""
    try:
        # 1. Renombrar columnas según mapeo
        df = df.rename(columns={k: v for k, v in MAPEO_COLUMNAS.items() if k in df.columns})
        
        # 2. Asegurar todas las columnas requeridas
        df["Base"] = nombre_base
        for col in COLUMNA_CRM:
            if col not in df.columns:
                df[col] = ""
        
        # 3. Ordenar columnas
        return df[COLUMNA_CRM]
    except Exception as e:
        print(f"Error en transformación: {e}")
        return None

def cargar_base_a_madre(nombre_base):
    """Carga una base específica desde destino a Base_Madre"""
    try:
        # 1. Obtener datos de la hoja en destino
        spreadsheet = CLIENT.open_by_key(DESTINO_SHEET_ID)
        worksheet = spreadsheet.worksheet(nombre_base)
        df = get_as_dataframe(worksheet)
        
        # 2. Transformar a estructura CRM
        df_crm = transformar_a_crm(df, nombre_base)
        if df_crm is None:
            return False, "Error en transformación"
        
        # 3. Cargar a Base_Madre
        sheet_madre = CLIENT.open_by_key(BASE_MADRE_ID).worksheet("Base_Madre")
        
        # Obtener última fila con datos
        ultima_fila = len(sheet_madre.get_all_values()) + 1
        
        # Agregar datos
        set_with_dataframe(sheet_madre, df_crm, row=ultima_fila, include_column_header=False)
        
        return True, f"Base {nombre_base} cargada exitosamente"
    except Exception as e:
        return False, f"Error al cargar base: {str(e)}"