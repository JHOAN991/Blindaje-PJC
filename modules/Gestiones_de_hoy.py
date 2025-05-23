def mostrar_informe():
    import streamlit as st
    import pandas as pd
    from datetime import datetime, time
    import gspread
    from google.oauth2.service_account import Credentials
    from dateutil import parser

    # === CONFIGURACIÓN ===
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Cargar las credenciales desde streamlit secrets
    service_account_info = dict(st.secrets["gcp_service_account"])
    CREDS = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)

# Autorizar cliente gspread
    client = gspread.authorize(CREDS)
    # === ID de la hoja y nombre de hoja ===
    LOG_SHEET_ID = "1YTGCDwIuYNqZpt6qvdUSYSoK5vbPHShvf2b4qOnF-58"
    HOJA = "Base_Madre"

    # Título de la página
    st.title("📊 Informe desde Base_Madre")

    # Carga de datos
    try:
        sheet = client.open_by_key(LOG_SHEET_ID).worksheet(HOJA)
        data = sheet.get_all_records()
    except Exception as e:
        st.error("❌ Error al conectar con Google Sheets. Verifica el ID del documento y el acceso compartido.")
        st.stop()

    # Carga y renombramiento de columnas
    df = pd.DataFrame(data)
    campos = {
        "BASE": "BASE", "SEGEMENTO REGIONAL": "BUNDLE", "SUSCRIPTOR": "SUSCRIPTOR",
        "Cuenta": "Cuenta", "NOMBRE_CLIENTE": "NOMBRE_CLIENTE", "Numero 1": "Numero 1",
        "EMAIL": "Fijo 2", "Agente": "Agente", "Fecha": "Fecha", "Hora": "Hora",
        "Gestion": "Gestion", "Razón": "Razon", "Comentario": "Comentario"
    }
    df = df.rename(columns=campos)

    # Conversión de tipos
    for col in ["SUSCRIPTOR", "Cuenta", "Numero 1", "Fijo 2"]:
        if col in df.columns:
            df[col] = df[col].astype(str)

    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce", dayfirst=True)

    def parsear_hora(valor):
        try:
            return parser.parse(valor).time()
        except:
            return None

    df["Hora"] = df["Hora"].astype(str).apply(parsear_hora)

    # Filtros
    fecha_seleccionada = st.date_input("📅 Selecciona la fecha", value=datetime.now().date())
    agentes_disponibles = sorted(df["Agente"].dropna().unique().tolist())
    agente_seleccionado = st.selectbox("👤 Selecciona un agente", ["Todos"] + agentes_disponibles)
    suscriptor_input = st.text_input("🔍 Buscar por SUSCRIPTOR (opcional)").strip()

    # Aplicar filtros
    df_filtrado = df[df["Fecha"].dt.date == fecha_seleccionada]
    if agente_seleccionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Agente"] == agente_seleccionado]
    if suscriptor_input:
        df_filtrado = df_filtrado[df_filtrado["SUSCRIPTOR"].str.contains(suscriptor_input, na=False)]

    if df_filtrado.empty:
        st.warning("⚠️ No se encontraron resultados con los filtros aplicados.")
        st.stop()

    # === Tabla de resumen por intervalos de horas ===
    st.subheader("⏰ Gestiones Completadas")

    df_completadas = df_filtrado[df_filtrado["Gestion"] == "Completado"].copy()
    df_completadas = df_completadas[df_completadas["Hora"].notnull()]

    df_completadas["Hora_dt"] = df_completadas["Hora"].apply(lambda h: datetime.combine(fecha_seleccionada, h))

    intervalos = [(hour, hour + 1) for hour in range(9, 18)]
    nombres_columnas = [f"{h}am - {h+1}am" if h < 12 else
                        f"{h-12}pm - {h+1-12}pm" if h < 23 else "11pm - 12am"
                        for h, _ in intervalos]

    agentes = sorted(df_completadas["Agente"].dropna().unique())
    resumen = pd.DataFrame(index=agentes, columns=nombres_columnas).fillna(0)

    for (inicio, fin), col_name in zip(intervalos, nombres_columnas):
        t_inicio = datetime.combine(fecha_seleccionada, time(inicio, 0))
        t_fin = datetime.combine(fecha_seleccionada, time(fin, 0))
        
        mask = df_completadas["Hora_dt"].between(t_inicio, t_fin)
        conteo = df_completadas[mask].groupby("Agente").size()
        
        for agente, cantidad in conteo.items():
            resumen.at[agente, col_name] = cantidad

    resumen["TOTAL"] = resumen.sum(axis=1)
    st.dataframe(resumen.astype(int))

    # === Métricas finales ===
    total_gestiones = len(df_filtrado)
    st.subheader("🧾 Resumen del Día")
    col1, col2 = st.columns(2)
    col1.metric("Total de Gestiones", total_gestiones)
    col2.metric("Fecha", fecha_seleccionada.strftime("%d/%m/%Y"))

    # === Mostrar detalles ===
    st.subheader("📋 Detalles")
    st.dataframe(df_filtrado[[
        "Agente", "Fecha", "Hora", "Gestion", "Razon", "Comentario",
        "Cuenta", "SUSCRIPTOR", "Numero 1", "Fijo 2"
    ]])
