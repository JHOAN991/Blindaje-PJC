import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe

# === CONFIGURACIÓN ===
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS = Credentials.from_service_account_info(
    dict(st.secrets["gcp_service_account"]), scopes=SCOPES
)
client = gspread.authorize(CREDS)

SPREADSHEET_ID = "1YTGCDwIuYNqZpt6qvdUSYSoK5vbPHShvf2b4qOnF-58"
SHEET_ORIGEN = "TOTAL"
SHEET_DESTINO = "Base_Madre"

LLAVES = ["Cuenta", "Base"]
CAMPOS_ACTUALIZAR = [
    "Fecha", "Hora", "Gestion", "Razon", "Comentario",
    "Agente", "Mejor contacto", "comentario tytan"
]
COLUMNAS_DECIMALES = [
    "Factura Actual", "Nueva factura catalogo", "Ajuste Permanente CM", "NOMBRE_CLIENTE",
    "Numero 2", "Numero 3", "Fijo 1", "Fijo 2",
    "factura_tel_actual", "factura_total_vieja", "factura_total_nueva"
]

def cargar_datos_hoja(nombre_hoja):
    try:
        ws = client.open_by_key(SPREADSHEET_ID).worksheet(nombre_hoja)
        df = get_as_dataframe(ws, dtype=str).dropna(how='all').fillna("").astype(str)
        return df, ws
    except Exception as e:
        st.error(f"Error al cargar la hoja {nombre_hoja}: {e}")
        return pd.DataFrame(), None

def actualizar_base(df_destino, df_origen):
    actualizados = 0
    origen_dict = {
        (fila["Cuenta"], fila["Base"]): fila for _, fila in df_origen.iterrows()
    }

    for i, fila in df_destino.iterrows():
        llave = (fila.get("Cuenta", ""), fila.get("Base", ""))
        if llave in origen_dict:
            fila_origen = origen_dict[llave]
            cambios = False
            for campo in CAMPOS_ACTUALIZAR:
                if campo in df_destino.columns and campo in fila_origen:
                    valor_actual = fila[campo]
                    valor_nuevo = fila_origen[campo]
                    if valor_actual != valor_nuevo:
                        df_destino.at[i, campo] = valor_nuevo
                        cambios = True
            if cambios:
                actualizados += 1

    return df_destino, actualizados

def formatear_decimales(df, columnas):
    for col in columnas:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: 
                "{:.2f}".format(float(str(x).replace(",", "."))).replace(".", ",")
                if str(x).replace(",", ".").replace(".", "").isdigit() else x
            )
    return df

# === FUNCIÓN EXPORTABLE ===

def ejecutar_actualizacion(progreso_callback=None):
    if progreso_callback: progreso_callback(10)
    df_origen, _ = cargar_datos_hoja(SHEET_ORIGEN)

    if progreso_callback: progreso_callback(30)
    df_destino, ws_destino = cargar_datos_hoja(SHEET_DESTINO)

    if df_origen.empty or df_destino.empty or ws_destino is None:
        st.warning("No se pudieron cargar los datos.")
        return

    if progreso_callback: progreso_callback(50)
    df_actualizado, total_actualizados = actualizar_base(df_destino, df_origen)

    if total_actualizados > 0:
        if progreso_callback: progreso_callback(70)
        df_actualizado = formatear_decimales(df_actualizado, COLUMNAS_DECIMALES)

        try:
            if progreso_callback: progreso_callback(90)
            ws_destino.clear()
            set_with_dataframe(ws_destino, df_actualizado, include_index=False)
        except Exception as e:
            st.error(f"Error al escribir en la hoja destino: {e}")
            return

    if progreso_callback: progreso_callback(100)
