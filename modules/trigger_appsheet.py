import streamlit as st
import threading
import time
import subprocess
import sys
from pathlib import Path

# Tiempo (segundos) entre ejecuciones consecutivas de Appsheet.py
INTERVALO = 30           # ajusta a tu gusto

# Ruta absoluta (o relativa) al script que quieres ejecutar
RUTA_APPSHEET = Path(__file__).parent.parent / "scripts" / "Appsheet.py"


def _ejecutar_appsheet(stop_event: threading.Event):
    """
    Hilo en segundo plano que lanza Appsheet.py cada INTERVALO segundos.
    Se detiene cuando stop_event.is_set() es True.
    """
    while not stop_event.is_set():
        try:
            # Ejecuta el script como nuevo proceso Python
            subprocess.run([sys.executable, str(RUTA_APPSHEET)], check=True)
        except Exception as e:
            # Imprime en consola de Streamlit para depurar
            print(f"[Appsheet Trigger] Error al ejecutar: {e}")

        # Espera hasta INTERVALO o hasta que se pida detener
        stop_event.wait(INTERVALO)


def mostrar_trigger():
    """
    Muestra un interruptor ON/OFF en la barra lateral.
    Controla un hilo en segundo plano que ejecuta Appsheet.py
    """
    st.sidebar.markdown("### ⚙️ Ejecución automática de Appsheet")
    activado = st.sidebar.toggle("Activar loop de Appsheet", key="toggle_appsheet")

    # Inicializa llaves en session_state si no existen
    if "appsheet_hilo" not in st.session_state:
        st.session_state.appsheet_hilo = None
    if "appsheet_stop_event" not in st.session_state:
        st.session_state.appsheet_stop_event = threading.Event()

    # --------- 1. Si se acaba de activar ----------
    if activado and st.session_state.appsheet_hilo is None:
        stop_event = threading.Event()
        hilo = threading.Thread(
            target=_ejecutar_appsheet,
            args=(stop_event,),
            daemon=True,
            name="AppsheetLoop",
        )
        hilo.start()
        st.session_state.appsheet_hilo = hilo
        st.session_state.appsheet_stop_event = stop_event
        st.sidebar.success("Loop de Appsheet **iniciado** ✅")

    # --------- 2. Si se acaba de desactivar ----------
    elif not activado and st.session_state.appsheet_hilo is not None:
        st.session_state.appsheet_stop_event.set()  # indica al hilo que pare
        st.session_state.appsheet_hilo = None
        st.sidebar.info("Loop de Appsheet detenido ✋")
