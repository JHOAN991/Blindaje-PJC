import streamlit as st
from datetime import date
from scripts.Generar_reporte import generar_reporte_por_rango

def mostrar_reporte():
    st.title("📊 Generador de Reporte por Fecha")
    st.markdown(
        "Filtra los registros por fecha en **Base_Madre**, actualiza las hojas "
        "correspondientes y genera archivos Excel descargables."
    )

    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("Fecha de inicio", value=date.today())
    with col2:
        fecha_fin = st.date_input("Fecha de fin", value=date.today())

    st.markdown("---")

    if st.button("🚀 Generar reporte"):
        with st.spinner("Procesando datos..."):
            resumen, archivos = generar_reporte_por_rango(fecha_inicio, fecha_fin)

        st.success("✅ Reporte generado correctamente.")

        st.markdown("### 📌 Resumen de procesamiento por hoja destino")
        for item in resumen:
            base = item.get("base", "N/A")
            estado = item.get("estado", "desconocido")

            if "error" in item:
                st.markdown(f"🔴 **{base}**: error – `{item['error']}`")
            else:
                st.markdown(f"🟢 **{base}**: {estado}")

        st.markdown("---")
        st.markdown("### 📥 Descarga los archivos generados")

        for nombre_archivo, archivo_excel in archivos:
            st.download_button(
                label=f"Descargar {nombre_archivo}",
                data=archivo_excel,
                file_name=nombre_archivo,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
