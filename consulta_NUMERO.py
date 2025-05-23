import pandas as pd

# Cargar el archivo fusionado
df = pd.read_csv("data/origen.csv", dtype=str).fillna("")

# Lista de números a buscar
numeros_a_buscar = [
    "64902444.0", "66019076.0", "68566959.0", "68984701.0", "69739107.0", 
    "66376997.0", "66478812.0"
]

# Columnas donde se hará la búsqueda
columnas_objetivo = ["Numero 1", "Numero 2", "Numero 3", "Numero 4"]

# Lista para guardar coincidencias
coincidencias = []

# Buscar coincidencias por cada número en cada columna
for numero in numeros_a_buscar:
    for col in columnas_objetivo:
        coincidencias_en_columna = df[df[col] == numero]
        for _, fila in coincidencias_en_columna.iterrows():
            coincidencias.append({
                "Número encontrado": numero,
                "Columna": col,
                "Agente": fila.get("Agente", "No disponible")
            })

# Mostrar resultados
if coincidencias:
    print("\n📄 Números encontrados y sus respectivos Agente:\n")
    resultados_df = pd.DataFrame(coincidencias)
    print(resultados_df.to_string(index=False))
else:
    print("\n🔎 No se encontraron coincidencias con esos números.")
