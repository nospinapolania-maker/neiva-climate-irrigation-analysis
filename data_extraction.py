import os
from datetime import datetime
import pandas as pd
from meteostat import daily, config


def extraer_y_limpiar_datos():
    print("=== Iniciando extraccion de datos climatologicos para Neiva ===")
    config.block_large_requests = False

    # 1. Definicion de parametros.
    # Estacion Aeropuerto Benito Salas (Neiva, Huila) -> WMO: 80315.
    station_id = "80315"
    start_date = datetime(1990, 1, 1)
    end_date = datetime(2026, 5, 31)

    print(f"Estacion: Aeropuerto Benito Salas (WMO: {station_id})")
    print(f"Periodo: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")

    # 2. Descarga de datos diarios con Meteostat.
    try:
        data = daily(station_id, start_date, end_date)
        df = data.fetch()
    except Exception as error:
        print(f"Error al descargar datos de Meteostat: {error}")
        return

    if df.empty:
        print("Error: el conjunto de datos esta vacio. Verifica la conexion o el ID de la estacion.")
        return

    print(f"Datos descargados con exito. Registros iniciales: {len(df)}")

    # 3. Limpieza de datos y reindexacion completa.
    # Meteostat entrega un indice de fechas llamado time.
    indice_diario = pd.date_range(start=start_date, end=end_date, freq="D")
    df = df.reindex(indice_diario)
    df.index.name = "fecha"
    df = df.reset_index()

    # Renombrar temp a tavg para mantener nombres climaticos consistentes.
    df = df.rename(columns={"temp": "tavg"})

    columnas_a_conservar = ["fecha", "tavg", "tmin", "tmax", "prcp", "wspd", "pres"]
    df = df[columnas_a_conservar]

    print("\n--- Conteo de valores faltantes antes de la limpieza ---")
    print(df.isnull().sum())

    # A. Tratamiento de precipitacion: si falta el dato, se asume 0.0 mm.
    df["prcp"] = df["prcp"].fillna(0.0)

    # B. Tratamiento de temperatura, viento y presion con interpolacion y medias mensuales.
    df["mes"] = df["fecha"].dt.month

    variables_a_limpiar = ["tavg", "tmin", "tmax", "wspd", "pres"]
    for columna in variables_a_limpiar:
        # Interpolacion lineal para brechas cortas de maximo 7 dias.
        df[columna] = df[columna].interpolate(method="linear", limit=7)

        # Imputacion con media climatologica mensual para brechas mas largas.
        medias_mensuales = df.groupby("mes")[columna].transform("mean")
        df[columna] = df[columna].fillna(medias_mensuales)

    df = df.drop(columns=["mes"])

    print("\n--- Conteo de valores faltantes despues de la limpieza ---")
    print(df.isnull().sum())

    # 4. Creacion de agregaciones mensuales para analisis y Power BI.
    df["año"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month
    df["año_mes"] = df["fecha"].dt.to_period("M")

    df_mensual = df.groupby(["año", "mes"]).agg(
        tavg_mean=("tavg", "mean"),
        tmin_mean=("tmin", "mean"),
        tmax_mean=("tmax", "mean"),
        prcp_sum=("prcp", "sum"),
        wspd_mean=("wspd", "mean"),
        pres_mean=("pres", "mean"),
        dias_lluvia=("prcp", lambda x: (x > 0.1).sum()),
        dias_registro=("fecha", "count")
    ).reset_index()

    # Conservar solo meses completos o casi completos.
    df_mensual = df_mensual[df_mensual["dias_registro"] >= 28].copy()

    # 5. Guardar archivos resultantes.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    ruta_diaria = os.path.join(data_dir, "neiva_clima_diario.csv")
    ruta_mensual = os.path.join(data_dir, "neiva_clima_mensual.csv")

    df.to_csv(ruta_diaria, index=False)
    df_mensual.to_csv(ruta_mensual, index=False)

    print("\nProceso finalizado con exito.")
    print(f"-> Datos diarios guardados en: {ruta_diaria} ({len(df)} registros)")
    print(f"-> Datos mensuales guardados en: {ruta_mensual} ({len(df_mensual)} registros)")


if __name__ == "__main__":
    extraer_y_limpiar_datos()
