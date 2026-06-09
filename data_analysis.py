import os
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import pymannkendall as mk

# Configuración de rutas relativas al script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')
PLOTS_DIR = os.path.join(SCRIPT_DIR, 'plots')

# Configuración de estilos visuales
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'figure.titlesize': 16
})

def load_data():
    csv_path = os.path.join(DATA_DIR, 'neiva_clima_mensual.csv')
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"No se encontró el archivo de datos mensuales en {csv_path}. Ejecuta primero data_extraction.py")
    
    df_monthly = pd.read_csv(csv_path)
    df_monthly['fecha'] = pd.to_datetime(df_monthly['año'].astype(str) + '-' + df_monthly['mes'].astype(str) + '-01')
    return df_monthly

def calculate_spi(df, scale=3):
    """
    Calcula el Índice de Precipitación Estandarizado (SPI) para una escala temporal dada.
    """
    print(f"Calculando SPI-{scale}...")
    
    # 1. Calcular suma móvil de precipitación
    df = df.sort_values('fecha').copy()
    df[f'prcp_{scale}m'] = df['prcp_sum'].rolling(window=scale).sum()
    
    # Eliminar filas iniciales que no tienen suficiente historial para el rolling
    df = df.dropna(subset=[f'prcp_{scale}m']).copy()
    
    spi_values = np.zeros(len(df))
    
    # 2. Calcular SPI ajustando una distribución Gamma mes a mes (estacionalidad)
    for mes in range(1, 13):
        indices_mes = df['mes'] == mes
        sub_df = df[indices_mes]
        
        if len(sub_df) < 10: # Se requieren suficientes datos históricos por mes
            continue
            
        x = sub_df[f'prcp_{scale}m'].values
        
        # Probabilidad de cero lluvia (q)
        zeros = x == 0
        m = np.sum(zeros)
        N = len(x)
        q = m / N
        
        # Filtrar valores mayores a cero para ajustar la Gamma
        non_zeros = x > 0
        x_no_zeros = x[non_zeros]
        
        if len(x_no_zeros) > 4:
            # Ajustar la distribución Gamma
            # floc=0 fija el parámetro de localización en 0, que es lo correcto para lluvia
            shape, loc, scale_param = stats.gamma.fit(x_no_zeros, floc=0)
            
            # Cumulative Distribution Function (CDF) de la Gamma para valores > 0
            cdf = stats.gamma.cdf(x, shape, loc=loc, scale=scale_param)
        else:
            # Si hay demasiados ceros o muy pocos datos, aproximar con promedio
            cdf = np.zeros(len(x))
            
        # Combinar probabilidad de cero y no-cero
        h = q + (1 - q) * cdf
        
        # Limitar valores extremos para evitar infinitos en la inversa de la Normal
        h = np.clip(h, 0.00001, 0.99999)
        
        # Transformación a una distribución normal estándar Z (SPI)
        z = stats.norm.ppf(h)
        
        # Asignar de vuelta al array de resultados
        spi_values[indices_mes] = z
        
    df[f'spi_{scale}'] = spi_values
    return df

def analyze_trends(df_monthly):
    print("\n=== ANÁLISIS DE TENDENCIAS (Prueba de Mann-Kendall) ===")
    
    # Agrupar datos anualmente para analizar tendencias a largo plazo
    df_annual = df_monthly.groupby('año').agg(
        tavg=('tavg_mean', 'mean'),
        tmax=('tmax_mean', 'mean'),
        tmin=('tmin_mean', 'mean'),
        prcp=('prcp_sum', 'sum')
    ).reset_index()
    
    # Excluir el año actual incompleto si aplica
    current_year = datetime.now().year
    df_annual = df_annual[df_annual['año'] < current_year]
    
    variables = {
        'tavg': 'Temperatura Media Anual (°C)',
        'tmax': 'Temperatura Máxima Anual (°C)',
        'tmin': 'Temperatura Mínima Anual (°C)',
        'prcp': 'Precipitación Total Anual (mm)'
    }
    
    results = {}
    for var, name in variables.items():
        # Mann-Kendall Test
        res = mk.original_test(df_annual[var])
        
        # Regresión lineal simple para obtener la pendiente (tasa de cambio por año)
        slope, intercept, r_value, p_value, std_err = stats.linregress(df_annual['año'], df_annual[var])
        
        results[var] = {
            'trend': res.trend,
            'p_value_mk': res.p,
            'slope_mk': res.slope,
            'slope_lr': slope,
            'change_10y': slope * 10
        }
        
        print(f"\n* Variable: {name}")
        print(f"  - Tendencia detectada (Mann-Kendall): {res.trend} (p-value: {res.p:.4f})")
        print(f"  - Pendiente del test: {res.slope:.4f} unidades/año")
        print(f"  - Tasa de cambio (Regresión): {slope:.4f} unidades/año ({slope * 10:.3f} por década)")
        
    return df_annual, results

def plot_temperature_trends(df_annual, results):
    plt.figure(figsize=(10, 6))
    
    # Graficar Temperatura Media y sus extremos
    plt.plot(df_annual['año'], df_annual['tavg'], marker='o', label='Temp. Media', color='#e74c3c', linewidth=2)
    plt.plot(df_annual['año'], df_annual['tmax'], marker='s', label='Temp. Máxima', color='#c0392b', alpha=0.5, linestyle='--')
    plt.plot(df_annual['año'], df_annual['tmin'], marker='^', label='Temp. Mínima', color='#e67e22', alpha=0.5, linestyle='--')
    
    # Línea de tendencia para Temp Media
    slope = results['tavg']['slope_lr']
    intercept = stats.linregress(df_annual['año'], df_annual['tavg'])[1]
    trend_line = slope * df_annual['año'] + intercept
    plt.plot(df_annual['año'], trend_line, color='black', linestyle=':', label=f'Tendencia ({slope*10:.2f}°C/década)')
    
    plt.title('Tendencia de Temperatura en Neiva (1990 - 2025)\nEvidencia de Calentamiento Local')
    plt.xlabel('Año')
    plt.ylabel('Temperatura (°C)')
    plt.legend(frameon=True)
    plt.tight_layout()
    
    os.makedirs(PLOTS_DIR, exist_ok=True)
    plot_path = os.path.join(PLOTS_DIR, 'temperatura_tendencia.png')
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Guardado: {plot_path}")

def plot_precipitation_seasonality(df_monthly):
    plt.figure(figsize=(10, 6))
    
    # Boxplot mensual de lluvias para ilustrar el patrón bimodal
    sns.boxplot(x='mes', y='prcp_sum', data=df_monthly, palette='Blues')
    
    # Añadir promedios mensuales como puntos rojos
    monthly_means = df_monthly.groupby('mes')['prcp_sum'].mean().reset_index()
    plt.scatter(monthly_means['mes'] - 1, monthly_means['prcp_sum'], color='red', marker='D', s=40, zorder=3, label='Promedio Histórico')
    
    plt.title('Distribución Mensual de Precipitación en Neiva\nIdentificación del Régimen Lluvia/Sequía (Patrón Bimodal)')
    plt.xlabel('Mes del Año')
    plt.ylabel('Precipitación Acumulada (mm/mes)')
    plt.xticks(ticks=range(12), labels=['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'])
    plt.legend()
    plt.tight_layout()
    os.makedirs(PLOTS_DIR, exist_ok=True)
    plot_path = os.path.join(PLOTS_DIR, 'precipitacion_estacionalidad.png')
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Guardado: {plot_path}")

def plot_spi_droughts(df_spi):
    plt.figure(figsize=(12, 6))
    
    # Filtrar últimos 15 años para mejor visualización de sequías recientes
    df_recent = df_spi[df_spi['año'] >= 2010].copy()
    
    # Definir colores para húmedo (azul) y seco (rojo)
    colors = ['#e74c3c' if x < 0 else '#3498db' for x in df_recent['spi_3']]
    
    plt.bar(df_recent['fecha'], df_recent['spi_3'], width=25, color=colors, edgecolor='none', alpha=0.85)
    
    # Líneas de umbral para sequía moderada/extrema
    plt.axhline(0, color='gray', linestyle='-', linewidth=0.8)
    plt.axhline(-1, color='#e67e22', linestyle='--', linewidth=1, label='Sequía Moderada (SPI = -1.0)')
    plt.axhline(-1.5, color='#c0392b', linestyle='-.', linewidth=1, label='Sequía Extrema (SPI = -1.5)')
    
    plt.title('Índice de Precipitación Estandarizado a 3 Meses (SPI-3) en Neiva (2010 - 2026)\nMonitoreo de Sequías Agrícolas')
    plt.xlabel('Año')
    plt.ylabel('Valor SPI-3')
    plt.legend(loc='lower left', frameon=True)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    os.makedirs(PLOTS_DIR, exist_ok=True)
    plot_path = os.path.join(PLOTS_DIR, 'spi_sequias.png')
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Guardado: {plot_path}")

def generate_agricultural_insights(df_monthly, df_spi):
    print("\n=== INSIGHTS Y ANÁLISIS DE RIEGO PARA PORTAFOLIO ===")
    
    # 1. Calendario de Déficit Hídrico Estructural (Promedios Mensuales)
    cal_clima = df_monthly.groupby('mes').agg(
        lluvia_prom=('prcp_sum', 'mean'),
        temp_max_prom=('tmax_mean', 'mean'),
        viento_prom=('wspd_mean', 'mean')
    ).reset_index()
    
    # La evapotranspiración (demanda de agua del cultivo/suelo) es proporcional a la Temp Max y Viento.
    # Los meses más críticos son los de alta temp/viento y baja lluvia.
    print("\n1. Calendario Histórico Climatológico de Neiva:")
    print(cal_clima.to_string(index=False, formatters={
        'lluvia_prom': '{:.1f} mm'.format,
        'temp_max_prom': '{:.1f} °C'.format,
        'viento_prom': '{:.1f} km/h'.format
    }))
    
    # Meses críticos de sequía estacional (Julio-Agosto y Enero-Febrero)
    # Meses lluviosos (Marzo-Mayo y Octubre-Noviembre)
    
    # 2. Análisis del Fenómeno de El Niño
    # Identificar sequías extremas recientes en Neiva (donde SPI-3 < -1.5)
    droughts_ext = df_spi[df_spi['spi_3'] <= -1.5][['año', 'mes', 'spi_3', 'prcp_sum']].copy()
    print(f"\n2. Registro Histórico de Sequías Extremas o Severas (SPI-3 <= -1.5) desde 1990:")
    print(droughts_ext.sort_values('spi_3').head(10).to_string(index=False))
    
    # Guardar datos finales con SPI para uso en Power BI
    final_csv_path = os.path.join(DATA_DIR, 'neiva_clima_analisis_final.csv')
    df_spi.to_csv(final_csv_path, index=False)
    print(f"\nDataset enriquecido guardado para Power BI: {final_csv_path}")

def main():
    try:
        df_monthly = load_data()
        
        # 1. Calcular el SPI a 3 meses (mejor indicador para sequías agrícolas de corto plazo)
        df_spi = calculate_spi(df_monthly, scale=3)
        
        # 2. Análisis de tendencias a largo plazo
        df_annual, trend_results = analyze_trends(df_monthly)
        
        # 3. Graficar tendencias de temperatura
        plot_temperature_trends(df_annual, trend_results)
        
        # 4. Graficar la estacionalidad (patrón bimodal)
        plot_precipitation_seasonality(df_monthly)
        
        # 5. Graficar la evolución de sequías (SPI)
        plot_spi_droughts(df_spi)
        
        # 6. Generar conclusiones de negocio/riego
        generate_agricultural_insights(df_monthly, df_spi)
        
    except Exception as e:
        print(f"Error durante el análisis: {e}")

if __name__ == "__main__":
    main()
