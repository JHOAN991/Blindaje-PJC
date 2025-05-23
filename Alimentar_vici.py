import gspread
import streamlit as st
import pandas as pd
import os
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe

# === CONFIGURACIÓN ===
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
service_account_info = dict(st.secrets["gcp_service_account"])
CREDS = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
client = gspread.authorize(CREDS)
# === INGRESO DE IDS DESDE CONSOLA ===
ids = []
print("🔗 Ingresa los IDs de los documentos. Escribe '.' para terminar:")
while True:
    id_input = input("📝 ID de documento: ").strip()
    if id_input == ".":
        break
    if id_input:
        ids.append(id_input)

# === ARCHIVO DE SALIDA ===
os.makedirs("resultado", exist_ok=True)
ARCHIVO_SALIDA = "resultado/vici.csv"

# === UNIÓN DE HOJAS "TOTAL" ===
dataframes = []
header = None

for idx, sheet_id in enumerate(ids):
    try:
        sheet = client.open_by_key(sheet_id).worksheet("TOTAL")
        df = get_as_dataframe(sheet, dtype=str, evaluate_formulas=True).fillna("")

        if idx == 0:
            header = df.columns
        else:
            df.columns = header  # Unifica encabezados

        dataframes.append(df)
        print(f"✅ Archivo {idx+1}: {sheet_id} importado correctamente.")

    except Exception as e:
        print(f"⚠️ Error al procesar {sheet_id}: {e}")

# === PROCESAR Y EXPORTAR ===
if dataframes:
    df_final = pd.concat(dataframes, ignore_index=True)

    # === EXTRAER HORA Y LIMPIAR COLUMNA "Fecha" ===
    print("⏱️ Extrayendo hora de la columna 'Fecha' y limpiando...")
    df_final["Hora"] = df_final["Fecha"].str.extract(r"(\d{1,2}:\d{2})")
    df_final["Fecha"] = df_final["Fecha"].str.extract(r"^([^ ]+)")  # Dejar solo la fecha

    # === GUARDAR RESULTADO ===
    df_final.to_csv(ARCHIVO_SALIDA, index=False)
    print(f"\n📁 Exportación completada. Archivo limpio guardado en: {ARCHIVO_SALIDA}")
else:
    print("❌ No se cargó ningún archivo válido.")
# === ACA PROCESAMOS LOS ARCHIVOS DE VICI INCLUYENDO LA HORA ===