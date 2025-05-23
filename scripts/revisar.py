import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from google.oauth2.service_account import Credentials
import streamlit as st

# ----- MAPEO DE COLUMNAS -----
MAPEO = {
    "Base": "Base",
    "BUNDLE": "BUNDLE",
    "PLAN INT": "plan_int_actual",
    "OFRECER": "plan_int_nuevo",
    "Factura Actual": "factura_int_actual",
    "Nueva factura catalogo": "factura_int_nuevo",
    "Ajuste Permanente CM": "descuento_int_nuevo",
    "Incremento + Impuesto": "plan_tv_actual",
    "SUSCRIPTOR": "SUSCRIPTOR",
    "Cuenta": "Cuenta",
    "NOMBRE_CLIENTE": "factura_tv_actual",
    "CICLO": "CICLO",
    "Numero 1": "plan_tv_nuevo",
    "Numero 2": "descuento_tv_nuevo",
    "Numero 3": "factura_tv_nuevo",
    "Numero 4": "vix",
    "Fijo 1": "hbo",
    "Fijo 2": "universal",
    "Agente": "Agente",
    "Fecha": "Fecha",
    "Gestion": "Gestion",
    "Razón": "Razon",
    "Comentario": "Comentario",
    "Incremento": "star",
    "Mejor contacto": "combo",
    "CEDULA": "disney",
    "INCREMEN TOTAL": "paramount",
    "plan_tel_actual": "plan_tel_actual",
    "factura_tel_actual": "factura_tel_actual",
    "factura_total_vieja": "factura_total_vieja",
    "factura_total_nueva": "factura_total_nueva",
    "comentario tytan" : "comentario tytan"
}

# ---------- CONFIGURACIÓN ----------
SHEET_ID = "1YTGCDwIuYNqZpt6qvdUSYSoK5vbPHShvf2b4qOnF-58"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS = Credentials.from_service_account_info(
    dict(st.secrets["gcp_service_account"]), scopes=SCOPES
)
client = gspread.authorize(CREDS)

def procesar_para_revision():
    """
    1) Mueve nuevos registros con 'Gestion' ≠ '' y ≠ 'Sin ajustes' a REVICION.
    2) Devuelve:
       • df_alerta ........ Registros con 'Sin ajustes'
       • df_rev_vacio ...... Registros en REVICION con Base ≠ '' y Estado de Gestion vacío
    """
    sh = client.open_by_key(SHEET_ID)

    # ---------- 1. Leer Base_Madre ----------
    ws_base = sh.worksheet("Base_Madre")
    df_base = get_as_dataframe(ws_base).fillna("")
    df_base.columns = df_base.columns.str.strip()

    df_con_ajuste = df_base[
        (df_base["Gestion"] != "") & (df_base["Gestion"].str.lower() != "sin ajustes")
    ].copy()

    df_sin_ajuste = df_base[
        df_base["Gestion"].str.lower() == "sin ajustes"
    ][["Cuenta", "Agente", "Gestion", "Base"]].copy()

    # ---------- 2. Preparar registros a mover ----------
    if not df_con_ajuste.empty:
        df_mapeado = df_con_ajuste.rename(columns=MAPEO)
        columnas_destino = [c for c in MAPEO.values() if c in df_mapeado.columns]
        df_mapeado = df_mapeado[columnas_destino]

        if "plan_tv_nuevo" in df_mapeado.columns:
            df_mapeado["plan_tv_nuevo"] = df_mapeado["plan_tv_nuevo"].replace("", "Vacio")

        # ---------- 3. Cargar / crear REVICION ----------
        try:
            ws_rev = sh.worksheet("REVICION")
            df_rev = get_as_dataframe(ws_rev).fillna("")
            df_rev.columns = df_rev.columns.str.strip()
        except gspread.exceptions.WorksheetNotFound:
            ws_rev = sh.add_worksheet(title="REVICION", rows="1000", cols="40")
            df_rev = pd.DataFrame(columns=columnas_destino)

        # Eliminar duplicados de nombre de columna
        df_rev = df_rev.loc[:, ~df_rev.columns.duplicated()]
        df_mapeado = df_mapeado.loc[:, ~df_mapeado.columns.duplicated()]

        # Añadir solo cuentas nuevas que NO tengan gestión ya registrada
        if not df_rev.empty:
            cuentas_existentes_con_gestion = df_rev[
                df_rev["Gestion"].astype(str).str.strip() != ""
            ]["Cuenta"].astype(str).unique()

            df_nuevos = df_mapeado[
                ~df_mapeado["Cuenta"].astype(str).isin(cuentas_existentes_con_gestion)
            ]

            if not df_nuevos.empty:
                df_rev = pd.concat([df_rev, df_nuevos], ignore_index=True)
        else:
            df_rev = df_mapeado

        set_with_dataframe(ws_rev, df_rev, include_index=False)
    else:
        # Si REVICION ya existe, cargarla para siguiente paso
        try:
            ws_rev = sh.worksheet("REVICION")
            df_rev = get_as_dataframe(ws_rev).fillna("")
            df_rev.columns = df_rev.columns.str.strip()
        except gspread.exceptions.WorksheetNotFound:
            df_rev = pd.DataFrame()

    # ---------- 4. Filtrar Base ≠ '' y Estado de Gestion vacío EN REVICION ----------
    if not df_rev.empty and "Estado de Gestion" in df_rev.columns:
        df_rev_vacio = df_rev[
            (df_rev["Base"] != "") & (df_rev["Estado de Gestion"].astype(str).str.strip() == "")
        ][["Base", "Cuenta", "Agente"]].copy()
    else:
        df_rev_vacio = pd.DataFrame(columns=["Base", "Cuenta", "Agente"])

    return df_sin_ajuste, df_rev_vacio
