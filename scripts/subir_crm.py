# scripts/subir_crm.py
import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Cargar las credenciales desde streamlit secrets
service_account_info = dict(st.secrets["gcp_service_account"])
CREDS = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)

# Autorizar cliente gspread
client = gspread.authorize(CREDS)
# === ID del archivo de Google Sheets donde se registran los logs ===
SHEET_ID = "1YTGCDwIuYNqZpt6qvdUSYSoK5vbPHShvf2b4qOnF-58" # <- reemplaza con el ID real del proyecto
HOJA_BASE = "Base_Madre"
HOJA_TOTAL = "TOTAL"

def obtener_bases_disponibles():
    hoja = client.open_by_key(SHEET_ID).worksheet(HOJA_BASE)
    df = get_as_dataframe(hoja, dtype=str).fillna("")
    bases_disponibles = df[df["Subida"].str.lower() != "si"]["Base"].unique().tolist()
    return bases_disponibles

def subir_base_a_total(nombre_base):
    columnas_deseadas = [
        "Base", "BUNDLE", "PLAN INT", "OFRECER", "Factura Actual", "Nueva factura catalogo",
        "Ajuste Permanente CM", "Incremento + Impuesto", "SUSCRIPTOR", "Cuenta", "NOMBRE_CLIENTE",
        "CICLO", "Numero 1", "Numero 2", "Numero 3", "Numero 4", "Fijo 1", "Fijo 2", "Agente",
        "Fecha", "Hora", "Gestion", "Razon", "Comentario", "Incremento", "Mejor contacto",
        "CEDULA", "INCREMEN TOTAL", "plan_tel_actual", "factura_tel_actual", 
        "factura_total_vieja", "factura_total_nueva"
    ]

    sh = client.open_by_key(SHEET_ID)
    base_madre = sh.worksheet(HOJA_BASE)
    total = sh.worksheet(HOJA_TOTAL)

    df_madre = get_as_dataframe(base_madre, dtype=str).fillna("")

    # Filtrar la base seleccionada
    df_seleccionada = df_madre[df_madre["Base"] == nombre_base].copy()
    if df_seleccionada.empty:
        return f"No se encontraron registros con Base = {nombre_base}"

    # Filtrar columnas
    df_seleccionada = df_seleccionada[[col for col in columnas_deseadas if col in df_seleccionada.columns]]

    # Marcar como subida
    df_madre.loc[df_madre["Base"] == nombre_base, "Subida"] = "Si"
    set_with_dataframe(base_madre, df_madre)

    # Agregar a TOTAL
    df_total = get_as_dataframe(total, dtype=str).fillna("")
    df_final = pd.concat([df_total, df_seleccionada], ignore_index=True)
    set_with_dataframe(total, df_final)

    return f"✅ Base '{nombre_base}' subida correctamente a TOTAL."
