import streamlit as st

st.set_page_config(page_title="Panel de Procesos", layout="centered")

# Módulos de la app
from modules import Gestiones_de_hoy, interfaz_inicio
from modules import panel_control
from modules import Reporte
from modules import reasignar_clientes
from modules import revisar_streamlit
from modules import Quitarbase  # <-- Nuevo módulo

# Funciones auxiliares
from scripts.reasignacion import contar_total_gestiones, iniciar_credenciales
from scripts.revisar import procesar_para_revision
from scripts.Appsheet import ejecutar_actualizacion  # Importamos la función directamente

def main():
    if "comenzar" not in st.session_state or not st.session_state.comenzar:
        interfaz_inicio.mostrar_inicio()
        return

    st.sidebar.title("Menú de Navegación")

    ejecutar_appsheet = st.sidebar.button("🔁 Ejecutar Appsheet.py")

    if ejecutar_appsheet:
        progreso = st.progress(0)
        with st.spinner("Ejecutando sincronización con Appsheet..."):
            def actualizar_progreso(valor):
                progreso.progress(valor)

            try:
                ejecutar_actualizacion(actualizar_progreso)
                st.success("✅ Sincronización completada correctamente.")
            except Exception as e:
                st.error(f"❌ Error al ejecutar Appsheet: {e}")

    # Menú lateral
    opcion = st.sidebar.selectbox(
        "Selecciona una opción",
        [
            "Panel de Control - Carga y Limpieza",
            "Informe de Gestiones",
            "Reporte por Fecha",
            "Reasignar Clientes",
            "Revisión de Clientes",
            "Quitar valores de la Base"  # <-- Nueva opción
        ]
    )

    if opcion == "Panel de Control - Carga y Limpieza":
        panel_control.mostrar_panel()
    elif opcion == "Informe de Gestiones":
        Gestiones_de_hoy.mostrar_informe()
    elif opcion == "Reporte por Fecha":
        Reporte.mostrar_reporte()
    elif opcion == "Reasignar Clientes":
        reasignar_clientes.mostrar_reasignacion()
    elif opcion == "Revisión de Clientes":
        revisar_streamlit.mostrar_revision()
    elif opcion == "Quitar valores de la Base":
        Quitarbase.mostrar_quitarbase()  # <-- Llamada al nuevo módulo

if __name__ == "__main__":
    main()
