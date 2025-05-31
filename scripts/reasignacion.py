import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe
import streamlit as st

# === CONFIGURACIÓN ===
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
LOG_SHEET_ID = "1YTGCDwIuYNqZpt6qvdUSYSoK5vbPHShvf2b4qOnF-58"
LOG_HOJA = "TOTAL"

# Cliente global
client = None

def iniciar_credenciales():
    global client
    if client is None:
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=SCOPES
        )
        client = gspread.authorize(creds)

def cargar_total():
    """Carga la hoja TOTAL como dataframe y retorna también el worksheet."""
    ws = client.open_by_key(LOG_SHEET_ID).worksheet(LOG_HOJA)
    df = get_as_dataframe(ws, evaluate_formulas=True).fillna("")
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
    """
    Reasigna el agente de las cuentas seleccionadas sin borrar columnas
    como 'Fecha'. Solo actualiza celdas en la columna 'Agente'.
    """
    # Crear índices temporales
    df_reasignar = df_reasignar.set_index("Cuenta")
    df_original = df_original.set_index("Cuenta")

    # Obtener encabezados y localizar columnas
    header = ws.row_values(1)
    col_agente = header.index("Agente") + 1
    col_cuenta = header.index("Cuenta") + 1

    # Mapear cuentas a filas (sin incluir encabezado)
    cuentas_hoja = ws.col_values(col_cuenta)
    cuenta_a_fila = {
        cuenta: fila for fila, cuenta in enumerate(cuentas_hoja[1:], start=2)
    }

    # Preparar actualizaciones
    updates = []
    for cuenta in df_reasignar.index:
        fila = cuenta_a_fila.get(cuenta)
        if fila:
            # Actualiza el DataFrame en memoria
            df_original.at[cuenta, "Agente"] = nuevo_agente
            # Programa la celda a modificar
            updates.append({
                "range": gspread.utils.rowcol_to_a1(fila, col_agente),
                "values": [[nuevo_agente]]
            })

    # Ejecutar actualizaciones en lote
    if updates:
        ws.spreadsheet.batch_update({
            "valueInputOption": "USER_ENTERED",
            "data": updates
        })

    df_original.reset_index(inplace=True)
    return df_original

def contar_total_gestiones():
    """
    Devuelve el número de filas en la hoja TOTAL
    cuyo campo 'Gestion' no está vacío.
    """
    df, _ = cargar_total()
    if "Gestion" in df.columns:
        return int((df["Gestion"].astype(str).str.strip() != "").sum())
    return 0
