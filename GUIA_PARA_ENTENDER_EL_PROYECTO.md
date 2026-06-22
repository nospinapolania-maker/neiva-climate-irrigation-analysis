# Guia para entender el proyecto

Este documento explica el proyecto en lenguaje sencillo, pensando en una persona que esta aprendiendo Python, analisis de datos y organizacion de proyectos.

El objetivo no es explicar cada linea de codigo todavia. El objetivo es que entiendas para que sirve cada archivo y en que orden se usa.

---

## 1. De que trata este proyecto

Este proyecto analiza datos climaticos de Neiva, Colombia.

La idea principal es responder una pregunta practica:

> Como se puede usar la informacion historica del clima para entender mejor los periodos secos y apoyar decisiones de riego agricola?

Para eso, el proyecto trabaja con datos como:

- temperatura promedio
- temperatura minima
- temperatura maxima
- lluvia
- viento
- presion atmosferica

Con esos datos, el proyecto crea archivos limpios, genera graficas y calcula un indicador llamado SPI-3, que ayuda a identificar periodos secos o posibles sequias.

---

## 2. Como leer este proyecto sin perderse

El proyecto se entiende mejor si lo lees en este orden:

1. `README.md`
2. `requirements.txt`
3. `data_extraction.py`
4. `data_analysis.py`
5. carpeta `data/`
6. carpeta `plots/`

Primero lees la explicacion general. Luego miras que necesita instalar el proyecto. Despues revisas el archivo que descarga y limpia datos. Finalmente revisas el archivo que analiza esos datos y genera resultados.

---

## 3. Que hace cada archivo principal

## README.md

El archivo `README.md` es la presentacion del proyecto.

Es lo primero que normalmente ve una persona cuando entra al repositorio en GitHub.

Sirve para explicar:

- de que trata el proyecto
- por que el proyecto es importante
- que problema intenta resolver
- que datos se usaron
- que archivos contiene el repositorio
- como ejecutar el proyecto
- que resultados principales se encontraron

En palabras sencillas:

> El README es la portada y la explicacion general del proyecto.

No es el codigo. Es el documento que ayuda a otra persona a entender rapidamente que hiciste.

---

## requirements.txt

El archivo `requirements.txt` contiene la lista de librerias que el proyecto necesita para funcionar.

Una libreria es codigo ya hecho por otras personas que usamos para no empezar desde cero.

En este proyecto aparecen librerias como:

- `pandas`: sirve para trabajar con tablas de datos.
- `numpy`: sirve para calculos numericos.
- `matplotlib`: sirve para hacer graficas.
- `seaborn`: sirve para hacer graficas mas faciles de leer.
- `meteostat`: sirve para descargar datos climaticos.
- `pymannkendall`: sirve para hacer una prueba estadistica de tendencia.
- `scipy`: sirve para calculos estadisticos.

En palabras sencillas:

> requirements.txt es la lista de herramientas que Python debe instalar antes de ejecutar el proyecto.

Se instala con este comando:

```bash
pip install -r requirements.txt
```

---

## data_extraction.py

El archivo `data_extraction.py` es el primer script que se debe ejecutar.

Su trabajo principal es conseguir los datos y prepararlos.

Hace estas tareas:

1. Se conecta a Meteostat, una fuente de datos climaticos.
2. Busca datos de la estacion meteorologica del Aeropuerto Benito Salas de Neiva.
3. Descarga datos diarios desde 1990 hasta 2026.
4. Organiza las fechas.
5. Revisa valores faltantes.
6. Rellena algunos datos faltantes.
7. Guarda archivos CSV en la carpeta `data/`.

Los archivos que genera son:

- `data/neiva_clima_diario.csv`
- `data/neiva_clima_mensual.csv`

En palabras sencillas:

> data_extraction.py trae los datos, los limpia y los deja listos para analizarlos.

Este archivo es como la etapa de preparacion de ingredientes antes de cocinar.

---

## data_analysis.py

El archivo `data_analysis.py` es el segundo script que se debe ejecutar.

Este archivo ya no se enfoca en descargar datos. Se enfoca en analizar los datos que ya fueron limpiados.

Hace estas tareas:

1. Lee el archivo `data/neiva_clima_mensual.csv`.
2. Calcula la lluvia acumulada de los ultimos 3 meses.
3. Calcula el indicador SPI-3.
4. Analiza tendencias de temperatura y lluvia.
5. Genera graficas.
6. Guarda un archivo final para usarlo en Power BI.

Los resultados principales se guardan en:

- `data/neiva_clima_analisis_final.csv`
- `plots/temperatura_tendencia.png`
- `plots/precipitacion_estacionalidad.png`
- `plots/spi_sequias.png`

En palabras sencillas:

> data_analysis.py toma los datos ya limpios y los convierte en resultados, graficas y conclusiones.

Este archivo es la parte donde el proyecto empieza a responder preguntas.

---

## 4. Que son las carpetas data y plots

## Carpeta data/

La carpeta `data/` guarda los archivos de datos en formato CSV.

Un archivo CSV es una tabla. Se puede abrir con Excel, Power BI, Python o cualquier herramienta de analisis de datos.

En este proyecto, la carpeta `data/` contiene:

- datos diarios
- datos mensuales
- datos finales con indicadores de sequia

## Carpeta plots/

La carpeta `plots/` guarda las graficas que genera el proyecto.

Estas graficas ayudan a ver patrones que son mas dificiles de entender mirando solo numeros.

Por ejemplo:

- como cambia la temperatura con los anos
- en que meses llueve mas o menos
- cuando aparecen periodos secos segun el SPI-3

---

## 5. Como ejecutar el proyecto paso a paso en Windows

Esta seccion asume que ya tienes Python instalado en tu computador.

## Paso 1: Abrir la carpeta del proyecto

Abre la carpeta:

```text
C:\Users\hewlett packard\Documents\GitHub\neiva-climate-irrigation-analysis
```

Puedes abrirla en VS Code para trabajar mas comodo.

---

## Paso 2: Abrir la terminal

En VS Code:

1. Abre el proyecto.
2. Ve al menu superior.
3. Selecciona `Terminal`.
4. Selecciona `New Terminal` o `Nueva terminal`.

La terminal debe quedar ubicada dentro de la carpeta del proyecto.

---

## Paso 3: Crear un entorno virtual

El entorno virtual sirve para instalar las librerias del proyecto sin mezclar todo con otros proyectos de Python.

Ejecuta:

```bash
python -m venv venv
```

Esto crea una carpeta llamada `venv`.

---

## Paso 4: Activar el entorno virtual

En Windows PowerShell, ejecuta:

```bash
.\venv\Scripts\Activate.ps1
```

Si funciono, normalmente veras algo parecido a esto al inicio de la terminal:

```text
(venv)
```

Eso significa que el entorno virtual esta activo.

---

## Paso 5: Instalar las librerias necesarias

Con el entorno virtual activo, ejecuta:

```bash
pip install -r requirements.txt
```

Este comando lee el archivo `requirements.txt` e instala las herramientas que el proyecto necesita.

---

## Paso 6: Descargar y limpiar los datos

Ahora ejecuta el primer script:

```bash
python data_extraction.py
```

Este paso debe crear o actualizar archivos dentro de la carpeta `data/`.

Despues de ejecutarlo, revisa que existan estos archivos:

```text
data/neiva_clima_diario.csv
data/neiva_clima_mensual.csv
```

---

## Paso 7: Analizar los datos y generar graficas

Ahora ejecuta el segundo script:

```bash
python data_analysis.py
```

Este paso debe crear o actualizar:

```text
data/neiva_clima_analisis_final.csv
plots/temperatura_tendencia.png
plots/precipitacion_estacionalidad.png
plots/spi_sequias.png
```

---

## Paso 8: Revisar los resultados

Despues de ejecutar los dos scripts, revisa:

- la carpeta `data/` para ver los archivos CSV
- la carpeta `plots/` para ver las graficas
- la terminal para leer los mensajes que imprimio Python

No necesitas entender todo de una vez. Primero debes entender el flujo general:

```text
descargar datos
limpiar datos
crear datos mensuales
analizar datos
generar graficas
guardar resultados
```

---

## 6. Orden correcto de ejecucion

Siempre ejecuta primero:

```bash
python data_extraction.py
```

Y despues:

```bash
python data_analysis.py
```

No ejecutes primero `data_analysis.py`, porque ese archivo necesita que ya existan los datos mensuales creados por `data_extraction.py`.

---

## 7. Resumen corto

Este proyecto tiene dos partes principales:

```text
data_extraction.py  -> descarga y limpia datos
data_analysis.py    -> analiza datos y genera resultados
```

El archivo `README.md` explica el proyecto.

El archivo `requirements.txt` dice que librerias hay que instalar.

La carpeta `data/` guarda los datos.

La carpeta `plots/` guarda las graficas.

Si entiendes eso, ya tienes la base para empezar a estudiar el proyecto sin perderte.
