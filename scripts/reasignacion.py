import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe
import streamlit as st

# === CONFIGURACIÓN ===
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
LOG_SHEET_ID = "1YTGCDwIuYNqZpt6qvdUSYSoK5vbPHShvf2b4qOnF-58"
LOG_HOJA = "TOTAL"

# Cliente global
client = None

def iniciar_credenciales():
    global client
    if client is None:  # Solo si no está iniciado
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=SCOPES
        )
        client = gspread.authorize(creds)

def cargar_total():
    """Carga la hoja TOTAL como dataframe y retorna también el worksheet."""
    ws = client.open_by_key(LOG_SHEET_ID).worksheet(LOG_HOJA)
    df = get_as_dataframe(ws).fillna("")
    return df, ws

def filtrar_clientes(df, base, ciclo, agente):
    """Filtra registros sin gestión según los parámetros indicados."""
    return df[
        (df["Base"] == base) &
        (df["CICLO"] == ciclo) &
        (df["Agente"] == agente) &
        (df["Gestion"] == "")
    ].copy()

def actualizar_agente(df_original, ws, df_reasignar, nuevo_agente):
    """Reasigna el agente de las cuentas seleccionadas."""
    df_original.set_index("Cuenta", inplace=True)
    df_reasignar.set_index("Cuenta", inplace=True)

    for cuenta in df_reasignar.index:
        if cuenta in df_original.index:
            df_original.at[cuenta, "Agente"] = nuevo_agente

    df_original.reset_index(inplace=True)
    ws.clear()
    set_with_dataframe(ws, df_original, include_index=False)

def contar_total_gestiones():
    """
    Devuelve el número de filas en la hoja TOTAL
    cuyo campo 'Gestion' no está vacío.
    """
    df, _ = cargar_total()
    if "Gestion" in df.columns:
        return int((df["Gestion"].astype(str).str.strip() != "").sum())
    return 0
