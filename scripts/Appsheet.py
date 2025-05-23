import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
service_account_info = dict(st.secrets["gcp_service_account"])
CREDS = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
client = gspread.authorize(CREDS)

SPREADSHEET_ID = "1YTGCDwIuYNqZpt6qvdUSYSoK5vbPHShvf2b4qOnF-58"
SHEET_ORIGEN = "TOTAL"
SHEET_DESTINO = "Base_Madre"

CAMPOS_ACTUALIZAR = [
    "Fecha", "Hora", "Gestion", "Razon", "Comentario",
    "Agente", "Mejor contacto", "comentario tytan"
]
LLAVES = ["Cuenta", "Base"]

# === FUNCIONES ===

def cargar_datos_hoja(nombre_hoja):
    try:
        print(f"Cargando datos desde hoja: {nombre_hoja}...")
        ws = client.open_by_key(SPREADSHEET_ID).worksheet(nombre_hoja)
        df = get_as_dataframe(ws, dtype=str).dropna(how='all').fillna("").astype(str)
        print(f"Datos cargados: {df.shape[0]} filas.")
        return df, ws
    except Exception as e:
        print(f"Error al cargar datos de la hoja '{nombre_hoja}': {e}")
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
                print(f"Actualizado: Cuenta={fila['Cuenta']} Base={fila['Base']}")
                actualizados += 1

    return df_destino, actualizados

# === EJECUCIÓN PRINCIPAL ===

def main():
    df_origen, _ = cargar_datos_hoja(SHEET_ORIGEN)
    df_destino, ws_destino = cargar_datos_hoja(SHEET_DESTINO)

    if df_origen.empty or df_destino.empty or ws_destino is None:
        print("No se puede continuar: error al cargar hojas.")
        return

    df_actualizado, total_actualizados = actualizar_base(df_destino, df_origen)

    if total_actualizados > 0:
        print("Guardando cambios en la hoja Base_Madre...")
        ws_destino.clear()
        set_with_dataframe(ws_destino, df_actualizado)
        print(f"{total_actualizados} registros actualizados en 'Base_Madre'.")
    else:
        print("No hubo cambios que actualizar.")

if __name__ == "__main__":
    main()
