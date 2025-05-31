import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from google.oauth2.service_account import Credentials
import streamlit as st
import re

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
    "comentario tytan": "comentario tytan"
}

# Columnas que pueden venir como números decimales con ".0"
COLUMNAS_DECIMALES = [
    "Factura Actual", "Nueva factura catalogo", "Ajuste Permanente CM", "NOMBRE_CLIENTE",
    "Numero 2", "Numero 3", "Fijo 1", "Fijo 2",
    "factura_tel_actual", "factura_total_vieja", "factura_total_nueva", "Cuenta", "SUSCRIPTOR"
]

SHEET_ID = "1YTGCDwIuYNqZpt6qvdUSYSoK5vbPHShvf2b4qOnF-58"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS = Credentials.from_service_account_info(
    dict(st.secrets["gcp_service_account"]), scopes=SCOPES
)
client = gspread.authorize(CREDS)


# Función auxiliar: convertir columnas a texto limpio
def convertir_a_texto(df):
    return df.astype(str).applymap(lambda x: x.strip() if isinstance(x, str) else x)

# Función auxiliar: limpiar ".0" de columnas numéricas
def limpiar_decimales(df: pd.DataFrame, columnas: list) -> pd.DataFrame:
    for col in columnas:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    return df

# Función auxiliar: deduplicar REVICION priorizando con gestión
def deduplicar_revision(df):
    df["prioridad"] = df["Estado de Gestion"].apply(lambda x: 0 if x.strip() == "" else 1)
    df = df.sort_values(by=["Cuenta", "Base", "prioridad"], ascending=[True, True, False])
    df = df.drop_duplicates(subset=["Cuenta", "Base"], keep="first")
    df.drop(columns=["prioridad"], inplace=True)
    return df

# FUNCIÓN PRINCIPAL
def procesar_para_revision():
    sh = client.open_by_key(SHEET_ID)

    # Leer Base_Madre
    ws_base = sh.worksheet("Base_Madre")
    df_base = get_as_dataframe(ws_base, dtype=str).fillna("")
    df_base.columns = df_base.columns.str.strip()

    # Limpiar columnas decimales
    df_base = limpiar_decimales(df_base, COLUMNAS_DECIMALES)

    # Filtrar con y sin ajustes
    df_con_ajuste = df_base[
        (df_base["Gestion"] != "") & (df_base["Gestion"].str.lower() != "sin ajustes")
    ].copy()

    df_sin_ajuste = df_base[
        df_base["Gestion"].str.lower() == "sin ajustes"
    ][["Cuenta", "Agente", "Gestion", "Base"]].copy()

    # Preparar registros con gestión
    if not df_con_ajuste.empty:
        df_mapeado = df_con_ajuste.rename(columns=MAPEO)
        columnas_destino = [c for c in MAPEO.values() if c in df_mapeado.columns]
        df_mapeado = df_mapeado[columnas_destino]

        if "plan_tv_nuevo" in df_mapeado.columns:
            df_mapeado["plan_tv_nuevo"] = df_mapeado["plan_tv_nuevo"].replace("", "Vacio")

        df_mapeado = convertir_a_texto(df_mapeado)

        # Cargar o crear hoja REVICION
        try:
            ws_rev = sh.worksheet("REVICION")
            df_rev = get_as_dataframe(ws_rev, dtype=str).fillna("")
            df_rev.columns = df_rev.columns.str.strip()
            df_rev = limpiar_decimales(df_rev, ["Cuenta"])
        except gspread.exceptions.WorksheetNotFound:
            ws_rev = sh.add_worksheet(title="REVICION", rows="1000", cols="60")
            df_rev = pd.DataFrame(columns=columnas_destino)

        # Evitar columnas duplicadas
        df_rev = df_rev.loc[:, ~df_rev.columns.duplicated()]
        df_mapeado = df_mapeado.loc[:, ~df_mapeado.columns.duplicated()]

        claves = [c for c in ["Cuenta", "Base"] if c in df_rev.columns]
        if claves and not df_rev.empty:
            existentes = df_rev[claves].apply(tuple, axis=1).unique()
            df_nuevos = df_mapeado[~df_mapeado[claves].apply(tuple, axis=1).isin(existentes)]
        else:
            df_nuevos = df_mapeado

        # Concatenar y deduplicar
        df_rev = pd.concat([df_rev, df_nuevos], ignore_index=True)
        df_rev = convertir_a_texto(df_rev)
        df_rev = deduplicar_revision(df_rev)

        set_with_dataframe(ws_rev, df_rev, include_index=False)

    else:
        # Solo limpiar REVICION si ya existe
        try:
            ws_rev = sh.worksheet("REVICION")
            df_rev = get_as_dataframe(ws_rev, dtype=str).fillna("")
            df_rev.columns = df_rev.columns.str.strip()
            df_rev = convertir_a_texto(df_rev)
            df_rev = deduplicar_revision(df_rev)
            set_with_dataframe(ws_rev, df_rev, include_index=False)
        except gspread.exceptions.WorksheetNotFound:
            df_rev = pd.DataFrame()

    # Filtrar registros sin Estado de Gestión
    if not df_rev.empty and "Estado de Gestion" in df_rev.columns:
        df_rev_vacio = df_rev[
            (df_rev["Base"] != "") & (df_rev["Estado de Gestion"].str.strip() == "")
        ][["Base", "Cuenta", "Agente"]].copy()
    else:
        df_rev_vacio = pd.DataFrame(columns=["Base", "Cuenta", "Agente"])

    return df_sin_ajuste, df_rev_vacio
