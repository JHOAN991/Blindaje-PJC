import pandas as pd
import os
from datetime import datetime

LOGS_CSV = "data/logs_flujo.csv"

def registrar_log_subida(modo, archivos_cargados, ciclo_subido, registros_agregados=0, agente_excluido="", ids_sheets=""):
    """
    Guarda un registro de la subida en el archivo de logs.
    """
    log = pd.DataFrame([{
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Modo asignacion": modo,
        "Agente excluido": agente_excluido,
        "Archivos cargados": archivos_cargados,
        "IDs Google Sheets": ids_sheets,
        "Ciclo subido": ciclo_subido,
    }])

    print("🧾 Log generado desde utils:")
    print(log.to_string(index=False))

    if os.path.exists(LOGS_CSV):
        log.to_csv(LOGS_CSV, mode='a', header=False, index=False, line_terminator='\n')
    else:
        log.to_csv(LOGS_CSV, index=False, line_terminator='\n')

    print(f"📜 Log actualizado en {LOGS_CSV}")
