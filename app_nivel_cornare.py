```python
import requests
import pandas as pd
import numpy as np
import streamlit as st
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LAT_DEFECTO = 6.2766
LON_DEFECTO = -75.5901

API_BASE_URL = "https://marco.cornare.gov.co/api/v1/estaciones"

LLAVE_FECHA = "level_date"
LLAVE_VALOR = "level"
CANDIDATOS_LAT = ["lat", "latitude", "latitud"]
CANDIDATOS_LON = ["lng", "lon", "longitude", "longitud"]

st.set_page_config(
    page_title="Nivel de estación — CORNARE",
    page_icon="🌊",
    layout="wide"
)

def obtener_serie_nivel(codigo_estacion, desde, hasta, calidad=1, timeout=30):
    url = f"{API_BASE_URL}/{codigo_estacion}/nivel"
    params = {"desde": desde, "hasta": hasta, "calidad": calidad}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }

    try:
        resp = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=timeout,
            verify=False
        )

        if resp.status_code == 200:
            return resp.json(), None

        return None, f"HTTP {resp.status_code}"

    except requests.exceptions.RequestException as e:
        return None, f"Error de red: {e}"


def obtener_todas_las_paginas(datos_json, timeout=30):
    registros = list(datos_json.get("values", []))
    siguiente_url = datos_json.get("next")

    while siguiente_url:
        try:
            resp = requests.get(
                siguiente_url,
                timeout=timeout,
                verify=False
            )
        except requests.exceptions.RequestException:
            break

        if resp.status_code != 200:
            break

        pagina = resp.json()
        registros.extend(pagina.get("values", []))
        siguiente_url = pagina.get("next")

    return registros


def detectar_coordenadas(datos_json):
    if not isinstance(datos_json, dict):
        return LAT_DEFECTO, LON_DEFECTO, False

    lat = next(
        (datos_json[k] for k in CANDIDATOS_LAT if k in datos_json),
        None
    )

    lon = next(
        (datos_json[k] for k in CANDIDATOS_LON if k in datos_json),
        None
    )

    if lat is not None and lon is not None:
        try:
            return float(lat), float(lon), True
        except (TypeError, ValueError):
            pass

    return LAT_DEFECTO, LON_DEFECTO, False


def calcular_indice_calidad(df):
    if df.empty or len(df) < 2:
        return 0.0, 0, 0

    df_idx = df.set_index("fecha")

    frecuencia_tipica = df["fecha"].diff().dropna().mode()

    if len(frecuencia_tipica) == 0:
        return 0.0, 0, 0

    frecuencia_tipica = frecuencia_tipica[0]

    rango_completo = pd.date_range(
        start=df_idx.index.min(),
        end=df_idx.index.max(),
        freq=frecuencia_tipica
    )

    esperados = len(rango_completo)
    huecos = esperados - len(df_idx)

    completitud = (
        max(0.0, 1 - (huecos / esperados))
        if esperados > 0 else 0.0
    )

    q1 = df["nivel"].quantile(0.25)
    q3 = df["nivel"].quantile(0.75)
    iqr = q3 - q1

    lim_inf = q1 - 1.5 * iqr
    lim_sup = q3 + 1.5 * iqr

    es_outlier = (
        (df["nivel"] < lim_inf) |
        (df["nivel"] > lim_sup) |
        (df["nivel"] < 0)
    )

    proporcion_outliers = es_outlier.mean()

    indice = (
        completitud * 0.7 +
        (1 - proporcion_outliers) * 0.3
    ) * 100

    return round(indice, 1), int(huecos), int(es_outlier.sum())


def calcular_metricas_avanzadas(df):
    serie = df["nivel"]

    actual = serie.iloc[-1]
    anterior = serie.iloc[-2] if len(serie) > 1 else actual

    minimo = serie.min()
    maximo = serie.max()
    promedio = serie.mean()
    mediana = serie.median()
    desviacion = serie.std() if len(serie) > 1 else 0
    rango = maximo - minimo

    variacion_absoluta = actual - anterior

    if anterior != 0:
        variacion_porcentual = ((actual - anterior) / abs(anterior)) * 100
    else:
        variacion_porcentual = 0

    if len(serie) >= 3:
        x = np.arange(len(serie))
        pendiente = np.polyfit(x, serie.values, 1)[0]
    else:
        pendiente = 0

    cambios = serie.diff().dropna()

    subidas = int((cambios > 0).sum())
    bajadas = int((cambios < 0).sum())
    estables = int((cambios == 0).sum())

    mayor_subida = cambios.max() if not cambios.empty else 0
    mayor_bajada = cambios.min() if not cambios.empty else 0

    percentil_actual = (
        (serie <= actual).sum() / len(serie)
    ) * 100

    coef_variacion = (
        (desviacion / promedio) * 100
        if promedio != 0 else 0
    )

    if pendiente > 0.01:
        tendencia = "Ascendente"
        tendencia_icono = "📈"
    elif pendiente < -0.01:
        tendencia = "Descendente"
        tendencia_icono = "📉"
    else:
        tendencia = "Estable"
        tendencia_icono = "➡️"

    if coef_variacion < 10:
        estabilidad = "Muy estable"
        estabilidad_score = 95
    elif coef_variacion < 20:
        estabilidad = "Estable"
        estabilidad_score = 80
    elif coef_variacion < 35:
        estabilidad = "Variable"
        estabilidad_score = 60
    else:
        estabilidad = "Muy variable"
        estabilidad_score = 35

    if actual > promedio * 1.5:
        riesgo = "Nivel elevado"
        riesgo_icono = "🔴"
    elif actual > promedio * 1.2:
        riesgo = "Vigilancia"
        riesgo_icono = "🟠"
    elif actual < promedio * 0.5:
        riesgo = "Nivel bajo"
        riesgo_icono = "🔵"
    else:
        riesgo = "Normal"
        riesgo_icono = "🟢"

    return {
        "actual": actual,
        "anterior": anterior,
        "minimo": minimo,
        "maximo": maximo,
        "promedio": promedio,
        "mediana": mediana,
        "desviacion": desviacion,
        "rango": rango,
        "variacion_absoluta": variacion_absoluta,
        "variacion_porcentual": variacion_porcentual,
        "pendiente": pendiente,
        "subidas": subidas,
        "bajadas": bajadas,
        "estables": estables,
        "mayor_subida": mayor_subida,
        "mayor_bajada": mayor_bajada,
        "percentil_actual": percentil_actual,
        "coef_variacion": coef_variacion,
        "tendencia": tendencia,
        "tendencia_icono": tendencia_icono,
        "estabilidad": estabilidad,
        "estabilidad_score": estabilidad_score,
        "riesgo": riesgo,
        "riesgo_icono": riesgo_icono
    }


st.sidebar.header("Parámetros de tu consulta")

nombre_estudiante = st.sidebar.text_input(
    "Nombre del estudiante",
    "Tu Nombre Aquí"
)

codigo_estacion = st.sidebar.text_input(
    "Código de estación",
    "42"
)

fecha_desde = st.sidebar.date_input(
    "Desde",
    pd.to_datetime("2026-08-23")
).strftime("%Y-%m-%d")

fecha_hasta = st.sidebar.date_input(
    "Hasta",
    pd.to_datetime("2026-08-30")
).strftime("%Y-%m-%d")

calidad = st.sidebar.selectbox(
    "Calidad",
    [1, 0],
    index=0,
    help="1 = solo datos validados"
)

consultar = st.sidebar.button(
    "🔍 Consultar",
    type="primary"
)

st.title("🌊 Nivel de ríos y quebradas — CORNARE")
st.caption(
    f"Estudiante: **{nombre_estudiante}** · Estación: **{codigo_estacion}**"
)

if consultar:

    with st.spinner("Consultando la API..."):
        datos_crudos, error = obtener_serie_nivel(
            codigo_estacion,
            fecha_desde,
            fecha_hasta,
            calidad
        )

    if error:
        st.error(f"❌ {error}")

    else:
        registros = obtener_todas_las_paginas(datos_crudos)

        if not registros:
            st.warning(
                "No hay registros para esta estación y rango de fechas. "
                "Prueba otro código u otro rango."
            )

        else:
            df = pd.DataFrame(registros)

            df = df.rename(
                columns={
                    LLAVE_FECHA: "fecha",
                    LLAVE_VALOR: "nivel"
                }
            )

            df["fecha"] = pd.to_datetime(
                df["fecha"],
                errors="coerce"
            )

            df["nivel"] = pd.to_numeric(
                df["nivel"],
                errors="coerce"
            )

            df = (
                df
                .dropna(subset=["fecha", "nivel"])
                .sort_values("fecha")
                .reset_index(drop=True)
            )

            lat, lon, coords_reales = detectar_coordenadas(
                datos_crudos
            )

            indice_calidad, huecos, n_outliers = calcular_indice_calidad(
                df
            )

            metricas = calcular_metricas_avanzadas(df)

            df["promedio_movil"] = (
                df["nivel"]
                .rolling(
                    window=min(10, len(df)),
                    min_periods=1
                )
                .mean()
            )

            df["variacion"] = df["nivel"].diff()

            st.markdown(
                f"""
                <div style="
                    padding:18px;
                    border-radius:16px;
                    background:linear-gradient(135deg,#0f172a,#164e63);
                    color:white;
                    margin-bottom:20px;
                ">
                    <h2 style="margin:0;">🌊 Centro de monitoreo hídrico</h2>
                    <p style="margin:6px 0 0 0;">
                        Estación <b>{codigo_estacion}</b> ·
                        {fecha_desde} → {fecha_hasta} ·
                        {len(df):,} lecturas analizadas
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "🌊 Nivel actual",
                f"{metricas['actual']:.2f}",
                f"{metricas['variacion_absoluta']:+.2f}"
            )

            col2.metric(
                "📊 Nivel promedio",
                f"{metricas['promedio']:.2f}",
                f"{metricas['actual'] - metricas['promedio']:+.2f}"
            )

            col3.metric(
                "📈 Tendencia",
                f"{metricas['tendencia_icono']} {metricas['tendencia']}",
                f"{metricas['pendiente']:+.4f}"
            )

            col4.metric(
                "🧭 Estado",
                f"{metricas['riesgo_icono']} {metricas['riesgo']}",
                f"{metricas['variacion_porcentual']:+.1f}%"
            )

            st.divider()

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "🔼 Nivel máximo",
                f"{metricas['maximo']:.2f}"
            )

            col2.metric(
                "🔽 Nivel mínimo",
                f"{metricas['minimo']:.2f}"
            )

            col3.metric(
                "↔️ Rango",
                f"{metricas['rango']:.2f}"
            )

            col4.metric(
                "📐 Mediana",
                f"{metricas['mediana']:.2f}"
            )

            st.subheader("📡 Comportamiento del nivel")

            grafico = df.set_index("fecha")[
                ["nivel", "promedio_movil"]
            ]

            st.line_chart(
                grafico,
                use_container_width=True,
                height=420
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "⚡ Mayor aumento",
                f"{metricas['mayor_subida']:.2f}"
            )

            col2.metric(
                "⚡ Mayor descenso",
                f"{metricas['mayor_bajada']:.2f}"
            )

            col3.metric(
                "🎯 Percentil actual",
                f"{metricas['percentil_actual']:.1f}%"
            )

            st.subheader("🧠 Lectura inteligente de la estación")

            estado_col1, estado_col2, estado_col3 = st.columns(3)

            with estado_col1:
                st.markdown(
                    f"""
                    <div style="
                        padding:20px;
                        border-radius:15px;
                        background:#f1f5f9;
                        text-align:center;
                    ">
                        <div style="font-size:38px;">
                            {metricas['tendencia_icono']}
                        </div>
                        <h3>{metricas['tendencia']}</h3>
                        <p>
                            El comportamiento general de la serie
                            presenta una tendencia
                            <b>{metricas['tendencia'].lower()}</b>.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with estado_col2:
                st.markdown(
                    f"""
                    <div style="
                        padding:20px;
                        border-radius:15px;
                        background:#f1f5f9;
                        text-align:center;
                    ">
                        <div style="font-size:38px;">
                            🧘
                        </div>
                        <h3>{metricas['estabilidad']}</h3>
                        <p>
                            Variabilidad relativa:
                            <b>{metricas['coef_variacion']:.1f}%</b>
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with estado_col3:
                st.markdown(
                    f"""
                    <div style="
                        padding:20px;
                        border-radius:15px;
                        background:#f1f5f9;
                        text-align:center;
                    ">
                        <div style="font-size:38px;">
                            {metricas['riesgo_icono']}
                        </div>
                        <h3>{metricas['riesgo']}</h3>
                        <p>
                            Nivel actual:
                            <b>{metricas['actual']:.2f}</b>
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.subheader("📊 Distribución de cambios")

            cambios_df = pd.DataFrame({
                "Movimiento": [
                    "Subidas",
                    "Bajadas",
                    "Estables"
                ],
                "Cantidad": [
                    metricas["subidas"],
                    metricas["bajadas"],
                    metricas["estables"]
                ]
            })

            st.bar_chart(
                cambios_df.set_index("Movimiento"),
                use_container_width=True
            )

            st.subheader("🎯 Indicadores de calidad")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Lecturas",
                f"{len(df):,}"
            )

            col2.metric(
                "Calidad",
                f"{indice_calidad}/100"
            )

            col3.metric(
                "Huecos",
                f"{huecos}"
            )

            col4.metric(
                "Outliers",
                f"{n_outliers}"
            )

            calidad_barra = max(
                0,
                min(100, indice_calidad)
            )

            st.progress(
                calidad_barra / 100,
                text=f"Calidad de datos: {calidad_barra:.1f}%"
            )

            st.subheader("📍 Ubicación de la estación")

            if not coords_reales:
                st.caption(
                    "La API no trajo latitud/longitud de la estación. "
                    "Se muestra el punto de partida definido en la aplicación."
                )

            st.map(
                pd.DataFrame({
                    "lat": [lat],
                    "lon": [lon]
                }),
                zoom=10
            )

            with st.expander("🔎 Detalle avanzado del índice de calidad"):

                st.write(
                    f"Completitud estimada: "
                    f"**{max(0, indice_calidad):.1f}%**"
                )

                st.write(
                    f"Huecos de reporte detectados: "
                    f"**{huecos}**"
                )

                st.write(
                    f"Outliers detectados: "
                    f"**{n_outliers}** de **{len(df)}** lecturas"
                )

                st.write(
                    "El índice combina completitud de la serie "
                    "(70%) y proporción de datos sin outliers (30%)."
                )

            with st.expander("📈 Estadísticas avanzadas"):

                estadisticas = pd.DataFrame({
                    "Métrica": [
                        "Nivel actual",
                        "Promedio",
                        "Mediana",
                        "Máximo",
                        "Mínimo",
                        "Rango",
                        "Desviación estándar",
                        "Coeficiente de variación",
                        "Variación última lectura",
                        "Variación porcentual",
                        "Subidas",
                        "Bajadas",
                        "Estables"
                    ],
                    "Valor": [
                        f"{metricas['actual']:.4f}",
                        f"{metricas['promedio']:.4f}",
                        f"{metricas['mediana']:.4f}",
                        f"{metricas['maximo']:.4f}",
                        f"{metricas['minimo']:.4f}",
                        f"{metricas['rango']:.4f}",
                        f"{metricas['desviacion']:.4f}",
                        f"{metricas['coef_variacion']:.2f}%",
                        f"{metricas['variacion_absoluta']:+.4f}",
                        f"{metricas['variacion_porcentual']:+.2f}%",
                        metricas["subidas"],
                        metricas["bajadas"],
                        metricas["estables"]
                    ]
                })

                st.dataframe(
                    estadisticas,
                    use_container_width=True,
                    hide_index=True
                )

            with st.expander("🗃️ Ver datos crudos"):

                tabla = df.copy()

                tabla["fecha"] = tabla["fecha"].dt.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                st.dataframe(
                    tabla,
                    use_container_width=True,
                    hide_index=True
                )

            csv = df.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                "⬇️ Descargar CSV",
                csv,
                file_name=f"nivel_estacion_{codigo_estacion}.csv",
                mime="text/csv"
            )

else:
    st.info(
        "Ajusta los parámetros en el sidebar y presiona **Consultar**."
    )
```
