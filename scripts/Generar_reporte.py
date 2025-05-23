import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from datetime import datetime
import streamlit as st
from google.oauth2.service_account import Credentials
from io import BytesIO

# CONFIGURACIÓN
LOG_SHEET_ID = "1YTGCDwIuYNqZpt6qvdUSYSoK5vbPHShvf2b4qOnF-58"
DESTINO_SHEET_ID = "1puCLMavPb7cDNEyBU33aJkaUK4O48AZUA7Mi5yp3fUg"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
service_account_info = dict(st.secrets["gcp_service_account"])
CREDS = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
client = gspread.authorize(CREDS)

def generar_reporte_por_rango(fecha_inicio, fecha_fin):
    archivos = []  # Aquí guardaremos tuplas (nombre_archivo, BytesIO)

    fecha_inicio = pd.to_datetime(fecha_inicio)
    fecha_fin = pd.to_datetime(fecha_fin)

    print(f"[LOG] Filtrando desde {fecha_inicio} hasta {fecha_fin}")

    # Leer Base_Madre
    ws_base_madre = client.open_by_key(LOG_SHEET_ID).worksheet("Base_Madre")
    df_base_madre = get_as_dataframe(ws_base_madre).fillna("")

    # Normalizar nombres de columnas (minúsculas)
    df_base_madre.columns = df_base_madre.columns.str.lower()

    # Convertir fecha
    df_base_madre["fecha_dt"] = pd.to_datetime(df_base_madre["fecha"], format="%d/%m/%Y", errors="coerce")

    # Filtrar por rango
    df_filtrado = df_base_madre[
        (df_base_madre["fecha_dt"] >= fecha_inicio) &
        (df_base_madre["fecha_dt"] <= fecha_fin) &
        (df_base_madre["gestion"] != "")
    ]

    print(f"[LOG] Registros filtrados: {len(df_filtrado)}")

    bases_unicas = df_filtrado["base"].unique()

    resumen = []

    for base in bases_unicas:
        try:
            print(f"[LOG] Procesando base: {base}")
            df_base = df_filtrado[df_filtrado["base"] == base].copy()

            df_base["día"] = df_base["fecha_dt"].dt.day
            df_base["mes"] = df_base["fecha_dt"].dt.month
            df_base["año"] = df_base["fecha_dt"].dt.year

            columnas_origen_a_destino = {
                "gestion": "gestion",
                "día": "día",
                "mes": "mes",
                "año": "año",
                "agente": "agente",
                "razon": "razón",
                "comentario": "comentario tytan",
                "comentario tytan":"comentario"
            }



            columnas_necesarias = ["cuenta"] + list(columnas_origen_a_destino.keys())
            df_nuevo = df_base[columnas_necesarias].fillna("")

            df_nuevo.rename(columns=columnas_origen_a_destino, inplace=True)

            ws_destino = client.open_by_key(DESTINO_SHEET_ID).worksheet(base)
            df_destino = get_as_dataframe(ws_destino).fillna("")
            df_destino.columns = df_destino.columns.str.lower()

            if "cuenta" not in df_destino.columns:
                resumen.append({"base": base, "estado": "error", "error": "La hoja no contiene la columna 'cuenta'"})
                print(f"[ERROR] La hoja {base} no contiene la columna 'cuenta'")
                continue

            columnas_originales = list(df_destino.columns)

            df_destino.set_index("cuenta", inplace=True)
            df_nuevo.set_index("cuenta", inplace=True)

            cuentas_actualizadas = 0
            campos_modificados = 0

            for cuenta in df_nuevo.index:
                if cuenta in df_destino.index:
                    for col in columnas_origen_a_destino.values():
                        if col in df_destino.columns:
                            original = str(df_destino.at[cuenta, col]).strip()
                            nuevo = str(df_nuevo.at[cuenta, col]).strip()

                            # Siempre actualizar, pero contar si es distinto
                            if original != nuevo:
                                campos_modificados += 1

                            df_destino.at[cuenta, col] = nuevo
                    cuentas_actualizadas += 1

            cuentas_actualizadas = int(cuentas_actualizadas)
            campos_modificados = int(campos_modificados)

            df_destino.reset_index(inplace=True)
            df_destino = df_destino.reindex(columns=columnas_originales)

            ws_destino.clear()
            set_with_dataframe(ws_destino, df_destino, include_index=False)

            resumen.append({
                "base": base,
                "estado": f"✅ {cuentas_actualizadas} cuentas actualizadas, {campos_modificados} campos modificados"
            })

            # Crear archivo Excel para esta base
            excel_output = BytesIO()
            with pd.ExcelWriter(excel_output, engine="xlsxwriter") as writer:
                df_destino.to_excel(writer, index=False, sheet_name=base)
            excel_output.seek(0)

            nombre_archivo = f"{base}_{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}.xlsx"
            archivos.append((nombre_archivo, excel_output))

        except Exception as e:
            resumen.append({"base": base, "estado": "error", "error": f"Error procesando la base {base}: {e}"})
            print(f"[ERROR] Error procesando la base {base}: {e}")

    return resumen, archivos
