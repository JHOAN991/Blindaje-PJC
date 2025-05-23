import streamlit as st
import pandas as pd
from scripts.revisar import procesar_para_revision

def mostrar_revision():
    st.title("📋 Revisión de clientes")

    if st.button("🔄 Procesar revisión ahora"):
        df_alerta, df_rev_vacio = procesar_para_revision()

        # ------- A. Alertas 'Sin ajustes' -------
        if not df_alerta.empty:
            st.warning("⚠️ Registros con Gestión = 'Sin ajustes':")
            st.dataframe(df_alerta, use_container_width=True)
        else:
            st.success("✅ Sin registros con 'Sin ajustes'.")

        # ------- B. Métrica total de vacíos -------
        cantidad_vacios = len(df_rev_vacio)
        st.metric("Clientes sin Estado de Gestión", cantidad_vacios)

        if cantidad_vacios > 0:
            resumen = (
                df_rev_vacio.groupby("Base")
                .size()
                .reset_index(name="Faltantes")
                .sort_values("Faltantes", ascending=False)
            )

            # ------- C. Métricas individuales por Base -------
            st.subheader("📊 Detalle por Base")
            cols = st.columns(min(4, len(resumen)))  # Máximo 4 por fila
            for i, row in resumen.iterrows():
                with cols[i % len(cols)]:
                    st.metric(label=f"Base: {row['Base']}", value=row["Faltantes"])

            # ------- D. Gráfica de barras -------
            st.bar_chart(data=resumen.set_index("Base")["Faltantes"])

            # ------- E. Tabla detallada -------
            st.info(
                f"🔎 Filas en REVICION sin 'Estado de Gestion' "
                f"(total: {cantidad_vacios}):"
            )
            st.dataframe(resumen, use_container_width=True)

            with st.expander("🧾 Ver detalle de registros faltantes"):
                st.dataframe(df_rev_vacio, use_container_width=True)
        else:
            st.success("✅ Todas las filas de REVICION tienen 'Estado de Gestion'.")
    else:
        st.info("Presiona el botón para ejecutar el proceso de revisión.")
