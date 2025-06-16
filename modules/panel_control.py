import streamlit as st
from scripts import Alimentar, subir_crm
from scripts.CARGAR_MADRE import ejecutar_carga  # ✅ ahora usamos función directamente

def mostrar_panel():
    st.title("📊 Panel de Control - Actualización de Base Madre")
    st.markdown("Este panel permite actualizar la Base_Madre con los registros más recientes desde la hoja TOTAL.")
    st.divider()

    st.markdown("### 🔄 Subir archivos o IDs para Alimentar")
    with st.expander("▶️ Opciones de carga"):
        google_ids_text = st.text_area("IDs de Google Sheets (uno por línea)", height=100)
        archivos_xlsx = st.file_uploader("Cargar archivos locales (.xlsx)", type=["xlsx"], accept_multiple_files=True)

        if archivos_xlsx or google_ids_text.strip():
            ejecutar_proceso_alimentar(google_ids_text, archivos_xlsx)

    st.divider()

    st.markdown("### 👤 Asignar Agente(s) antes de subir a Base_Madre")

    agentes_disponibles = [
        "Michell  Escobar", "Luris Henriquez", "Nadeshka Castillo", "Alejandro Bonilla", "Julian Ramirez", "Emily Medina",
        "Jhoan Medina", "Rosmery Umanzor", "John Florian", "Sugeidys Batista", "Darineth Diaz", "Edivinia Duarte", "Veronica Zuñiga"
    ]

    seleccion = st.multiselect("Selecciona uno o más agentes:", options=["Todos"] + agentes_disponibles, default=[])

    if "Todos" in seleccion:
        agentes_seleccionados = agentes_disponibles
    else:
        agentes_seleccionados = seleccion

    confirmar_agente = st.checkbox(f"Confirmo que quiero asignar los registros a: {', '.join(agentes_seleccionados) if agentes_seleccionados else 'Ninguno'}")

    if st.button("📤 Ejecutar carga de Base_Madre (CARGAR_MADRE.py)"):
        if confirmar_agente and agentes_seleccionados:
            with st.spinner(f"Ejecutando carga para agentes: {', '.join(agentes_seleccionados)}..."):
                try:
                    ejecutar_carga(agentes_seleccionados)
                    st.success(f"✅ Base_Madre actualizada con registros distribuidos entre: {', '.join(agentes_seleccionados)}.")
                except Exception as e:
                    st.error(f"❌ Error al ejecutar carga: {e}")
        else:
            st.warning("⚠️ Debes seleccionar al menos un agente y confirmar antes de continuar.")

    st.divider()

    st.markdown("### 📤 Subir Base seleccionada a hoja TOTAL (CRM)")

    bases_disponibles = subir_crm.obtener_bases_disponibles()
    if bases_disponibles:
        base_elegida = st.selectbox("Selecciona una base para subir a TOTAL:", bases_disponibles)
        if st.button("🚀 Subir base al CRM (TOTAL)"):
            with st.spinner(f"Subiendo base '{base_elegida}' a hoja TOTAL..."):
                resultado = subir_crm.subir_base_a_total(base_elegida)
            st.success(resultado)
    else:
        st.info("No hay bases pendientes por subir.")

    st.caption("💡 Recuerda verificar los datos en la hoja 'Base_Madre' y 'TOTAL' después de cada ejecución.")

def ejecutar_proceso_alimentar(google_ids_text, archivos_xlsx):
    ids_limpios = [x.strip() for x in google_ids_text.splitlines() if x.strip()]

    if archivos_xlsx:
        st.subheader("👀 Previsualización de archivos locales (.xlsx)")
        previews = Alimentar.cargar_archivos_locales(archivos_xlsx, preview=True)
        for nombre, df_preview in previews:
            st.markdown(f"**{nombre}**")
            st.dataframe(df_preview)

    if st.button("✅ Confirmar y procesar archivos"):
        with st.spinner("Procesando carga de bases (Alimentar)..."):
            resultados = Alimentar.procesar_entradas(sheets_ids=ids_limpios, archivos_locales=archivos_xlsx)
        st.success("✅ Proceso de carga (Alimentar) finalizado.")
        st.write("### Resultado por entrada:")
        for nombre, estado in resultados:
            st.write(f"- **{nombre}**: {estado}")
