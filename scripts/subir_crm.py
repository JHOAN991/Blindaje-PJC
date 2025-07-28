import gspread
import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe

# Configuración
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
CLIENT = gspread.authorize(CREDS)

# IDs y configuraciones
SHEET_ID = "1YTGCDwIuYNqZpt6qvdUSYSoK5vbPHShvf2b4qOnF-58"
HOJA_BASE = "Base_Madre"
HOJA_TOTAL = "TOTAL"

# Columnas requeridas para el CRM
COLUMNAS_CRM = [
    "Base", "BUNDLE", "PLAN INT", "OFRECER", "Factura Actual", "Nueva factura catalogo",
    "Ajuste Permanente CM", "Incremento + Impuesto", "SUSCRIPTOR", "Cuenta", "NOMBRE_CLIENTE",
    "CICLO", "Numero 1", "Numero 2", "Numero 3", "Numero 4", "Fijo 1", "Fijo 2", "Agente",
    "Fecha", "Hora", "Gestion", "Razon", "Comentario", "Incremento", "Mejor contacto",
    "CEDULA", "INCREMEN TOTAL", "plan_tel_actual", "factura_tel_actual", 
    "factura_total_vieja", "factura_total_nueva"
]

# Columnas que deben tener "Vacio" si están vacías
COLUMNAS_A_RELLENAR = ["OFRECER", "Numero 1", "Numero 4"]

def obtener_bases_no_subidas():
    """Obtiene las bases que no han sido marcadas como 'Si' en columna Subida"""
    try:
        sheet = CLIENT.open_by_key(SHEET_ID).worksheet(HOJA_BASE)
        df = get_as_dataframe(sheet).fillna("")
        return df[df["Subida"].str.upper() != "SI"]["Base"].unique().tolist()
    except Exception as e:
        print(f"Error al obtener bases no subidas: {e}")
        return []

def rellenar_campos_vacios(df):
    """Rellena campos vacíos en columnas específicas con 'Vacio'"""
    for columna in COLUMNAS_A_RELLENAR:
        if columna in df.columns:
            df[columna] = df[columna].apply(lambda x: "Vacio" if pd.isna(x) or str(x).strip() == "" else x)
    return df

def subir_base_crm(nombre_base):
    """
    Sube una base específica de Base_Madre a TOTAL sin modificaciones,
    manteniendo solo las columnas requeridas por el CRM
    """
    try:
        # 1. Obtener datos de Base_Madre
        spreadsheet = CLIENT.open_by_key(SHEET_ID)
        base_madre = spreadsheet.worksheet(HOJA_BASE)
        df_madre = get_as_dataframe(base_madre).fillna("")
        
        # 2. Filtrar base seleccionada
        df_seleccionada = df_madre[df_madre["Base"] == nombre_base]
        if df_seleccionada.empty:
            return False, f"Base '{nombre_base}' no encontrada en Base_Madre"
        
        # 3. Rellenar campos vacíos en columnas específicas
        df_seleccionada = rellenar_campos_vacios(df_seleccionada)
        
        # 4. Filtrar columnas (solo las que existen en ambos lugares)
        columnas_disponibles = [col for col in COLUMNAS_CRM if col in df_seleccionada.columns]
        df_seleccionada = df_seleccionada[columnas_disponibles]
        
        # 5. Marcar como subida en Base_Madre
        df_madre.loc[df_madre["Base"] == nombre_base, "Subida"] = "SI"
        set_with_dataframe(base_madre, df_madre)
        
        # 6. Agregar a TOTAL
        total = spreadsheet.worksheet(HOJA_TOTAL)
        df_total = get_as_dataframe(total).fillna("")
        
        # Concatenar manteniendo solo columnas comunes
        columnas_comunes = [col for col in COLUMNAS_CRM if col in df_total.columns]
        df_final = pd.concat([
            df_total[columnas_comunes], 
            df_seleccionada[columnas_comunes]
        ], ignore_index=True)
        
        set_with_dataframe(total, df_final)
        
        return True, f"Base '{nombre_base}' subida exitosamente a TOTAL"
    except Exception as e:
        return False, f"Error al subir base: {str(e)}"