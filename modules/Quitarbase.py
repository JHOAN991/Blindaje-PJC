import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_ID = "1YTGCDwIuYNqZpt6qvdUSYSoK5vbPHShvf2b4qOnF-58"
HOJA_TOTAL = "TOTAL"

def mostrar_quitarbase():
    st.subheader("🗂 Quitar valores de la columna Base / Revisión de Gestión")

    # Configuración y cliente
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=SCOPES)
    client = gspread.authorize(creds)

    try:
        ws = client.open_by_key(SHEET_ID).worksheet(HOJA_TOTAL)
        df = get_as_dataframe(ws, evaluate_formulas=True).fillna("")

        if df.empty:
            st.warning("⚠️ No hay datos en la hoja TOTAL.")
            return

        # Mostrar las bases disponibles
        if "Base" not in df.columns:
            st.error("❌ La hoja no contiene la columna 'Base'.")
            return

        bases_disponibles = sorted(df["Base"].unique())
        base_seleccionada = st.selectbox("Selecciona una base para quitar:", bases_disponibles)

        if st.button(f"❌ Quitar base '{base_seleccionada}'"):
            # Filtrar DataFrame: eliminar esa base
            df_filtrado = df[df["Base"] != base_seleccionada].copy()

            if df_filtrado.empty:
                st.warning("⚠️ Al eliminar esta base, ya no quedan datos. Se dejará sólo el encabezado.")

            # Preparar datos para update
            headers = list(df.columns)
            values = df_filtrado.values.tolist()

            # Limpiar hoja y actualizar
            ws.clear()
            # Sobrescribir desde A1: encabezado + datos
            ws.update('A1', [headers] + values)

            st.success(f"✅ Base '{base_seleccionada}' eliminada correctamente.")
            st.info(f"Número de filas ahora: {len(df_filtrado)}")

    except Exception as e:
        st.error(f"❌ Error al procesar la hoja: {e}")
        print(f"❌ Error: {e}")
