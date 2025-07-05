import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from google.oauth2.service_account import Credentials
import streamlit as st

# ----- CONFIGURACIÓN -----
MAPEO_COLUMNAS = {
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
    "Razon": "Razon",
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

COLUMNAS_DECIMALES = [
    "Factura Actual", "Nueva factura catalogo", "Ajuste Permanente CM", "NOMBRE_CLIENTE",
    "Numero 2", "Numero 3", "Fijo 1", "Fijo 2",
    "factura_tel_actual", "factura_total_vieja", "factura_total_nueva", "Cuenta", "SUSCRIPTOR"
]

ESTADOS_MANTENER = ["REVISANDO", "MAL GESTIONADO"]
ESTADO_ELIMINAR = "BIEN GESTIONADO"

# ----- FUNCIONES AUXILIARES -----
def _limpiar_datos(df, columnas_decimales=None):
    """Limpia y formatea el DataFrame"""
    if columnas_decimales is None:
        columnas_decimales = []
    df = df.fillna("")
    df.columns = df.columns.str.strip()
    for col in columnas_decimales:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    return df

def _filtrar_estados(df):
    """Filtra el DataFrame según los estados de gestión"""
    if "Estado de Gestion" not in df.columns:
        return df
    df["Estado de Gestion"] = df["Estado de Gestion"].str.strip().str.upper()
    condicion = (
        df["Estado de Gestion"].isin(ESTADOS_MANTENER) |
        df["Estado de Gestion"].eq("")
    ) & ~df["Estado de Gestion"].eq(ESTADO_ELIMINAR)
    return df[condicion].copy()

def _obtener_clientes_para_revision(df_base, df_revision):
    """
    Identifica clientes que tienen 'Gestion' (no vacío)
    pero no tienen valor en 'Gestion-Revision'
    y que aún no están en REVICION.
    """
    if df_revision.empty:
        condicion = (df_base["Gestion"].str.strip() != "") & (df_base["Gestion-Revision"].str.strip() == "")
        return df_base[condicion].copy()

    # Crear clave para comparar
    df_base["clave"] = df_base["Cuenta"] + "|" + df_base["Base"]
    df_revision["clave"] = df_revision["Cuenta"] + "|" + df_revision["Base"]

    condicion = (
        (df_base["Gestion"].str.strip() != "") &
        (df_base["Gestion-Revision"].str.strip() == "") &
        (~df_base["clave"].isin(df_revision["clave"]))
    )
    df_resultado = df_base[condicion].copy()
    return df_resultado.drop(columns=["clave"])

# ----- FUNCIÓN PRINCIPAL -----
def procesar_para_revision():
    """
    Procesa la hoja REVICION según los criterios requeridos.
    
    Returns:
        tuple: (df_sin_ajuste, df_rev_vacio)
               - df_sin_ajuste: Clientes con 'Sin ajustes'
               - df_rev_vacio: Clientes sin estado de gestión
    """
    try:
        # Conexión con Google Sheets
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]),
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(creds)
        sh = client.open_by_key("1YTGCDwIuYNqZpt6qvdUSYSoK5vbPHShvf2b4qOnF-58")

        # 1. Cargar Base_Madre
        ws_base = sh.worksheet("Base_Madre")
        df_base = get_as_dataframe(ws_base, dtype=str)
        df_base = _limpiar_datos(df_base, COLUMNAS_DECIMALES)

        # Filtrar clientes con 'Sin ajustes'
        df_sin_ajuste = df_base[
            df_base["Gestion"].str.strip().str.lower() == "sin ajustes"
        ][["Cuenta", "Agente", "Gestion", "Base"]].copy()

        # 2. Cargar o crear REVICION
        try:
            ws_rev = sh.worksheet("REVICION")
            df_rev = get_as_dataframe(ws_rev, dtype=str)
            df_rev = _limpiar_datos(df_rev)
        except gspread.exceptions.WorksheetNotFound:
            ws_rev = sh.add_worksheet(title="REVICION", rows="1000", cols="60")
            df_rev = pd.DataFrame()

        # 3. Filtrar REVICION
        df_rev_filtrado = _filtrar_estados(df_rev)

        # 4. Buscar clientes que tienen Gestion pero no Gestion-Revision
        df_nuevos = _obtener_clientes_para_revision(df_base, df_rev)

        if not df_nuevos.empty:
            # Mapear columnas
            df_nuevos_mapeado = df_nuevos.rename(columns=MAPEO_COLUMNAS)
            columnas_destino = [c for c in MAPEO_COLUMNAS.values() if c in df_nuevos_mapeado.columns]
            df_nuevos_mapeado = df_nuevos_mapeado[columnas_destino]

            # Combinar con REVICION filtrado
            df_final = pd.concat([df_rev_filtrado, df_nuevos_mapeado], ignore_index=True)
        else:
            df_final = df_rev_filtrado

        # 5. Guardar cambios en REVICION
        ws_rev.clear()
        set_with_dataframe(ws_rev, df_final, include_index=False)

        # 6. Preparar datos de retorno
        df_rev_vacio = df_final[
            (df_final["Base"] != "") &
            (df_final["Estado de Gestion"].str.strip() == "")
        ][["Base", "Cuenta", "Agente"]].copy()

        return df_sin_ajuste, df_rev_vacio

    except Exception as e:
        raise Exception(f"Error en procesar_para_revision: {str(e)}")
