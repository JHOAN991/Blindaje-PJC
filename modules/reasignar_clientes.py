import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe
import pandas as pd

# === CONFIGURACIÓN ===
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
LOG_SHEET_ID = "1YTGCDwIuYNqZpt6qvdUSYSoK5vbPHShvf2b4qOnF-58"
LOG_HOJA = "TOTAL"

# 👥 Agentes válidos para reasignación
AGENTES_REASIGNACION = [
    "Michell  Escobar", "Luris Henriquez", "Nadeshka Castillo",
    "Alejandro Bonilla", "Julian Ramirez", "Emily Medina", "Jhoan Medina",
    "Rosmery Umanzor", "John Florian", "Sugeidys Batista",
    "Darineth Diaz", "Edivinia Duarte", "Veronica Zuñiga"
]

def mostrar_reasignacion():
    st.title("🔄 Reasignar Clientes sin Gestión")

    # --- Autenticación ---
    creds_info = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    client = gspread.authorize(creds)

    # --- Cargar hoja TOTAL ---
    ws = client.open_by_key(LOG_SHEET_ID).worksheet(LOG_HOJA)
    df = get_as_dataframe(ws).fillna("")

    if df.empty:
        st.warning("No se pudieron cargar datos desde la hoja TOTAL.")
        return

    # Guardar el orden y las columnas originales para no alterar estructura
    columnas_originales = df.columns.tolist()

    # === Filtros Base y CICLO ===
    st.subheader("📊 Filtros de segmentación")
    bases = sorted(df["Base"].dropna().unique())
    base_sel = st.selectbox("Selecciona la Base", bases)

    ciclos = sorted(df[df["Base"] == base_sel]["CICLO"].dropna().unique())
    ciclos.insert(0, "Todos")
    ciclo_sel = st.selectbox("Selecciona el CICLO", ciclos)

    if ciclo_sel == "Todos":
        df_filtrado_base = df[df["Base"] == base_sel]
    else:
        df_filtrado_base = df[(df["Base"] == base_sel) & (df["CICLO"] == ciclo_sel)]

    # === Sección A: Vista previa por agente (dinámica) ===
    st.subheader("👀 Vista previa de clientes sin gestión por agente")

    df_sin_gestion = df_filtrado_base[df_filtrado_base["Gestion"] == ""]
    resumen_agentes = (
        df_sin_gestion.groupby("Agente")
        .size()
        .reset_index(name="Cantidad")
        .sort_values("Cantidad", ascending=False)
    )

    st.dataframe(resumen_agentes, use_container_width=True)

    with st.expander("🔎 Ver detalle por agente"):
        if not resumen_agentes.empty:
            agente_vista = st.selectbox("Selecciona un agente para ver sus clientes", resumen_agentes["Agente"])
            detalle = df_sin_gestion[df_sin_gestion["Agente"] == agente_vista]
            st.dataframe(detalle, use_container_width=True)

            # ✅ Opción de descarga
            csv = detalle.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Descargar clientes del agente en CSV",
                data=csv,
                file_name=f"clientes_{agente_vista.replace(' ', '_')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No hay agentes con cuentas sin gestión según los filtros seleccionados.")

    st.markdown("---")

    # === Sección B: Reasignación de clientes ===
    st.subheader("🔁 Reasignar clientes sin gestión")

    agentes_actuales = sorted(df_filtrado_base["Agente"].dropna().unique())
    agente_sel = st.selectbox("Selecciona el agente actual", agentes_actuales)

    # --- Filtrar registros sin gestión ---
    df_filtrado = df_filtrado_base[
        (df_filtrado_base["Agente"] == agente_sel) &
        (df_filtrado_base["Gestion"] == "")
    ].copy()

    st.info(f"🔍 Se encontraron **{len(df_filtrado)}** cuentas sin gestión asignadas al agente seleccionado.")

    if len(df_filtrado) == 0:
        return

    # --- Elegir cantidad ---
    max_cuentas = len(df_filtrado)
    cant_reasignar = st.number_input(
        "¿Cuántas cuentas deseas reasignar?",
        min_value=1, max_value=max_cuentas, value=max_cuentas, step=1
    )

    # --- Nuevo agente ---
    nuevo_agente = st.selectbox(
        "Nuevo agente responsable",
        [a for a in AGENTES_REASIGNACION if a != agente_sel]
    )

    # --- Acción ---
    if st.button("✅ Reasignar cuentas"):
        df_reasignar = df_filtrado.head(cant_reasignar).copy()

        # Actualizar agente en el DataFrame original sin alterar estructura
        df.set_index("Cuenta", inplace=True)
        df_reasignar.set_index("Cuenta", inplace=True)
        for cuenta in df_reasignar.index:
            if cuenta in df.index:
                df.at[cuenta, "Agente"] = nuevo_agente
        df.reset_index(inplace=True)

        # Reordenar exactamente igual que al inicio
        df = df.reindex(columns=columnas_originales)

        # Guardar cambios
        ws.clear()
        set_with_dataframe(ws, df, include_index=False)

        st.success(f"🎉 {cant_reasignar} cuentas fueron reasignadas a **{nuevo_agente}** sin cambiar la estructura de la hoja.")
