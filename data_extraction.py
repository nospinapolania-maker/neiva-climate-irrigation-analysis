import os
from datetime import datetime
import pandas as pd
import numpy as np
from meteostat import daily, config

def extract_and_clean_data():
    print("=== Iniciando Extracción de Datos Climatológicos para Neiva ===")
    config.block_large_requests = False
    
    # 1. Definición de parámetros
    # Estación Aeropuerto Benito Salas (Neiva, Huila) -> WMO: 80315
    station_id = "80315"
    start_date = datetime(1990, 1, 1)
    end_date = datetime(2026, 5, 31)
    
    print(f"Estación: Aeropuerto Benito Salas (WMO: {station_id})")
    print(f"Periodo: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
    
    # 2. Descarga de datos diarios usando Meteostat
    try:
        data = daily(station_id, start_date, end_date)
        df = data.fetch()
    except Exception as e:
        print(f"Error al descargar datos de Meteostat: {e}")
        return
    
    if df.empty:
        print("Error: El conjunto de datos retornado está vacío. Verifica la conexión o el ID de la estación.")
        return
        
    print(f"Datos descargados con éxito. Registros iniciales: {len(df)}")
    
    # 3. Limpieza de datos y Reindexación Completa
    # El dataframe ya tiene un DatetimeIndex (llamado 'time') por defecto.
    
    # Crear un índice diario completo desde start_date hasta end_date para rellenar días faltantes
    full_index = pd.date_range(start=start_date, end=end_date, freq='D')
    df = df.reindex(full_index)
    df.index.name = 'fecha'
    df = df.reset_index()
    
    # Renombrar 'temp' a 'tavg'
    df = df.rename(columns={'temp': 'tavg'})
    
    # Seleccionar las columnas relevantes
    columns_to_keep = ['fecha', 'tavg', 'tmin', 'tmax', 'prcp', 'wspd', 'pres']
    df = df[columns_to_keep]
    
    # Inspección de valores nulos antes de la limpieza
    print("\n--- Conteo de Valores Faltantes (Nulos) Antes de Limpieza ---")
    print(df.isnull().sum())
    
    # A. Tratamiento de Precipitación (prcp)
    df['prcp'] = df['prcp'].fillna(0.0)
    
    # B. Tratamiento de otras variables mediante interpolación y medias mensuales históricas
    df['mes'] = df['fecha'].dt.month
    
    variables_to_clean = ['tavg', 'tmin', 'tmax', 'wspd', 'pres']
    for col in variables_to_clean:
        # 1. Interpolación lineal para brechas cortas (máximo 7 días)
        df[col] = df[col].interpolate(method='linear', limit=7)
        # 2. Imputación con la media climatológica histórica del mes para brechas largas
        monthly_means = df.groupby('mes')[col].transform('mean')
        df[col] = df[col].fillna(monthly_means)
        
    # Eliminar columna auxiliar de mes
    df = df.drop(columns=['mes'])
    
    print("\n--- Conteo de Valores Faltantes Después de Limpieza ---")
    print(df.isnull().sum())
    
    # 4. Creación de agregaciones mensuales (útil para análisis de tendencias y Power BI)
    df['año'] = df['fecha'].dt.year
    df['mes'] = df['fecha'].dt.month
    df['año_mes'] = df['fecha'].dt.to_period('M')
    
    df_monthly = df.groupby(['año', 'mes']).agg(
        tavg_mean=('tavg', 'mean'),
        tmin_mean=('tmin', 'mean'),
        tmax_mean=('tmax', 'mean'),
        prcp_sum=('prcp', 'sum'),
        wspd_mean=('wspd', 'mean'),
        pres_mean=('pres', 'mean'),
        dias_lluvia=('prcp', lambda x: (x > 0.1).sum()), # Días con lluvia relevante
        dias_registro=('fecha', 'count')
    ).reset_index()
    
    # Asegurar que solo consideramos meses completos
    df_monthly = df_monthly[df_monthly['dias_registro'] >= 28].copy()
    
    # 5. Guardar archivos resultantes
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    daily_path = os.path.join(data_dir, 'neiva_clima_diario.csv')
    monthly_path = os.path.join(data_dir, 'neiva_clima_mensual.csv')
    
    df.to_csv(daily_path, index=False)
    df_monthly.to_csv(monthly_path, index=False)
    
    print(f"\nProceso finalizado con éxito.")
    print(f"-> Datos diarios guardados en: {daily_path} ({len(df)} registros)")
    print(f"-> Datos mensuales guardados en: {monthly_path} ({len(df_monthly)} registros)")

if __name__ == "__main__":
    extract_and_clean_data()
