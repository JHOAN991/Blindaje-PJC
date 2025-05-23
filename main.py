import subprocess
import streamlit as st

st.set_page_config(page_title="Panel de Procesos", layout="centered")

from modules import Gestiones_de_hoy, interfaz_inicio
from modules import panel_control
from modules import Reporte
from modules import reasignar_clientes
from modules import revisar_streamlit

from scripts.reasignacion import contar_total_gestiones, iniciar_credenciales
from scripts.revisar import procesar_para_revision

def main():
    if "comenzar" not in st.session_state or not st.session_state.comenzar:
        interfaz_inicio.mostrar_inicio()
        return

    st.sidebar.title("Menú de Navegación")

    ejecutar_appsheet = st.sidebar.button("🔁 Ejecutar Appsheet.py")

    if ejecutar_appsheet:
        st.sidebar.info("Ejecutando Appsheet.py...")
        resultado = subprocess.run(["python", "scripts/Appsheet.py"], capture_output=True, text=True)
        st.sidebar.text_area("Salida del script:", resultado.stdout + "\n" + resultado.stderr, height=300)

    # Menú lateral
    opcion = st.sidebar.selectbox(
        "Selecciona una opción",
        [
            "Panel de Control - Carga y Limpieza",
            "Informe de Gestiones",
            "Reporte por Fecha",
            "Reasignar Clientes",
            "Revisión de Clientes"
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

if __name__ == "__main__":
    main()
