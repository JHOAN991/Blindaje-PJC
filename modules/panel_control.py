import streamlit as st
import pandas as pd
from scripts import Alimentar, CARGAR_MADRE
from gspread_dataframe import get_as_dataframe

# Configuración de agentes
AGENTES_DISPONIBLES = [
    "Michell Escobar", "Luris Henriquez", "Nadeshka Castillo", 
    "Alejandro Bonilla", "Julian Ramirez", "Emily Medina",
    "Jhoan Medina", "Rosmery Umanzor", "John Florian", 
    "Sugeidys Batista", "Darineth Diaz", "Edivinia Duarte",
    "Veronica Zuñiga"
]

def mostrar_panel():
    """Función principal que muestra el panel de control completo"""
    st.set_page_config(layout="wide")
    st.title("📊 Panel de Control - Gestión de Bases CRM")
    
    # Mostrar estado de bases
    mostrar_estado_bases()
    st.divider()
    
    # Sección de carga de datos
    mostrar_seccion_alimentar()
    st.divider()
    
    # Sección de asignación de agentes
    agentes_seleccionados = mostrar_seccion_agentes()
    st.divider()
    
    # Sección de carga a Base Madre
    mostrar_seccion_cargar_madre(agentes_seleccionados)
    st.divider()
    
    # Sección de subida a CRM
    mostrar_seccion_CARGAR_MADRE()

def mostrar_estado_bases():
    """Muestra el estado de las bases"""
    st.markdown("### 🔍 Estado Actual de Bases")
    
    try:
        # Obtener bases existentes en Base_Madre
        bases_madre = CARGAR_MADRE.obtener_bases_existentes()
        
        # Obtener hojas en el documento de destino
        hojas_destino = CARGAR_MADRE.obtener_hojas_destino()
        
        # Calcular bases faltantes
        bases_faltantes = list(set(hojas_destino) - set(bases_madre))
        
        if bases_faltantes:
            st.warning(f"⚠️ Hay {len(bases_faltantes)} bases pendientes por cargar a Base_Madre:")
            for base in bases_faltantes:
                st.write(f"- {base}")
        else:
            st.success("✅ Todas las bases están actualizadas en Base_Madre")
            
    except Exception as e:
        st.error(f"Error al verificar estado de bases: {str(e)}")

def mostrar_seccion_alimentar():
    """Muestra la sección para cargar nuevos datos"""
    st.markdown("### 🔄 Cargar Nuevos Datos")
    
    with st.expander("📤 Opciones de Carga", expanded=True):
        google_ids_text = st.text_area("IDs de Google Sheets (uno por línea)", height=100)
        archivos_xlsx = st.file_uploader("Subir archivos Excel/CSV", type=["xlsx", "csv"], accept_multiple_files=True)

        if st.button("✅ Procesar Datos"):
            procesar_datos(google_ids_text, archivos_xlsx)

def procesar_datos(google_ids_text, archivos_xlsx):
    """Procesa los datos ingresados"""
    ids_limpios = [x.strip() for x in google_ids_text.splitlines() if x.strip()]
    
    if not ids_limpios and not archivos_xlsx:
        st.warning("⚠️ No hay datos para procesar")
        return
    
    with st.spinner("Procesando datos..."):
        # Mostrar previsualización
        if archivos_xlsx:
            st.subheader("👀 Vista Previa de Archivos")
            for archivo in archivos_xlsx:
                try:
                    df = pd.read_csv(archivo) if archivo.name.endswith('.csv') else pd.read_excel(archivo)
                    with st.expander(f"📄 {archivo.name} - {len(df)} registros"):
                        st.dataframe(df.head(3))
                except Exception as e:
                    st.error(f"Error al leer {archivo.name}: {str(e)}")
        
        # Procesar todos los datos
        resultados = Alimentar.procesar_entradas(
            sheets_ids=ids_limpios,
            archivos_locales=archivos_xlsx
        )
        
        # Mostrar resultados
        st.success("✅ Proceso completado")
        for nombre, estado in resultados:
            st.write(f"- {nombre}: {estado}")

def mostrar_seccion_agentes():
    """Muestra la sección de selección de agentes"""
    st.markdown("### 👥 Asignación de Agentes")
    
    seleccion = st.multiselect(
        "Seleccionar agentes:",
        options=["Todos"] + AGENTES_DISPONIBLES,
        default=[]
    )

    if "Todos" in seleccion:
        agentes_seleccionados = AGENTES_DISPONIBLES
    else:
        agentes_seleccionados = seleccion
        
    st.info(f"Agentes seleccionados: {', '.join(agentes_seleccionados) if agentes_seleccionados else 'Ninguno'}")
    
    return agentes_seleccionados

def mostrar_seccion_cargar_madre(agentes_seleccionados):
    """Muestra la sección para cargar datos a Base Madre"""
    st.markdown("### 🏗️ Cargar a Base Madre")
    
    try:
        # Obtener bases existentes y hojas destino
        bases_madre = CARGAR_MADRE.obtener_bases_existentes()
        hojas_destino = CARGAR_MADRE.obtener_hojas_destino()
        bases_faltantes = list(set(hojas_destino) - set(bases_madre))
        
        if bases_faltantes:
            base_seleccionada = st.selectbox(
                "Seleccionar base para cargar:",
                options=bases_faltantes
            )
            
            confirmar = st.checkbox("Confirmar asignación de agentes")
            
            if st.button("🚀 Cargar a Base Madre"):
                if not confirmar:
                    st.warning("Debes confirmar la asignación de agentes")
                    return
                    
                if not agentes_seleccionados:
                    st.warning("Debes seleccionar al menos un agente")
                    return
                    
                with st.spinner(f"Cargando {base_seleccionada} a Base Madre..."):
                    success, mensaje = CARGAR_MADRE.cargar_base_a_madre(base_seleccionada)
                    
                    if success:
                        st.success(mensaje)
                        st.balloons()
                    else:
                        st.error(mensaje)
        else:
            st.info("No hay bases pendientes por cargar a Base Madre")
            
    except Exception as e:
        st.error(f"Error al cargar bases: {str(e)}")

def mostrar_seccion_CARGAR_MADRE():
    """Muestra la sección para subir datos al CRM"""
    st.markdown("### 📤 Subir a CRM (TOTAL)")
    
    try:
        # Obtener bases no subidas (donde Subida != "SI")
        sheet = CARGAR_MADRE.CLIENT.open_by_key(CARGAR_MADRE.BASE_MADRE_ID).worksheet("Base_Madre")
        df = get_as_dataframe(sheet).fillna("")
        bases_disponibles = df[df["Subida"].str.upper() != "Si"]["Base"].unique().tolist()
        
        if bases_disponibles:
            base_seleccionada = st.selectbox(
                "Seleccionar base para subir al CRM:",
                options=bases_disponibles
            )
            
            if st.button("🔼 Subir a TOTAL"):
                with st.spinner(f"Subiendo {base_seleccionada} al CRM..."):
                    success, mensaje = CARGAR_MADRE.subir_base_a_total(base_seleccionada)
                    
                    if success:
                        st.success(mensaje)
                    else:
                        st.error(mensaje)
        else:
            st.info("No hay bases pendientes por subir al CRM")
            
    except Exception as e:
        st.error(f"Error al subir al CRM: {str(e)}")

if __name__ == "__main__":
    mostrar_panel()