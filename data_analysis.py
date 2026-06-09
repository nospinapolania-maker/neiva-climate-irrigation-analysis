import os
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import pymannkendall as mk

# Configuracion de rutas relativas al script.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
PLOTS_DIR = os.path.join(SCRIPT_DIR, "plots")

# Configuracion de estilos visuales.
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 14,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.titlesize": 16
})


def cargar_datos():
    csv_path = os.path.join(DATA_DIR, "neiva_clima_mensual.csv")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"No se encontro el archivo de datos mensuales en {csv_path}. "
            "Ejecuta primero data_extraction.py"
        )

    df_mensual = pd.read_csv(csv_path)
    df_mensual["fecha"] = pd.to_datetime(
        df_mensual["año"].astype(str) + "-" + df_mensual["mes"].astype(str) + "-01"
    )
    return df_mensual


def calcular_spi(df, escala=3):
    """
    Calcula el Indice de Precipitacion Estandarizado (SPI) para una escala temporal.
    """
    print(f"Calculando SPI-{escala}...")

    # 1. Calcular suma movil de precipitacion.
    df = df.sort_values("fecha").copy()
    df[f"prcp_{escala}m"] = df["prcp_sum"].rolling(window=escala).sum()

    # Eliminar filas iniciales sin suficiente historial para la ventana movil.
    df = df.dropna(subset=[f"prcp_{escala}m"]).copy()

    valores_spi = np.zeros(len(df))

    # 2. Calcular SPI ajustando una distribucion Gamma mes a mes.
    for mes in range(1, 13):
        indices_mes = df["mes"] == mes
        sub_df = df[indices_mes]

        if len(sub_df) < 10:
            continue

        x = sub_df[f"prcp_{escala}m"].values

        # Probabilidad de cero lluvia.
        ceros = x == 0
        m = np.sum(ceros)
        n = len(x)
        q = m / n

        # Filtrar valores mayores a cero para ajustar la distribucion Gamma.
        no_ceros = x > 0
        x_no_ceros = x[no_ceros]

        if len(x_no_ceros) > 4:
            # floc=0 fija el parametro de localizacion en 0, adecuado para lluvia.
            shape, loc, scale_param = stats.gamma.fit(x_no_ceros, floc=0)

            # Funcion de distribucion acumulada de la Gamma para valores mayores a cero.
            cdf = stats.gamma.cdf(x, shape, loc=loc, scale=scale_param)
        else:
            # Si hay demasiados ceros o pocos datos, se aproxima con ceros.
            cdf = np.zeros(len(x))

        # Combinar probabilidad de cero y no cero.
        h = q + (1 - q) * cdf

        # Limitar valores extremos para evitar infinitos en la inversa normal.
        h = np.clip(h, 0.00001, 0.99999)

        # Transformar a una distribucion normal estandar Z, que corresponde al SPI.
        z = stats.norm.ppf(h)

        valores_spi[indices_mes] = z

    df[f"spi_{escala}"] = valores_spi
    return df


def analizar_tendencias(df_mensual):
    print("\n=== ANALISIS DE TENDENCIAS: prueba de Mann-Kendall ===")

    # Agrupar anualmente para analizar tendencias de largo plazo.
    df_anual = df_mensual.groupby("año").agg(
        tavg=("tavg_mean", "mean"),
        tmax=("tmax_mean", "mean"),
        tmin=("tmin_mean", "mean"),
        prcp=("prcp_sum", "sum")
    ).reset_index()

    # Excluir el año actual si todavia esta incompleto.
    año_actual = datetime.now().year
    df_anual = df_anual[df_anual["año"] < año_actual]

    variables = {
        "tavg": "Temperatura media anual (C)",
        "tmax": "Temperatura maxima anual (C)",
        "tmin": "Temperatura minima anual (C)",
        "prcp": "Precipitacion total anual (mm)"
    }

    resultados = {}
    for variable, nombre in variables.items():
        prueba_mk = mk.original_test(df_anual[variable])
        pendiente, intercepto, r_value, p_value, std_err = stats.linregress(
            df_anual["año"], df_anual[variable]
        )

        resultados[variable] = {
            "tendencia": prueba_mk.trend,
            "p_value_mk": prueba_mk.p,
            "pendiente_mk": prueba_mk.slope,
            "pendiente_regresion": pendiente,
            "cambio_10_anios": pendiente * 10
        }

        print(f"\n* Variable: {nombre}")
        print(f"  - Tendencia detectada: {prueba_mk.trend} (p-value: {prueba_mk.p:.4f})")
        print(f"  - Pendiente Mann-Kendall: {prueba_mk.slope:.4f} unidades/año")
        print(f"  - Cambio estimado por regresion: {pendiente:.4f} unidades/año ({pendiente * 10:.3f} por decada)")

    return df_anual, resultados


def graficar_tendencias_temperatura(df_anual, resultados):
    plt.figure(figsize=(10, 6))

    plt.plot(df_anual["año"], df_anual["tavg"], marker="o", label="Temp. media", color="#e74c3c", linewidth=2)
    plt.plot(df_anual["año"], df_anual["tmax"], marker="s", label="Temp. maxima", color="#c0392b", alpha=0.5, linestyle="--")
    plt.plot(df_anual["año"], df_anual["tmin"], marker="^", label="Temp. minima", color="#e67e22", alpha=0.5, linestyle="--")

    pendiente = resultados["tavg"]["pendiente_regresion"]
    intercepto = stats.linregress(df_anual["año"], df_anual["tavg"])[1]
    linea_tendencia = pendiente * df_anual["año"] + intercepto
    plt.plot(df_anual["año"], linea_tendencia, color="black", linestyle=":", label=f"Tendencia ({pendiente * 10:.2f} C/decada)")

    plt.title("Tendencia de temperatura en Neiva (1990 - 2025)\nEvidencia de calentamiento local")
    plt.xlabel("Año")
    plt.ylabel("Temperatura (C)")
    plt.legend(frameon=True)
    plt.tight_layout()

    os.makedirs(PLOTS_DIR, exist_ok=True)
    ruta_grafica = os.path.join(PLOTS_DIR, "temperatura_tendencia.png")
    plt.savefig(ruta_grafica, dpi=300)
    plt.close()
    print(f"Grafica guardada: {ruta_grafica}")


def graficar_estacionalidad_precipitacion(df_mensual):
    plt.figure(figsize=(10, 6))

    sns.boxplot(x="mes", y="prcp_sum", data=df_mensual, palette="Blues")

    promedios_mensuales = df_mensual.groupby("mes")["prcp_sum"].mean().reset_index()
    plt.scatter(
        promedios_mensuales["mes"] - 1,
        promedios_mensuales["prcp_sum"],
        color="red",
        marker="D",
        s=40,
        zorder=3,
        label="Promedio historico"
    )

    plt.title("Distribucion mensual de precipitacion en Neiva\nIdentificacion del regimen lluvia/sequia")
    plt.xlabel("Mes del año")
    plt.ylabel("Precipitacion acumulada (mm/mes)")
    plt.xticks(ticks=range(12), labels=["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"])
    plt.legend()
    plt.tight_layout()

    os.makedirs(PLOTS_DIR, exist_ok=True)
    ruta_grafica = os.path.join(PLOTS_DIR, "precipitacion_estacionalidad.png")
    plt.savefig(ruta_grafica, dpi=300)
    plt.close()
    print(f"Grafica guardada: {ruta_grafica}")


def graficar_sequias_spi(df_spi):
    plt.figure(figsize=(12, 6))

    df_reciente = df_spi[df_spi["año"] >= 2010].copy()
    colores = ["#e74c3c" if x < 0 else "#3498db" for x in df_reciente["spi_3"]]

    plt.bar(df_reciente["fecha"], df_reciente["spi_3"], width=25, color=colores, edgecolor="none", alpha=0.85)

    plt.axhline(0, color="gray", linestyle="-", linewidth=0.8)
    plt.axhline(-1, color="#e67e22", linestyle="--", linewidth=1, label="Sequia moderada (SPI = -1.0)")
    plt.axhline(-1.5, color="#c0392b", linestyle="-.", linewidth=1, label="Sequia extrema (SPI = -1.5)")

    plt.title("Indice de Precipitacion Estandarizado a 3 meses (SPI-3) en Neiva (2010 - 2026)\nMonitoreo de sequias agricolas")
    plt.xlabel("Año")
    plt.ylabel("Valor SPI-3")
    plt.legend(loc="lower left", frameon=True)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()

    os.makedirs(PLOTS_DIR, exist_ok=True)
    ruta_grafica = os.path.join(PLOTS_DIR, "spi_sequias.png")
    plt.savefig(ruta_grafica, dpi=300)
    plt.close()
    print(f"Grafica guardada: {ruta_grafica}")


def generar_insights_agricolas(df_mensual, df_spi):
    print("\n=== INSIGHTS Y ANALISIS DE RIEGO PARA PORTAFOLIO ===")

    calendario_climatico = df_mensual.groupby("mes").agg(
        lluvia_prom=("prcp_sum", "mean"),
        temp_max_prom=("tmax_mean", "mean"),
        viento_prom=("wspd_mean", "mean")
    ).reset_index()

    print("\n1. Calendario historico climatologico de Neiva:")
    print(calendario_climatico.to_string(index=False, formatters={
        "lluvia_prom": "{:.1f} mm".format,
        "temp_max_prom": "{:.1f} C".format,
        "viento_prom": "{:.1f} km/h".format
    }))

    sequias_extremas = df_spi[df_spi["spi_3"] <= -1.5][["año", "mes", "spi_3", "prcp_sum"]].copy()
    print("\n2. Registro historico de sequias extremas o severas (SPI-3 <= -1.5) desde 1990:")
    print(sequias_extremas.sort_values("spi_3").head(10).to_string(index=False))

    ruta_csv_final = os.path.join(DATA_DIR, "neiva_clima_analisis_final.csv")
    df_spi.to_csv(ruta_csv_final, index=False)
    print(f"\nDataset enriquecido guardado para Power BI: {ruta_csv_final}")


def main():
    try:
        df_mensual = cargar_datos()
        df_spi = calcular_spi(df_mensual, escala=3)
        df_anual, resultados_tendencia = analizar_tendencias(df_mensual)
        graficar_tendencias_temperatura(df_anual, resultados_tendencia)
        graficar_estacionalidad_precipitacion(df_mensual)
        graficar_sequias_spi(df_spi)
        generar_insights_agricolas(df_mensual, df_spi)
    except Exception as error:
        print(f"Error durante el analisis: {error}")


if __name__ == "__main__":
    main()
