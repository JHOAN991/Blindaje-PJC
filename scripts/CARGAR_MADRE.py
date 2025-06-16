import pandas as pd
import os
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe
import streamlit as st  # Solo necesario si ejecutas desde Streamlit

# === CONFIGURACIÓN ===
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
service_account_info = dict(st.secrets["gcp_service_account"])
CREDS = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
client = gspread.authorize(CREDS)
SPREADSHEET_ID = "1YTGCDwIuYNqZpt6qvdUSYSoK5vbPHShvf2b4qOnF-58"
SHEET_NAME = "Base_Madre"

# === RUTAS LOCALES ===
directorio_bases = "BASES"
directorio_cargados = "Bases_Cargadas"

columnas_deseadas = [
    "Base", "BUNDLE", "PLAN INT", "OFRECER", "Factura Actual", "Nueva factura catalogo",
    "Ajuste Permanente CM", "Incremento + Impuesto", "SUSCRIPTOR", "Cuenta", "NOMBRE_CLIENTE",
    "CICLO", "Numero 1", "Numero 2", "Numero 3", "Numero 4", "Fijo 1", "Fijo 2", "Agente",
    "Fecha", "Hora", "Gestion", "Razon", "Comentario", "Incremento", "Mejor contacto",
    "CEDULA", "INCREMEN TOTAL", "plan_tel_actual", "factura_tel_actual", "factura_total_vieja", "factura_total_nueva", "Subida", "comentario tytan"
]

def asignar_agentes(df, agentes):
    total = len(df)
    if not agentes:
        df["Agente"] = ""
        return df

    asignaciones = [total // len(agentes)] * len(agentes)
    for i in range(total % len(agentes)):
        asignaciones[i] += 1

    df["Agente"] = [agente for agente, n in zip(agentes, asignaciones) for _ in range(n)]
    return df

def ejecutar_carga(agentes=[]):
    os.makedirs(directorio_cargados, exist_ok=True)

    try:
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
        df_maestro = get_as_dataframe(sheet, dtype=str, evaluate_formulas=True).fillna("")
        print("📂 Datos cargados desde Base_Madre.")
    except Exception as e:
        print(f"⚠️ No se pudo cargar Base_Madre. Se creará nueva. Error: {e}")
        df_maestro = pd.DataFrame(columns=columnas_deseadas)

    archivos = [f for f in os.listdir(directorio_bases) if f.lower().endswith(".csv")]
    if not archivos:
        print("📭 No hay archivos para procesar en la carpeta BASES.")
        return

    for archivo in archivos:
        ruta = os.path.join(directorio_bases, archivo)
        try:
            df = pd.read_csv(ruta, dtype=str).fillna("")
            cols_validas = [col for col in columnas_deseadas if col in df.columns]
            if not cols_validas:
                print(f"⚠️ {archivo} ignorado (sin columnas relevantes).")
                continue

            df_filtrado = df.reindex(columns=columnas_deseadas, fill_value="")
            df_filtrado = asignar_agentes(df_filtrado, agentes)

            df_maestro = pd.concat([df_maestro, df_filtrado], ignore_index=True)
            print(f"✅ {archivo} agregado con {len(df_filtrado)} registros.")

            os.replace(ruta, os.path.join(directorio_cargados, archivo))
            print(f"📦 {archivo} movido a '{directorio_cargados}/'.")

        except Exception as e:
            print(f"❌ Error procesando {archivo}: {e}")

    try:
        df_maestro = df_maestro[columnas_deseadas]
        sheet.clear()
        set_with_dataframe(sheet, df_maestro, include_index=False)
        print(f"\n✅ Base_Madre actualizada con {len(df_maestro)} registros.")
    except Exception as e:
        print(f"❌ Error al escribir en Google Sheets: {e}")

# Para permitir uso desde terminal si es necesario
if __name__ == "__main__":
    import sys
    agentes_str = sys.argv[1] if len(sys.argv) > 1 else ""
    agentes_lista = [a.strip() for a in agentes_str.split(",") if a.strip()]
    ejecutar_carga(agentes_lista)
