import streamlit as st

def mostrar_inicio():
    if "comenzar" not in st.session_state:
        st.session_state.comenzar = False

    query_params = st.query_params
    if "comenzar" in query_params and not st.session_state.comenzar:
        st.session_state.comenzar = True
        st.rerun()
  # <- redirige para cargar el panel

    if not st.session_state.comenzar:
        st.markdown("""
        <style>
        .centered-container {
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            align-items: center;
            height: auto;
            padding-top: 100px;
            text-align: center;
        }
        .big-title {
            font-size: 60px;
            font-weight: bold;
            color: #4B8BBE;
            margin-bottom: 10px;
        }
        .subtitle {
            font-size: 25px;
            color: #bbb;
            margin-bottom: 40px;
        }
        .custom-button {
            font-size: 20px;
            padding: 12px 40px;
            background-color: #262730;
            color: white;
            border: 2px solid #4B8BBE;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-left: 50px;
        }
        .custom-button:hover {
            background-color: #4B8BBE;
            color: black;
        }
        </style>

        <div class="centered-container">
            <div class="big-title">👋 Bienvenida, Dary</div>
            <div class="subtitle">Este es tu panel para gestionar la carga y limpieza de datos.</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style='display: flex; justify-content: center;'>
            <form action="" method="get">
                <input type="hidden" name="comenzar" value="1">
                <button class="custom-button" type="submit">Comenzar</button>
            </form>
        </div>
        """, unsafe_allow_html=True)
        st.stop()
