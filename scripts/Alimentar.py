import gspread
import pandas as pd
import os
from datetime import datetime
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe
import streamlit as st

# === CONFIGURACIÓN ===
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
service_account_info = dict(st.secrets["gcp_service_account"])
CREDS = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
client = gspread.authorize(CREDS)

# === ID de los archivos de Google Sheets ===
LOG_SHEET_ID = "1YTGCDwIuYNqZpt6qvdUSYSoK5vbPHShvf2b4qOnF-58"
LOG_HOJA = "logs"

DESTINO_SHEET_ID = "1puCLMavPb7cDNEyBU33aJkaUK4O48AZUA7Mi5yp3fUg"

# === DIRECTORIO DE SALIDA TEMPORAL ===
os.makedirs("BASES", exist_ok=True)

# === ESTRUCTURA DE COLUMNAS DEL CRM FINAL ===
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

def log_en_google_sheets(nombre_archivo, cantidad, origen):
    try:
        sheet = client.open_by_key(LOG_SHEET_ID).worksheet(LOG_HOJA)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        nueva_fila = [[now, nombre_archivo, cantidad, origen]]
        sheet.append_rows(nueva_fila, value_input_option="USER_ENTERED")
    except Exception as e:
        print(f"Error al registrar log en Google Sheets: {e}")

def transformar_a_estructura_crm(df, nombre_archivo):
    nombre_base = os.path.splitext(nombre_archivo)[0]
    columnas_renombradas = {col: MAPEO_COLUMNAS[col] for col in df.columns if col in MAPEO_COLUMNAS}
    df = df.rename(columns=columnas_renombradas)
    df_final = pd.DataFrame(columns=COLUMNA_CRM)

    for col in df.columns:
        if col in df_final.columns:
            df_final[col] = df[col]

    for col in COLUMNA_CRM:
        if col not in df_final.columns:
            df_final[col] = ""

    df_final["Base"] = nombre_base
    return df_final[COLUMNA_CRM]

def guardar_en_google_sheet(nombre_archivo_sin_ext, df):
    try:
        spreadsheet = client.open_by_key(DESTINO_SHEET_ID)
        try:
            spreadsheet.del_worksheet(spreadsheet.worksheet(nombre_archivo_sin_ext))
        except:
            pass  # Si no existe, ignoramos

        hoja = spreadsheet.add_worksheet(title=nombre_archivo_sin_ext, rows=str(len(df)+1), cols=str(len(df.columns)))
        set_with_dataframe(hoja, df.fillna(""), include_index=False)
    except Exception as e:
        print(f"Error al guardar en hoja '{nombre_archivo_sin_ext}': {e}")

def cargar_archivos_locales(uploaded_files, preview=False):
    resultados = []
    for archivo in uploaded_files:
        try:
            nombre = archivo.name
            nombre_sin_ext = os.path.splitext(nombre)[0]
            ext = os.path.splitext(nombre)[1].lower()

            if ext == ".csv":
                df = pd.read_csv(archivo, dtype=str).fillna("")
            elif ext in [".xls", ".xlsx"]:
                df = pd.read_excel(archivo, dtype=str).fillna("")
            else:
                resultados.append((nombre, f"error: formato no soportado ({ext})"))
                continue

            if preview:
                resultados.append((nombre, df.head(15)))
            else:
                # Guardar base VIRGEN en Google Sheets
                guardar_en_google_sheet(nombre_sin_ext, df)

                # Transformar para CRM y guardar CSV local
                df_transformado = transformar_a_estructura_crm(df, nombre)
                output_path = f"BASES/{nombre_sin_ext}.csv"
                df_transformado.to_csv(output_path, index=False)

                log_en_google_sheets(nombre, len(df_transformado), "Local")
                resultados.append((output_path, "success"))

        except Exception as e:
            resultados.append((archivo.name, f"error: {e}"))

    return resultados

def procesar_entradas(sheets_ids=[], archivos_locales=[]):
    resultados_locales = cargar_archivos_locales(archivos_locales) if archivos_locales else []
    return resultados_locales

from scripts.CARGAR_MADRE import ejecutar_carga
